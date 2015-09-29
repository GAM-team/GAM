#!/usr/bin/env python
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

u"""GAM is a command line tool which allows Administrators to control their Google Apps domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see http://git.io/gam

"""

__author__ = u'Jay Lee <jay0lee@gmail.com>'
__version__ = u'3.60'
__license__ = u'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

import sys, os, time, datetime, random, socket, csv, platform, re, calendar, base64, string, codecs, StringIO, subprocess

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
GAM_SITE = u'https://github.com/jay0lee/GAM'
GAM_RELEASES = GAM_SITE+u'/releases'
GAM_WIKI = GAM_SITE+u'/wiki'
GAM_WIKI_CREATE_CLIENT_SECRETS = GAM_WIKI+u'/CreatingClientSecretsFile#creating-your-own-oauth2servicejson'
GAM_APPSPOT = u'https://gam-update.appspot.com'
GAM_APPSPOT_LATEST_VERSION = GAM_APPSPOT+u'/latest-version.txt?v='+__version__
GAM_APPSPOT_LATEST_VERSION_ANNOUNCEMENT = GAM_APPSPOT+u'/latest-version-announcement.txt?v='+__version__

TRUE = u'true'
FALSE = u'false'
TRUE_FALSE = [TRUE, FALSE]
TRUE_VALUES = [TRUE, u'on', u'yes', u'enabled', u'1']
FALSE_VALUES = [FALSE, u'off', u'no', u'disabled', u'0']
NEVER = u'Never'
ONE_KILO_BYTES = 1024
ONE_MEGA_BYTES = 1024*1024
ONE_GIGA_BYTES = 1024*1024*1024
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
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
# GAM entity types as specified on the command line
CL_ENTITY_COURSEPARTICIPANTS = u'courseparticipants'
CL_ENTITY_CROS = u'cros'
CL_ENTITY_GROUP = u'group'
CL_ENTITY_GROUPS = u'groups'
CL_ENTITY_LICENSES = u'licenses'
CL_ENTITY_OU = u'ou'
CL_ENTITY_OU_AND_CHILDREN = u'ou_and_children'
CL_ENTITY_QUERY = u'query'
CL_ENTITY_STUDENTS = u'students'
CL_ENTITY_TEACHERS = u'teachers'
CL_ENTITY_USER = u'user'
CL_ENTITY_USERS = u'users'
#
CL_CROS_ENTITIES = [
  CL_ENTITY_CROS,
  ]
CL_USER_ENTITIES = [
  CL_ENTITY_COURSEPARTICIPANTS,
  CL_ENTITY_GROUP,
  CL_ENTITY_GROUPS,
  CL_ENTITY_LICENSES,
  CL_ENTITY_OU,
  CL_ENTITY_OU_AND_CHILDREN,
  CL_ENTITY_QUERY,
  CL_ENTITY_STUDENTS,
  CL_ENTITY_TEACHERS,
  CL_ENTITY_USER,
  CL_ENTITY_USERS,
  ]
#
# Aliases for CL entity types
CL_ENTITY_ALIAS_MAP = {
  u'license': CL_ENTITY_LICENSES,
  u'licence': CL_ENTITY_LICENSES,
  u'licences': CL_ENTITY_LICENSES,
  u'org': CL_ENTITY_OU,
  u'org_and_child': CL_ENTITY_OU_AND_CHILDREN,
  u'ou_and_child': CL_ENTITY_OU_AND_CHILDREN,
  }
#
# CL entity source selectors
CL_ENTITY_SELECTOR_ALL = u'all'
CL_ENTITY_SELECTOR_FILE = u'file'
#
CL_ENTITY_SELECTORS = [
  CL_ENTITY_SELECTOR_ALL,
  CL_ENTITY_SELECTOR_FILE,
  ]
#
# Allowed values for CL source selector all
CL_CROS_ENTITY_SELECTOR_ALL_SUBTYPES = [
  CL_ENTITY_CROS,
  ]
CL_USER_ENTITY_SELECTOR_ALL_SUBTYPES = [
  CL_ENTITY_USERS,
  ]
#
CL_ENTITY_ALL_CROS = CL_ENTITY_SELECTOR_ALL+u' '+CL_ENTITY_CROS
CL_ENTITY_ALL_USERS = CL_ENTITY_SELECTOR_ALL+u' '+CL_ENTITY_USERS
#
CL_ENTITY_SELECTOR_ALL_SUBTYPES_MAP = {
  CL_ENTITY_CROS: CL_ENTITY_ALL_CROS,
  CL_ENTITY_USERS: CL_ENTITY_ALL_USERS,
  }
#
#
# Global variables
#
# Shared by batch_worker and run_batch
q = None
#
# Location of gam.cfg, if not set, gamPath will be used
EV_GAM_CFG_HOME = u'GAM_CFG_HOME'
# Name of config file
GAM_CFG = u'gam.cfg'
GAM_BAK = u'gam.bak'
# Path to gam, assigned in SetGlobalVariables after the command line is cleaned up for Windows
GC_GAM_PATH = u'gam_path'
# Where will CSV files be written
GC_CSVFILE = u'csvfile'
# File containing time of last GAM update check
GC_LAST_UPDATE_CHECK_TXT = u'lastupdatecheck'
LAST_UPDATE_CHECK_TXT = u'lastupdatecheck.txt'
#
# Global variables derived from values in gam.cfg
#
# Full path to cacert.pem
GC_CACERT_PEM = u'cacert_pem'
# Extra arguments to pass to GAPI functions
GC_EXTRA_ARGS = u'extra_args'
# Values retrieved from oauth2service.json
GC_OAUTH2SERVICE_KEY = u'aouth2service_key'
GC_OAUTH2SERVICE_ACCOUNT_EMAIL = u'aouth2service_account_email'
GC_OAUTH2SERVICE_ACCOUNT_CLIENT_ID = u'aouth2service_account_client_id'
#
# Global variables defined in  gam.cfg
#
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, don't automatically generate gam batch commands
GC_AUTO_BATCH_MIN = u'auto_batch_min'
# GAM cache directory. If no_cache is specified, this variable will be set to None
GC_CACHE_DIR = u'cache_dir'
# Character set of batch, csv, data files
GC_CHARSET = u'charset'
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

GC_DEFAULTS = {
  GC_AUTO_BATCH_MIN: 0,
  GC_CACHE_DIR: u'',
  GC_CHARSET: u'ascii',
  GC_CLIENT_SECRETS_JSON: FN_CLIENT_SECRETS_JSON,
  GC_CONFIG_DIR: u'',
  GC_CUSTOMER_ID: u'',
  GC_DEBUG_LEVEL: 0,
  GC_DOMAIN: u'',
  GC_DRIVE_DIR: u'',
  GC_NO_BROWSER: FALSE,
  GC_NO_CACHE: FALSE,
  GC_NO_UPDATE_CHECK: FALSE,
  GC_NO_VERIFY_SSL: FALSE,
  GC_NUM_THREADS: 5,
  GC_OAUTH2_TXT: FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: FN_OAUTH2SERVICE_JSON,
  GC_SECTION: u'',
  GC_SHOW_GETTINGS: TRUE,
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
  GC_CHARSET: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_CLIENT_SECRETS_JSON: {GC_VAR_TYPE_KEY: GC_TYPE_FILE},
  GC_CONFIG_DIR: {GC_VAR_TYPE_KEY: GC_TYPE_DIRECTORY},
  GC_CUSTOMER_ID: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_DEBUG_LEVEL: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (0, None)},
  GC_DOMAIN: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_DRIVE_DIR: {GC_VAR_TYPE_KEY: GC_TYPE_DIRECTORY},
  GC_NO_BROWSER: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NO_CACHE: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NO_VERIFY_SSL: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  GC_NUM_THREADS: {GC_VAR_TYPE_KEY: GC_TYPE_INTEGER, GC_VAR_LIMITS_KEY: (1, None)},
  GC_OAUTH2_TXT: {GC_VAR_TYPE_KEY: GC_TYPE_FILE},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE_KEY: GC_TYPE_FILE},
  GC_SECTION: {GC_VAR_TYPE_KEY: GC_TYPE_STRING},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE_KEY: GC_TYPE_BOOLEAN},
  }

GC_VAR_ALIASES = {
  u'autobatchmin':  u'auto_batch_min',
  u'cachedir':  u'cache_dir',
  u'charset':  u'charset',
  u'clientsecretsjson':  u'client_secrets_json',
  u'configdir':  u'config_dir',
  u'customerid':  u'customer_id',
  u'debuglevel':  u'debug_level',
  u'domain':  u'domain',
  u'drivedir':  u'drive_dir',
  u'nobrowser':  u'no_browser',
  u'nocache':  u'no_cache',
  u'noupdatecheck':  u'no_update_check',
  u'noverifyssl':  u'no_verify_ssl',
  u'numthreads':  u'num_threads',
  u'oauth2txt':  u'oauth2_txt',
  u'oauth2servicejson':  u'oauth2service_json',
  u'section':  u'section',
  u'showgettings':  u'show_gettings',
  }

# Command line batch/csv keywords
GAM_CMD = u'gam'
COMMIT_BATCH_CMD = u'commit-batch'
LOOP_CMD = u'loop'
MATCHFIELD_CMD = u'matchfield'
#
CHARSET_ARGUMENT_PRESENT = {u'charset': True,  }
MATCHFIELD_ARGUMENT_PRESENT = {MATCHFIELD_CMD: True, }
GAM_ARGUMENT_PRESENT = {GAM_CMD: True, }
LOOP_ARGUMENT_PRESENT = {LOOP_CMD: True, }
#
CHARSET_ARGUMENT_PRESENT = {u'charset': True,  }
CLEAR_ARGUMENT_PRESENT = {u'clear': True, }
CLIENTID_ARGUMENT_PRESENT = {u'clientid': True, }
DATAFIELD_ARGUMENT_PRESENT = {u'datafield': True,  }
DATA_ARGUMENT_PRESENT = {u'data': True,  }
DELIMITER_ARGUMENT_PRESENT = {u'delimiter': True,  }
FILE_ARGUMENT_PRESENT = {u'file': True, }
FROM_ARGUMENT_PRESENT = {u'from': True, }
IDS_ARGUMENT_PRESENT = {u'ids': True, }
ID_ARGUMENT_PRESENT = {u'id': True, }
KEYFIELD_ARGUMENT_PRESENT = {u'keyfield': True,  }
LOGO_ARGUMENT_PRESENT = {u'logo': True, }
MATCHFIELD_ARGUMENT_PRESENT = {u'matchfield': True, }
MODE_ARGUMENT_PRESENT = {u'mode' : True, }
MOVE_ADD_ARGUMENT_PRESENT = {u'move': True, u'add': True, }
MULTIVALUE_ARGUMENT_PRESENT = {u'multivalued': True, u'multivalue': True, u'value': True, }
NOINFO_ARGUMENT_PRESENT = {u'noinfo': True, }
NORMALIZE_ARGUMENT_PRESENT = {u'normalize': True, }
NOUSERS_ARGUMENT_PRESENT = {u'nousers': True, }
ORG_OU_ARGUMENT_PRESENT = {u'org': True, u'ou': True, }
PRIMARY_ARGUMENT_PRESENT = {u'primary': True, }
QUERY_ARGUMENT_PRESENT = {u'query': True, }
SHOWTITLES_ARGUMENT_PRESENT = {u'showtitles': True, }
TODRIVE_ARGUMENT_PRESENT = {u'todrive': True,  }
TO_ARGUMENT_PRESENT = {u'to': True, }
UNSTRUCTURED_FORMATTED_ARGUMENT_PRESENT = {u'unstructured': True, u'formatted': True, }
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
REDIRECT_ARGUMENT_PRESENT = {REDIRECT_CMD: True, }
SELECT_ARGUMENT_PRESENT = {SELECT_CMD: True, }
SELECT_SAVE_ARGUMENT_PRESENT = {SELECT_SAVE_CMD: True, }
SELECT_VERIFY_ARGUMENT_PRESENT = {SELECT_VERIFY_CMD: True, }
CONFIG_ARGUMENT_PRESENT = {CONFIG_CMD: True, }
CONFIG_CREATE_OVERWRITE_ARGUMENT_PRESENT = {CONFIG_CREATE_OVERWRITE_CMD: True}
GAM_ARGUMENT_PRESENT = {GAM_CMD: True, }
LOOP_ARGUMENT_PRESENT = {LOOP_CMD: True, }
#
# Google API constants
NEVER_TIME = u'1970-01-01T00:00:00.000Z'
NEVER_START_DATE = u'1970-01-01'
NEVER_END_DATE = u'1969-12-31'
ROLE_MANAGER = u'MANAGER'
ROLE_MEMBER = u'MEMBER'
ROLE_OWNER = u'OWNER'
ROLE_USER = u'USER'
ROLE_MANAGER_MEMBER = ','.join([ROLE_MANAGER, ROLE_MEMBER])
ROLE_MANAGER_OWNER = ','.join([ROLE_MANAGER, ROLE_OWNER])
ROLE_MANAGER_MEMBER_OWNER = ','.join([ROLE_MANAGER, ROLE_MEMBER, ROLE_OWNER])
ROLE_MEMBER_OWNER = ','.join([ROLE_MEMBER, ROLE_OWNER])
SORTORDER_CHOICES_MAP = {u'ascending': u'ASCENDING', u'descending': u'DESCENDING'}

# Valid language codes
LANGUAGE_CODES_MAP = {
  u'af': u'af', #Afrikaans
  u'am': u'am', #Amharic
  u'ar': u'ar', #Arabica
  u'az': u'az', #Azerbaijani
  u'bg': u'bg', #Bulgarian
  u'bn': u'bn', #Bengali
  u'ca': u'ca', #Catalan
  u'chr': u'chr', #Cherokee
  u'cs': u'cs', #Czech
  u'cy': u'cy', #Welsh
  u'da': u'da', #Danish
  u'de': u'de', #German
  u'el': u'el', #Greek
  u'en': u'en', #English
  u'en-gb': u'en-GB', #English (UK)
  u'en-us': u'en-US', #English (US)
  u'es': u'es', #Spanish
  u'es-419': u'es-419', #Spanish (Latin America)
  u'et': u'et', #Estonian
  u'eu': u'eu', #Basque
  u'fa': u'fa', #Persian
  u'fi': u'fi', #Finnish
  u'fr': u'fr', #French
  u'fr-ca': u'fr-ca', #French (Canada)
  u'ag': u'ga', #Irish
  u'gl': u'gl', #Galician
  u'gu': u'gu', #Gujarati
  u'he': u'he', #Hebrew
  u'hi': u'hi', #Hindi
  u'hr': u'hr', #Croatian
  u'hu': u'hu', #Hungarian
  u'hy': u'hy', #Armenian
  u'id': u'id', #Indonesian
  u'in': u'in',
  u'is': u'is', #Icelandic
  u'it': u'it', #Italian
  u'iw': u'he', #Hebrew
  u'ja': u'ja', #Japanese
  u'ka': u'ka', #Georgian
  u'km': u'km', #Khmer
  u'kn': u'kn', #Kannada
  u'ko': u'ko', #Korean
  u'lo': u'lo', #Lao
  u'lt': u'lt', #Lithuanian
  u'lv': u'lv', #Latvian
  u'ml': u'ml', #Malayalam
  u'mn': u'mn', #Mongolian
  u'mr': u'mr', #Marathi
  u'ms': u'ms', #Malay
  u'my': u'my', #Burmese
  u'ne': u'ne', #Nepali
  u'nl': u'nl', #Dutch
  u'no': u'no', #Norwegian
  u'or': u'or', #Oriya
  u'pl': u'pl', #Polish
  u'pt-br': u'pt-BR', #Portuguese (Brazil)
  u'pt-pt': u'pt-PT', #Portuguese (Portugal)
  u'ro': u'ro', #Romanian
  u'ru': u'ru', #Russian
  u'si': u'si', #Sinhala
  u'sk': u'sk', #Slovak
  u'sl': u'sl', #Slovenian
  u'sr': u'sr', #Serbian
  u'sv': u'sv', #Swedish
  u'sw': u'sw', #Swahili
  u'ta': u'ta', #Tamil
  u'te': u'te', #Telugu
  u'th': u'th', #Thai
  u'tl': u'tl', #Tagalog
  u'tr': u'tr', #Turkish
  u'uk': u'uk', #Ukrainian
  u'ur': u'ur', #Urdu
  u'vi': u'vi', #Vietnamese
  u'zh-cn': u'zh-CN', #Chinese (Simplified)
  u'zh-hk': u'zh-HK', #Chinese (Hong Kong/Traditional)
  u'zh-tw': u'zh-TW', #Chinese (Taiwan/Traditional)
  u'zu': u'zu', #Zulu
  }
#
# Object BNF names
OBJECT_ACCESS_TOKEN = u'AccessToken'
OBJECT_ARGUMENT = u'argument'
OBJECT_ASP_ID = u'AspID'
OBJECT_CHAR_SET = u'CharacterSet'
OBJECT_CIDR_NETMASK = u'CIDRnetmask'
OBJECT_CLIENT_ID = u'ClientID'
OBJECT_COURSE_ALIAS = u'CourseAlias'
OBJECT_COURSE_ALIAS_LIST = u'CourseAliasList'
OBJECT_COURSE_ENTITY = u'CourseEntity'
OBJECT_COURSE_ID = u'CourseID'
OBJECT_CROS_DEVICE_ENTITY = u'CrOSDeviceEntity'
OBJECT_CROS_ENTITY = u'CrOSEntity'
OBJECT_DOMAIN_NAME = u'DomainName'
OBJECT_DRIVE_FILE_ENTITY = u'DriveFileEntity'
OBJECT_DRIVE_FILE_ID = u'DriveFileID'
OBJECT_DRIVE_FILE_NAME = u'DriveFileName'
OBJECT_DRIVE_FOLDER_ID = u'DriveFolderID'
OBJECT_DRIVE_FOLDER_NAME = u'DriveFolderName'
OBJECT_EMAIL_ADDRESS = u'EmailAddress'
OBJECT_EMAIL_ADDRESS_ENTITY = u'EmailAddressEntity'
OBJECT_EMAIL_ADDRESS_OR_UID = u'EmailAaddress|UniqueID'
OBJECT_ENTITY = u'Entity'
OBJECT_ENTITY_TYPE = u'EntityType'
OBJECT_FIELD_NAME = u'FieldName'
OBJECT_FILE_NAME = u'FileName'
OBJECT_FILE_NAME_OR_URL = u'FileName|URL'
OBJECT_FILE_PATH = u'FilePath'
OBJECT_FORMAT_LIST = u'FormatList'
OBJECT_GAM_ARGUMENT_LIST = u'GAM argument list'
OBJECT_GROUP_ENTITY = u'GroupEntity'
OBJECT_GROUP_ITEM = u'GroupItem'
OBJECT_HOST_NAME = u'HostName'
OBJECT_JOB_ID = u'JobID'
OBJECT_JOB_OR_PRINTER_ID = u'JobID|PrinterID'
OBJECT_LABEL_NAME = u'LabelName'
OBJECT_LABEL_REPLACEMENT = u'LabelReplacement'
OBJECT_MOBILE_DEVICE_ENTITY = u'MobileDeviceEntity'
OBJECT_MOBILE_ENTITY = u'MobileEntity'
OBJECT_NAME = u'Name'
OBJECT_NOTIFICATION_ID = u'NotificationID'
OBJECT_ORGUNIT_PATH = u'OrgUnitPath'
OBJECT_ORGUNIT_ENTITY = u'OrgUnitEntity'
OBJECT_PERMISSION_ID = u'PermissionID'
OBJECT_PHOTO_FILENAME_PATTERN = u'FilenameNamePattern'
OBJECT_PRINTER_ID = u'PrinterID'
OBJECT_PRINTER_ID_LIST = u'PrinterIDList'
OBJECT_PRINTJOB_AGE = u'PrintJobAge'
OBJECT_PRINTJOB_ID = u'PrintJobID'
OBJECT_PRODUCT_ID_LIST = u'ProductIDList'
OBJECT_PROPERTY_KEY = u'PropertyKey'
OBJECT_PROPERTY_VALUE = u'PropertyValue'
OBJECT_QUERY = u'Query'
OBJECT_RECURRENCE = u'RRULE EXRULE RDATE and EXDATE lines'
OBJECT_REQUEST_ID = u'RequestID'
OBJECT_RESOURCE_ENTITY = u'ResourceEntity'
OBJECT_RESOURCE_ID = u'ResourceID'
OBJECT_RE_PATTERN = u'PythonRegularExpression'
OBJECT_SCHEMA_ENTITY = u'SchemaEntity'
OBJECT_SCHEMA_NAME = u'SchemaName'
OBJECT_SCHEMA_NAME_LIST = u'SchemaNameList'
OBJECT_SECTION_NAME = u'SectionName'
OBJECT_SKU_ID = u'SKUID'
OBJECT_SKU_ID_LIST = u'SKUIDList'
OBJECT_STRING = u'String'
OBJECT_STUDENT_ID = u'StudentID'
OBJECT_TEACHER_ID = u'TeacherID'
OBJECT_URI = u'URI'
OBJECT_URL = u'URL'
OBJECT_USER_ENTITY = u'UserEntity'
OBJECT_USER_ITEM = u'UserItem'
#
MESSAGE_CLIENT_API_ACCESS_DENIED = u'Access Denied. Please make sure the Client Name:\n\n{0}\n\nis authorized for the API Scope(s):\n\n{1}\n\nThis can be configured in your Control Panel under:\n\nSecurity -->\nAdvanced Settings -->\nManage API client access'
MESSAGE_GAM_EXITING_FOR_UPDATE = u'GAM is now exiting so that you can overwrite this old version with the latest release'
MESSAGE_GAM_OUT_OF_MEMORY = u'GAM has run out of memory. If this is a large Google Apps instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS = u'Header "{0}" not found in CSV headers of "{1}".'
MESSAGE_HIT_CONTROL_C_TO_UPDATE = u'\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can turn off update checks with the command: "gam config select default set no_update_check true save"'
MESSAGE_NO_DISCOVERY_INFORMATION = u'No online discovery doc and {0} does not exist locally'
MESSAGE_NO_PYTHON_SSL = u'You don\'t have the Python SSL module installed so we can\'t verify SSL Certificates. You can fix this by installing the Python SSL module or you can live on the edge and turn SSL validation off with the command: "gam config select default set no_verify_ssl true save"'
MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE = u'Cowardly refusing to perform migration due to lack of target drive space.'
MESSAGE_REQUEST_COMPLETED_NO_FILES = u'Request completed but no files were returned, try requesting again'
MESSAGE_REQUEST_NOT_COMPLETE = u'Request needs to be completed before downloading, current status is: {0}'
MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = u'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON = u'Please follow the instructions at this site to setup a Service Account.'
NESSAGE_OAUTH2SERVICE_JSON_INVALID = u'The file {0} is missing required keys (client_email, client_id or private_key).'
#
def convertUTF8(data):
  import collections
  if isinstance(data, str):
    return data
  if isinstance(data, unicode):
    if os.name != u'nt':
      return data.encode('utf-8')
    return data
  if isinstance(data, collections.Mapping):
    return dict(map(convertUTF8, data.iteritems()))
  if isinstance(data, collections.Iterable):
    return type(data)(map(convertUTF8, data))
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
  doGAMVersion(checkForCheck=False)
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
#
# Error message types
# Keys into ARGUMENT_ERROR_NAMES; arbitrary values but must be unique
ARGUMENTS_MUTUALLY_EXCLUSIVE = u'muex'
ARGUMENT_EXTRANEOUS = u'extr'
ARGUMENT_INVALID = u'inva'
ARGUMENT_MISSING = u'miss'
#
# ARGUMENT_ERROR_NAMES[0] is plural,ARGUMENT_ERROR_NAMES[1] is singular
# These values can be translated into other languages
ARGUMENT_ERROR_NAMES = {
  ARGUMENTS_MUTUALLY_EXCLUSIVE: [u'Mutually exclusive arguments', u'Mutually exclusive arguments'],
  ARGUMENT_EXTRANEOUS: [u'Extra arguments', u'Extra argument'],
  ARGUMENT_INVALID: [u'Invalid arguments', u'Invalid argument'],
  ARGUMENT_MISSING: [u'Missing arguments', u'Missing argument'],
  }
#
# Concatenate list members, any item containing spaces is enclosed in ''
#
def makeQuotedList(items):
  qstr = u''
  for item in items:
    if item and (item.find(u' ') == -1) and (item.find(u',') == -1):
      qstr += item
    else:
      qstr += u"'"+item+u"'"
    qstr += u' '
  return qstr[:-1] if len(qstr) > 0 else u''

def systemErrorExit(sysRC, message):
  if message:
    sys.stderr.write(u'\n{0}{1}\n'.format(ERROR_PREFIX, message))
  sys.exit(sysRC)

def noPythonSSLExit():
  systemErrorExit(14, MESSAGE_NO_PYTHON_SSL)

def usageErrorExit(i, message):
  if i < len(sys.argv):
    sys.stderr.write(convertUTF8(u'\nCommand: {0} >>>{1}<<< {2}\n'.format(makeQuotedList(sys.argv[:i]),
                                                                          makeQuotedList([sys.argv[i]]),
                                                                          makeQuotedList(sys.argv[i+1:]) if i < len(sys.argv) else u'')))
  else:
    sys.stderr.write(convertUTF8(u'\nCommand: {0} >>><<<\n'.format(makeQuotedList(sys.argv))))
  sys.stderr.write(u'\n{0}{1}\n'.format(ERROR_PREFIX, message))
  sys.stderr.write(u'\nHelp: Documentation is at {0}\n'.format(GAM_WIKI))
  sys.exit(2)

def entityServiceNotApplicableWarning(entityType, entityName):
  print u'{0}: {1}, Service not applicable'.format(entityType, entityName)

#
# Invalid CSV ~Header
#
def csvFieldErrorExit(i, fieldName, fieldNames):
  usageErrorExit(i, MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(fieldName, u','.join(fieldNames)))
#
# The last thing shown is unknown
#
def unknownArgumentExit(i):
  usageErrorExit(i, ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1])
#
# Argument describes what's expected
#
def expectedArgumentExit(i, problem, argument):
  usageErrorExit(i, u'{0}: expected <{1}>'.format(problem, argument))

def invalidArgumentExit(i, argument):
  expectedArgumentExit(i, ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1], argument)
#
# Argument describes what's missing
#
def missingArgumentExit(argument):
  expectedArgumentExit(len(sys.argv), ARGUMENT_ERROR_NAMES[ARGUMENT_MISSING][1], argument)
#
# Choices is the valid set of choices that was expected
#
def formatChoiceList(choices):
  if isinstance(choices, dict):
    choiceList = choices.keys()
  else:
    choiceList = choices
  if len(choiceList) <= 5:
    return '|'.join(choiceList)
  else:
    return '|'.join(sorted(choiceList))

def invalidChoiceExit(i, choices):
  expectedArgumentExit(i, ARGUMENT_ERROR_NAMES[ARGUMENT_INVALID][1], formatChoiceList(choices))

def missingChoiceExit(i, choices):
  expectedArgumentExit(i, ARGUMENT_ERROR_NAMES[ARGUMENT_MISSING][1], formatChoiceList(choices))

def printLine(message):
  sys.stdout.write(message+u'\n')
#
# Get an argument, downshift, delete underscores
#
def getArgument(i):
  if i < len(sys.argv):
    argument = sys.argv[i].lower()
    if argument:
      return argument.replace(u'_', u'')
  missingArgumentExit(OBJECT_ARGUMENT)

def getBoolean(i):
  if i < len(sys.argv):
    boolean = sys.argv[i].strip().lower()
    if boolean in TRUE_VALUES:
      return True
    if boolean in FALSE_VALUES:
      return False
    invalidChoiceExit(i, TRUE_FALSE)
  missingChoiceExit(i, TRUE_FALSE)

DEFAULT_CHOICE = u'defaultChoice'
CHOICE_ALIASES = u'choiceAliases'
MAP_CHOICE = u'mapChoice'

def getChoice(i, choices, **opts):
  if i < len(sys.argv):
    choice = sys.argv[i].strip().lower()
    if choice:
      if CHOICE_ALIASES in opts and choice in opts[CHOICE_ALIASES]:
        choice = opts[CHOICE_ALIASES][choice]
      if choice not in choices:
        choice = choice.replace(u'_', u'')
        if CHOICE_ALIASES in opts and choice in opts[CHOICE_ALIASES]:
          choice = opts[CHOICE_ALIASES][choice]
      if choice in choices:
        return choice if (MAP_CHOICE not in opts or not opts[MAP_CHOICE]) else choices[choice]
    if DEFAULT_CHOICE in opts:
      return opts[DEFAULT_CHOICE]
    invalidChoiceExit(i, choices)
  elif DEFAULT_CHOICE in opts:
    return opts[DEFAULT_CHOICE]
  missingChoiceExit(i, choices)

COLORHEX_PATTERN = re.compile(r'#[0-9a-fA-F]{6}')
COLORHEX_FORMAT_REQUIRED = u'#ffffff'

def getColorHexAttribute(i):
  if i < len(sys.argv):
    tg = COLORHEX_PATTERN.match(sys.argv[i].strip())
    if tg:
      return tg.group(0)
    invalidArgumentExit(i, COLORHEX_FORMAT_REQUIRED)
  missingArgumentExit(COLORHEX_FORMAT_REQUIRED)

def cleanCourseId(courseId):
  if courseId.startswith(u'd:'):
    return courseId[2:]
  return courseId

def normalizeCourseId(courseId):
  if not courseId.isdigit() and courseId[:2] != u'd:':
    return u'd:{0}'.format(courseId)
  return courseId

def getCourseId(i):
  if i < len(sys.argv):
    courseId = sys.argv[i]
    if courseId:
      return normalizeCourseId(courseId)
  missingArgumentExit(OBJECT_COURSE_ID)

def getCourseAlias(i):
  if i < len(sys.argv):
    courseAlias = sys.argv[i]
    if courseAlias:
      if courseAlias[:2] != u'd:':
        return u'd:{0}'.format(courseAlias)
      return courseAlias
  missingArgumentExit(OBJECT_COURSE_ALIAS)

#
# Normalize user/group email address/uid
# uid:12345abc -> 12345abc
# foo -> foo@domain
# foo@ -> foo@domain
# foo@bar.com -> foo@bar.com
# @domain -> @domain  (Not good, but what else to do?)
#
NO_UID = u'noUid'

def normalizeEmailAddressOrUID(emailAddressOrUID, **opts):
  uidOK = (NO_UID not in opts) or (not opts[NO_UID])
  if uidOK and (emailAddressOrUID.find(u':') != -1):
    if emailAddressOrUID[:4].lower() == u'uid:':
      return emailAddressOrUID[4:]
    if emailAddressOrUID[:3].lower() == u'id:':
      return emailAddressOrUID[3:]
  atLoc = emailAddressOrUID.find(u'@')
  if atLoc != 0:
    if (atLoc == -1) or (atLoc == len(emailAddressOrUID)-1) and GC_Values[GC_DOMAIN]:
      if atLoc == -1:
        emailAddressOrUID = u'{0}@{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
      else:
        emailAddressOrUID = u'{0}{1}'.format(emailAddressOrUID, GC_Values[GC_DOMAIN])
  return emailAddressOrUID.lower()

EMPTYOK = u'emptyOK'
OPTIONAL = u'optional'

def getEmailAddress(i, **opts):
  uidOK = (NO_UID not in opts) or (not opts[NO_UID])
  if i < len(sys.argv):
    emailAddress = sys.argv[i].strip().lower()
    if emailAddress:
      if uidOK and (emailAddress.find(u':') != -1):
        if emailAddress[:4] == u'uid:':
          return emailAddress[4:]
        if emailAddress[:3] == u'id:':
          return emailAddress[3:]
      atLoc = emailAddress.find(u'@')
      if atLoc == -1:
        if GC_Values[GC_DOMAIN]:
          emailAddress = u'{0}@{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
        return emailAddress
      elif atLoc != 0:
        if (atLoc == len(emailAddress)-1) and GC_Values[GC_DOMAIN]:
          emailAddress = u'{0}{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
        return emailAddress
      else:
        invalidArgumentExit(i, u'name@domain')
    elif OPTIONAL in opts and opts[OPTIONAL]:
      return None
  elif  OPTIONAL in opts and opts[OPTIONAL]:
    return None
  missingArgumentExit(OBJECT_EMAIL_ADDRESS_OR_UID if uidOK else OBJECT_EMAIL_ADDRESS)

def getPermissionId(i, anyoneAllowed=False):
  if i < len(sys.argv):
    emailAddress = sys.argv[i].strip().lower()
    if emailAddress:
      if emailAddress[:3] == u'id:':
        return (False, emailAddress[3:])
      atLoc = emailAddress.find(u'@')
      if atLoc == -1:
        if emailAddress == u'anyone':
          if anyoneAllowed:
            return (False, emailAddress)
          invalidArgumentExit(i, u'anyone not allowed')
        if GC_Values[GC_DOMAIN]:
          emailAddress = u'{0}@{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
        return (True, emailAddress)
      elif atLoc != 0:
        if (atLoc == len(emailAddress)-1) and GC_Values[GC_DOMAIN]:
          emailAddress = u'{0}{1}'.format(emailAddress, GC_Values[GC_DOMAIN])
        return (True, emailAddress)
      else:
        invalidArgumentExit(i, u'name@domain')
  missingArgumentExit(OBJECT_PERMISSION_ID)

#
# Products/SKUs
#
GOOGLE_APPS_PRODUCT = u'Google-Apps'
GOOGLE_COORDINATE_PRODUCT = u'Google-Coordinate'
GOOGLE_DRIVE_STORAGE_PRODUCT = u'Google-Drive-storage'
GOOGLE_VAULT_PRODUCT = u'Google-Vault'

GOOGLE_PRODUCTS = [
  GOOGLE_APPS_PRODUCT,
  GOOGLE_COORDINATE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_VAULT_PRODUCT,
]

GOOGLE_APPS_FOR_BUSINESS_SKU = GOOGLE_APPS_PRODUCT+u'-For-Business'
GOOGLE_APPS_FOR_POSTINI_SKU = GOOGLE_APPS_PRODUCT+u'-For-Postini'
GOOGLE_APPS_UNLIMITED_SKU = GOOGLE_APPS_PRODUCT+u'-Unlimited'
GOOGLE_COORDINATE_SKU = GOOGLE_COORDINATE_PRODUCT
GOOGLE_VAULT_SKU = GOOGLE_VAULT_PRODUCT
GOOGLE_VAULT_FORMER_EMPLOYEE_SKU = GOOGLE_VAULT_PRODUCT+u'-Former-Employee'
GOOGLE_DRIVE_STORAGE_20GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-20GB'
GOOGLE_DRIVE_STORAGE_50GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-50GB'
GOOGLE_DRIVE_STORAGE_200GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-200GB'
GOOGLE_DRIVE_STORAGE_400GB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-400GB'
GOOGLE_DRIVE_STORAGE_1TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-1TB'
GOOGLE_DRIVE_STORAGE_2TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-2TB'
GOOGLE_DRIVE_STORAGE_4TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-4TB'
GOOGLE_DRIVE_STORAGE_8TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-8TB'
GOOGLE_DRIVE_STORAGE_16TB_SKU = GOOGLE_DRIVE_STORAGE_PRODUCT+u'-16TB'

GOOGLE_SKUS = {
  GOOGLE_APPS_FOR_BUSINESS_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_FOR_POSTINI_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_APPS_UNLIMITED_SKU: GOOGLE_APPS_PRODUCT,
  GOOGLE_COORDINATE_SKU: GOOGLE_COORDINATE_PRODUCT,
  GOOGLE_VAULT_SKU: GOOGLE_VAULT_PRODUCT,
  GOOGLE_VAULT_FORMER_EMPLOYEE_SKU: GOOGLE_VAULT_PRODUCT,
  GOOGLE_DRIVE_STORAGE_20GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_50GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_200GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_400GB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_1TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_2TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_4TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_8TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
  GOOGLE_DRIVE_STORAGE_16TB_SKU: GOOGLE_DRIVE_STORAGE_PRODUCT,
}

GOOGLE_SKU_CHOICES_MAP = {
  u'apps': GOOGLE_APPS_FOR_BUSINESS_SKU,
  u'gafb': GOOGLE_APPS_FOR_BUSINESS_SKU,
  u'gafw': GOOGLE_APPS_FOR_BUSINESS_SKU,
  u'gams': GOOGLE_APPS_FOR_POSTINI_SKU,
  u'gau': GOOGLE_APPS_UNLIMITED_SKU,
  u'unlimited': GOOGLE_APPS_UNLIMITED_SKU,
  u'd4w': GOOGLE_APPS_UNLIMITED_SKU,
  u'dfw': GOOGLE_APPS_UNLIMITED_SKU,
  u'coordinate': GOOGLE_COORDINATE_SKU,
  u'vault': GOOGLE_VAULT_SKU,
  u'vfe': GOOGLE_VAULT_FORMER_EMPLOYEE_SKU,
  u'drive-20gb': GOOGLE_DRIVE_STORAGE_20GB_SKU,
  u'drive20gb': GOOGLE_DRIVE_STORAGE_20GB_SKU,
  u'20gb': GOOGLE_DRIVE_STORAGE_20GB_SKU,
  u'drive-50gb': GOOGLE_DRIVE_STORAGE_50GB_SKU,
  u'drive50gb': GOOGLE_DRIVE_STORAGE_50GB_SKU,
  u'50gb': GOOGLE_DRIVE_STORAGE_50GB_SKU,
  u'drive-200gb': GOOGLE_DRIVE_STORAGE_200GB_SKU,
  u'drive200gb': GOOGLE_DRIVE_STORAGE_200GB_SKU,
  u'200gb': GOOGLE_DRIVE_STORAGE_200GB_SKU,
  u'drive-400gb': GOOGLE_DRIVE_STORAGE_400GB_SKU,
  u'drive400gb': GOOGLE_DRIVE_STORAGE_400GB_SKU,
  u'400gb': GOOGLE_DRIVE_STORAGE_400GB_SKU,
  u'drive-1tb': GOOGLE_DRIVE_STORAGE_1TB_SKU,
  u'drive1tb': GOOGLE_DRIVE_STORAGE_1TB_SKU,
  u'1tb': GOOGLE_DRIVE_STORAGE_1TB_SKU,
  u'drive-2tb': GOOGLE_DRIVE_STORAGE_2TB_SKU,
  u'drive2tb': GOOGLE_DRIVE_STORAGE_2TB_SKU,
  u'2tb': GOOGLE_DRIVE_STORAGE_2TB_SKU,
  u'drive-4tb': GOOGLE_DRIVE_STORAGE_4TB_SKU,
  u'drive4tb': GOOGLE_DRIVE_STORAGE_4TB_SKU,
  u'4tb': GOOGLE_DRIVE_STORAGE_4TB_SKU,
  u'drive-8tb': GOOGLE_DRIVE_STORAGE_8TB_SKU,
  u'drive8tb': GOOGLE_DRIVE_STORAGE_8TB_SKU,
  u'8tb': GOOGLE_DRIVE_STORAGE_8TB_SKU,
  u'drive-16tb': GOOGLE_DRIVE_STORAGE_16TB_SKU,
  u'drive16tb': GOOGLE_DRIVE_STORAGE_16TB_SKU,
  u'16tb': GOOGLE_DRIVE_STORAGE_16TB_SKU,
  }

def getGoogleProductListMap(i):
  if i < len(sys.argv):
    productsOK = True
    products = sys.argv[i].replace(u',', u' ').split()
    productsMapped = []
    for product in products:
      if product in GOOGLE_PRODUCTS:
        productsMapped.append(product)
      else:
        product = product.lower()
        if product in GOOGLE_SKU_CHOICES_MAP:
          productsMapped.append(GOOGLE_SKUS[GOOGLE_SKU_CHOICES_MAP[product]])
        else:
          productsOK = False
    if productsOK:
      return productsMapped
    invalidChoiceExit(i, GOOGLE_SKU_CHOICES_MAP)
  missingArgumentExit(OBJECT_PRODUCT_ID_LIST)

MATCH_PRODUCT = u'matchProduct'

def getGoogleSKUMap(i, **opts):
  if i < len(sys.argv):
    skuOK = True
    sku = sys.argv[i].strip()
    if sku:
      if sku not in GOOGLE_SKUS:
        sku = sku.lower()
        if sku in GOOGLE_SKU_CHOICES_MAP:
          sku = GOOGLE_SKU_CHOICES_MAP[sku]
        else:
          skuOK = False
      if skuOK:
        if (not MATCH_PRODUCT in opts) or (GOOGLE_SKUS[sku] == opts[MATCH_PRODUCT]):
          return sku
      invalidChoiceExit(i, GOOGLE_SKU_CHOICES_MAP)
  missingArgumentExit(OBJECT_SKU_ID)

def getGoogleSKUListMap(i):
  if i < len(sys.argv):
    skusOK = True
    skus = sys.argv[i].replace(u',', u' ').split()
    skusMapped = []
    for sku in skus:
      if sku in GOOGLE_SKUS:
        skusMapped.append(GOOGLE_SKU_CHOICES_MAP[sku])
      else:
        sku = sku.lower()
        if sku in GOOGLE_SKU_CHOICES_MAP:
          skusMapped.append(GOOGLE_SKU_CHOICES_MAP[sku])
        else:
          skusOK = False
    if skusOK:
      return skusMapped
    invalidChoiceExit(i, GOOGLE_SKU_CHOICES_MAP)
  missingArgumentExit(OBJECT_SKU_ID_LIST)

def integerLimits(minVal, maxVal):
  if (minVal != None) and (maxVal != None):
    return u'integer {0}<=x<={1}'.format(minVal, maxVal)
  if minVal != None:
    return u'integer x>={0}'.format(minVal)
  if maxVal != None:
    return u'integer x<={0}'.format(maxVal)
  return u'integer x'

def getInteger(i, minVal=None, maxVal=None):
  if i < len(sys.argv):
    try:
      number = int(sys.argv[i].strip())
      if (not minVal or (number >= minVal)) and (not maxVal or (number <= maxVal)):
        return number
    except ValueError:
      pass
    invalidArgumentExit(i, integerLimits(minVal, maxVal))
  missingArgumentExit(integerLimits(minVal, maxVal))

def orgUnitPathQuery(path):
  return u"orgUnitPath='{0}'".format(path.replace(u"'", u"\'"))

def makeOrgUnitPathAbsolute(path):
  if path.startswith(u'/') or path.startswith(u'id:'):
    return path
  return u'/'+path

def makeOrgUnitPathRelative(path):
  if not path.startswith(u'/'):
    return path
  return path[1:]

def getOrgUnitPath(i, absolutePath=True):
  if i < len(sys.argv):
    path = sys.argv[i].strip()
    if path:
      if absolutePath:
        return makeOrgUnitPathAbsolute(path)
      else:
        return makeOrgUnitPathRelative(path)
  missingArgumentExit(OBJECT_ORGUNIT_PATH)

def getREPattern(i):
  if i < len(sys.argv):
    patstr = sys.argv[i]
    if patstr:
      try:
        pattern = re.compile(patstr)
        return pattern
      except re.error as e:
        usageErrorExit(i, u'{0} Error: {1}'.format(OBJECT_RE_PATTERN, e))
  missingArgumentExit(OBJECT_RE_PATTERN)

def getString(i, item, **opts):
  if i < len(sys.argv):
    argstr = sys.argv[i]
    if argstr:
      return argstr
    if (EMPTYOK in opts and opts[EMPTYOK]) or (OPTIONAL in opts and opts[OPTIONAL]):
      return u''
  elif  OPTIONAL in opts and opts[OPTIONAL]:
    return u''
  missingArgumentExit(item)

def getStringReturnInList(i, item):
  argstr = getString(i, item, emptyOK=True)
  if argstr:
    return [argstr]
  return []

DATETIME_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2}) *T? *(\d{2}):(\d{2}):(\d{2})?(\.(\d+)((Z|((\+|\-)\d{2}:\d{2})))?)?')
DATETIME_FORMAT = u'%Y-%m-%d %H:%M'
DATETIME_FORMAT_REQUIRED = u'yyyy-mm-dd hh:mm'

def getYYYYMMDDHHMM(i, **opts):
  if i < len(sys.argv):
    argstr = sys.argv[i].strip()
    if argstr:
      tg = DATETIME_PATTERN.match(argstr)
      if tg:
        tgg = tg.groups(u'0')
        try:
          datestr = datetime.datetime(int(tgg[0]), int(tgg[1]), int(tgg[2]),
                                      int(tgg[3]), int(tgg[4])).strftime(DATETIME_FORMAT)
          return datestr
        except:
          pass
        invalidArgumentExit(i, DATETIME_FORMAT_REQUIRED)
    elif OPTIONAL in opts and opts[OPTIONAL]:
      return u''
  elif  OPTIONAL in opts and opts[OPTIONAL]:
    return u''
  missingArgumentExit(DATETIME_FORMAT_REQUIRED)

DATE_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
DATE_FORMAT = u'%Y-%m-%d'
DATE_FORMAT_REQUIRED = u'yyyy-mm-dd'

def getYYYYMMDD(i, **opts):
  if i < len(sys.argv):
    argstr = sys.argv[i].strip()
    if argstr:
      tg = DATE_PATTERN.match(argstr)
      if tg:
        tgg = tg.groups(u'0')
        try:
          datestr = datetime.datetime(int(tgg[0]), int(tgg[1]), int(tgg[2])).strftime(DATE_FORMAT)
          return datestr
        except:
          pass
        invalidArgumentExit(i, DATE_FORMAT_REQUIRED)
    elif EMPTYOK in opts and opts[EMPTYOK]:
      return u''
  missingArgumentExit(DATE_FORMAT_REQUIRED)

TIME_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2}) *T? *(\d{2}):(\d{2}):(\d{2})(\.(\d+)((Z|((\+|\-)\d{2}:\d{2})))?)?')
TIME_FORMAT = u'%Y-%m-%dT%H:%M:%S.%f'
TIME_FORMAT_REQUIRED = u'yyyy-mm-dd[ |T]hh:mm:ss[.fff[Z]]'

def getTime(i, **opts):
  if i < len(sys.argv):
    argstr = sys.argv[i].strip()
    if argstr:
      tg = TIME_PATTERN.match(argstr)
      if tg:
        tgg = tg.groups(u'0')
        try:
          datestr = datetime.datetime(int(tgg[0]), int(tgg[1]), int(tgg[2]),
                                      int(tgg[3]), int(tgg[4]), int(tgg[5]),
                                      int(tgg[7]+[u'00000', u'0000', u'000', u'00', u'0', u''][len(tgg[7])-1])).strftime(TIME_FORMAT)+(tgg[8] if tgg[8] != u'0' else u'')
          return datestr
        except:
          pass
        invalidArgumentExit(i, TIME_FORMAT_REQUIRED)
    elif EMPTYOK in opts and opts[EMPTYOK]:
      return u''
  missingArgumentExit(TIME_FORMAT_REQUIRED)

EVENT_TIME_FORMAT_REQUIRED = u'allday yyyy-mm-dd | yyyy-mm-dd[ |T]hh:mm:ss[.fff[Z]]'

def getEventTime(i):
  if i < len(sys.argv):
    if sys.argv[i].strip().lower() == u'allday':
      return {u'date': getYYYYMMDD(i)}
    return {u'dateTime': getTime(i)}
  missingArgumentExit(EVENT_TIME_FORMAT_REQUIRED)

AGE_TIME_PATTERN = re.compile(r'(\d+)([mhd])')
AGE_TIME_FORMAT_REQUIRED = u'<Number>m|h|d'

def getAgeTime(i):
  if i < len(sys.argv):
    tg = AGE_TIME_PATTERN.match(sys.argv[i].strip())
    if tg:
      tgg = tg.groups(u'0')
      age_number = int(tgg[0])
      age_unit = tgg[1]
      now = int(time.time())
      if age_unit == u'm':
        age = now-(age_number*SECONDS_PER_MINUTE)
      elif age_unit == u'h':
        age = now-(age_number*SECONDS_PER_HOUR)
      else: # age_unit == u'd':
        age = now-(age_number*SECONDS_PER_DAY)
      return age
    invalidArgumentExit(i, AGE_TIME_FORMAT_REQUIRED)
  missingArgumentExit(AGE_TIME_FORMAT_REQUIRED)

def formatByteCount(fileSize):
  if fileSize < ONE_KILO_BYTES:
    return u'1kb'
  if fileSize < ONE_MEGA_BYTES:
    return u'{0}kb'.format(fileSize / ONE_KILO_BYTES)
  if fileSize < ONE_GIGA_BYTES:
    return u'{0}mb'.format(fileSize / ONE_MEGA_BYTES)
  return u'{0}gb'.format(fileSize / ONE_GIGA_BYTES)
#
# Get domain from email address
#
def getEmailAddressDomain(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return GC_Values[GC_DOMAIN].lower()
  return emailAddress[atLoc+1:].lower()
#
# Get user name from email address
#
def getEmailAddressUsername(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return emailAddress.lower()
  return emailAddress[:atLoc].lower()
#
# Split email address unto user and domain
#
def splitEmailAddress(emailAddress):
  atLoc = emailAddress.find(u'@')
  if atLoc == -1:
    return (emailAddress.lower(), GC_Values[GC_DOMAIN].lower())
  return (emailAddress[:atLoc].lower(), emailAddress[atLoc+1:].lower())
#
# Open a file
#
def openFile(filename, mode='rb'):
  try:
    if filename != u'-':
      f = open(filename, mode)
    else:
      f = StringIO.StringIO(unicode(sys.stdin.read()))
    return f
  except IOError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sys.exit(6)
#
# Close a file
#
def closeFile(f):
  try:
    f.close()
    return True
  except IOError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    return False
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
def writeFile(filename, data, mode='wb', continueOnError=False, displayError=True):
  try:
    with open(filename, mode) as f:
      f.write(data)
    return True
  except IOError as e:
    if continueOnError:
      if displayError:
        sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
      return False
    sys.exit(6)
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
    return self.reader.next().encode("utf-8")

class UnicodeDictReader(object):
  """
  A CSV reader which will iterate over lines in the CSV file "f",
  which is encoded in the given encoding.
  """

  def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
    f = UTF8Recoder(f, encoding)
    self.reader = csv.reader(f, dialect=dialect, **kwds)
    self.fieldnames = self.reader.next()

  def next(self):
    row = self.reader.next()
    vals = [unicode(s, "utf-8") for s in row]
    return dict((self.fieldnames[x], vals[x]) for x in range(len(self.fieldnames)))

  def __iter__(self):
    return self
#
class UnicodeReader(object):
  """
  A file reader which will iterate over lines in the file "f",
  which is encoded in the given encoding.
  """

  def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
    f = UTF8Recoder(f, encoding)
    self.reader = csv.reader(f, dialect=dialect, **kwds)

  def next(self):
    row = self.reader.next()
    return [unicode(s, "utf-8") for s in row]

  def __iter__(self):
    return self
#
# Set global variables from config file
# Check for GAM updates based on status of no_update_check in config file
#
def SetGlobalVariables():
  global GC_Values
  import ConfigParser, collections

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
    try:
      if os.environ[u'GAMUSERCONFIGDIR']:
        _getOldEnvVar(GC_CONFIG_DIR, u'GAMUSERCONFIGDIR')
    except KeyError:
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
    if value in TRUE_VALUES:
      return True
    if value in FALSE_VALUES:
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
    GC_DEFAULTS[GC_CONFIG_DIR] = os.environ[EV_GAM_CFG_HOME]
    GC_DEFAULTS[GC_CACHE_DIR] = os.path.join(GC_Values[GC_GAM_PATH], GAMCACHE)
    GC_DEFAULTS[GC_DRIVE_DIR] = GC_Values[GC_GAM_PATH]
  except KeyError:
# If GAM_CFG_HOME environment is not set, use getGAMPaths
    homePath = os.path.expanduser(u'~')
    GC_DEFAULTS[GC_CONFIG_DIR] = os.path.join(homePath, u'.gam')
    GC_DEFAULTS[GC_CACHE_DIR] = os.path.join(homePath, u'.gam', 'cache')
    GC_DEFAULTS[GC_DRIVE_DIR] = os.path.join(homePath, u'Downloads')
  gamCfgHome = GC_DEFAULTS[GC_CONFIG_DIR]

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
  if getChoice(i, SELECT_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    i += 1
    sectionName = getString(i, OBJECT_SECTION_NAME, emptyOK=True)
    if (not sectionName) or (sectionName.upper() == ConfigParser.DEFAULTSECT):
      sectionName = ConfigParser.DEFAULTSECT
    elif not gamcfg.has_section(sectionName):
      usageErrorExit(i, u'Section: {0}, Not Found'.format(sectionName))
    i += 1
    while i < len(sys.argv):
      if getChoice(i, SELECT_SAVE_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        gamcfg.set(ConfigParser.DEFAULTSECT, GC_SECTION, sectionName)
        _writeConfigFile(gamcfg, configFileName, action=u'Saved')
      elif getChoice(i, SELECT_VERIFY_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
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
  elif getChoice(i, CONFIG_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    i += 1
    sectionName = _getCfgSection(ConfigParser.DEFAULTSECT, GC_SECTION)
    while i < len(sys.argv):
      my_arg = getChoice(i, CONFIG_SUB_CMDS)
      i += 1
# create <SectionName> [overwrite]
      if my_arg == CONFIG_CREATE_CMD:
        value = getString(i, OBJECT_SECTION_NAME)
        if value.upper() == ConfigParser.DEFAULTSECT:
          usageErrorExit(i, u'Section: {0}, Invalid'.format(value))
        overwrite = getChoice(i, CONFIG_CREATE_OVERWRITE_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True)
        if overwrite:
          i += 1
        if gamcfg.has_section(value):
          if not overwrite:
            usageErrorExit(i-1, u'Section: {0}, Duplicate'.format(value))
        else:
          gamcfg.add_section(value)
        sectionName = value
# delete <SectionName>
      elif my_arg == CONFIG_DELETE_CMD:
        value = getString(i, OBJECT_SECTION_NAME)
        if value.upper() == ConfigParser.DEFAULTSECT:
          usageErrorExit(i, u'Section: {0}, Invalid'.format(value))
        if not gamcfg.has_section(value):
          usageErrorExit(i, u'Section: {0}, Not Found'.format(value))
        i += 1
        gamcfg.remove_section(value)
        sectionName = ConfigParser.DEFAULTSECT
        if gamcfg.get(ConfigParser.DEFAULTSECT, GC_SECTION, raw=True) == value:
          gamcfg.set(ConfigParser.DEFAULTSECT, GC_SECTION, u'')
# select <SectionName>
      elif my_arg == CONFIG_SELECT_CMD:
        value = getString(i, OBJECT_SECTION_NAME, emptyOK=True)
        if (not value) or (value.upper() == ConfigParser.DEFAULTSECT):
          value = u''
          sectionName = ConfigParser.DEFAULTSECT
        elif not gamcfg.has_section(value):
          usageErrorExit(i, u'Section: {0}, Not Found'.format(value))
        else:
          sectionName = value
        i += 1
# make <Directory>
      elif my_arg == CONFIG_MAKE_CMD:
        dstPath = os.path.expanduser(getString(i, OBJECT_FILE_PATH))
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
        srcFile = os.path.expanduser(getString(i, OBJECT_FILE_NAME))
        i += 1
        if not os.path.isabs(srcFile):
          srcFile = os.path.join(GC_Values[GC_GAM_PATH], srcFile)
        dstFile = os.path.expanduser(getString(i, OBJECT_FILE_NAME))
        i += 1
        if not os.path.isabs(dstFile):
          dstFile = os.path.join(gamcfg.get(sectionName, GC_CONFIG_DIR, raw=True), dstFile)
        data = readFile(srcFile, mode=u'rU')
        writeFile(dstFile, data)
# reset <VariableName>
      elif my_arg == CONFIG_RESET_CMD:
        itemName = getChoice(i, GC_DEFAULTS, choiceAliases=GC_VAR_ALIASES)
        i += 1
        if itemName in [GC_NO_UPDATE_CHECK]:
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
        itemName = getChoice(i, GC_DEFAULTS, choiceAliases=GC_VAR_ALIASES)
        i += 1
        if itemName == GC_SECTION:
          value = getString(i, OBJECT_STRING, emptyOK=True)
          i += 1
          if (not value) or (value.upper() == ConfigParser.DEFAULTSECT):
            value = u''
          elif not gamcfg.has_section(value):
            usageErrorExit(i-1, u'Section: {0}, Not Found'.format(value))
          gamcfg.set(ConfigParser.DEFAULTSECT, GC_SECTION, value)
          continue
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_BOOLEAN:
          value = TRUE if getBoolean(i) else FALSE
          i += 1
          if itemName == GC_NO_UPDATE_CHECK:
            gamcfg.set(ConfigParser.DEFAULTSECT, itemName, value)
            continue
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_INTEGER:
          minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS_KEY]
          value = str(getInteger(i, minVal=minVal, maxVal=maxVal))
          i += 1
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_DIRECTORY:
          value = getString(i, OBJECT_FILE_PATH)
          i += 1
          fullPath = os.path.expanduser(value)
          if (sectionName != ConfigParser.DEFAULTSECT) and (not os.path.isabs(fullPath)):
            fullPath = os.path.join(gamcfg.get(ConfigParser.DEFAULTSECT, itemName, raw=True), fullPath)
          if not os.path.isdir(fullPath):
            usageErrorExit(i-1, u'Invalid Path')
        elif GC_VAR_INFO[itemName][GC_VAR_TYPE_KEY] == GC_TYPE_FILE:
          value = getString(i, OBJECT_FILE_NAME, emptyOK=True)
          i += 1
        else:
          value = getString(i, OBJECT_STRING)
          i += 1
        gamcfg.set(sectionName, itemName, value)
# save
      elif my_arg == CONFIG_SAVE_CMD:
        _writeConfigFile(gamcfg, configFileName, action=u'Saved')
# backup <FileName>
      elif my_arg == CONFIG_BACKUP_CMD:
        fileName = os.path.expanduser(getString(i, OBJECT_FILE_NAME))
        i += 1
        if not os.path.isabs(fileName):
          fileName = os.path.join(gamCfgHome, fileName)
        _writeConfigFile(gamcfg, fileName, action=u'Backed up')
# restore <FileName>
      elif my_arg == CONFIG_RESTORE_CMD:
        fileName = os.path.expanduser(getString(i, OBJECT_FILE_NAME))
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
  GC_Values[GC_LAST_UPDATE_CHECK_TXT] = os.path.join(gamcfg.get(ConfigParser.DEFAULTSECT, GC_CONFIG_DIR, raw=True), LAST_UPDATE_CHECK_TXT)
  if not GC_Values[GC_NO_UPDATE_CHECK]:
    GAMCheckForUpdates()
# redirect (csv sectionname|<FileName>)|(stdout write|append sectionname|<FileName>)|(stderr write|append sectionname|<FileName>)
  while getChoice(i, REDIRECT_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    i += 1
    my_arg = getChoice(i, REDIRECT_SUB_CMDS)
    i += 1
# csv sectionname|<FileName>
    if my_arg == REDIRECT_CSV_CMD:
      _setCSVFile(getString(i, OBJECT_FILE_NAME))
      i += 1
# stdout write|append sectionname|<FileName>
# stderr write|append sectionname|<FileName>
    else:
      ext = u'out' if my_arg == REDIRECT_STDOUT_CMD else u'err'
      mode = getChoice(i, REDIRECT_MODE_MAP, mapChoice=True)
      i += 1
      _setSTDFile(getString(i, OBJECT_FILE_NAME), ext, mode)
      i += 1
  if GC_CSVFILE not in GC_Values:
    GC_Values[GC_CSVFILE] = sys.stdout
# Globals derived from config file values
  GC_Values[GC_CACERT_PEM] = os.path.join(GC_Values[GC_GAM_PATH], FN_CACERT_PEM)
  GC_Values[GC_EXTRA_ARGS] = {u'prettyPrint': GC_Values[GC_DEBUG_LEVEL] > 0}
  GC_Values[GC_OAUTH2SERVICE_KEY] = None
  GC_Values[GC_OAUTH2SERVICE_ACCOUNT_EMAIL] = None
  GC_Values[GC_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = None
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

def GAMCheckForUpdates(forceCheck=False):
  import urllib2
  try:
    current_version = float(__version__)
  except ValueError:
    return
  now_time = calendar.timegm(time.gmtime())
  if not forceCheck:
    last_check_time = readFile(GC_Values[GC_LAST_UPDATE_CHECK_TXT], continueOnError=True, displayError=forceCheck)
    if last_check_time == None:
      last_check_time = 0
    if last_check_time > now_time - 604800:
      return
  try:
    c = urllib2.urlopen(GAM_APPSPOT_LATEST_VERSION)
    try:
      latest_version = float(c.read())
    except ValueError:
      return
    if forceCheck or (latest_version > current_version):
      print u'Version: Check, Current: {0:.2f}, Latest: {1:.2f}'.format(current_version, latest_version)
    if latest_version <= current_version:
      writeFile(GC_Values[GC_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
      return
    a = urllib2.urlopen(GAM_APPSPOT_LATEST_VERSION_ANNOUNCEMENT)
    announcement = a.read()
    sys.stderr.write(announcement)
    try:
      printLine(MESSAGE_HIT_CONTROL_C_TO_UPDATE)
      time.sleep(15)
    except KeyboardInterrupt:
      import webbrowser
      webbrowser.open(GAM_RELEASES)
      printLine(MESSAGE_GAM_EXITING_FOR_UPDATE)
      sys.exit(0)
    writeFile(GC_Values[GC_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
    return
  except (urllib2.HTTPError, urllib2.URLError):
    return

def doGAMVersion(checkForCheck=True):
  import struct
  print u'GAM %s - http://git.io/gam\n%s\nPython %s.%s.%s %s-bit %s\ngoogle-api-python-client %s\n%s %s\nPath: %s' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2], struct.calcsize('P')*8, sys.version_info[3], googleapiclient.__version__,
                   platform.platform(), platform.machine(), GC_Values[GC_GAM_PATH])
  if checkForCheck:
    i = 2
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg == u'check':
        GAMCheckForUpdates(forceCheck=True)
        i += 1
      else:
        unknownArgumentExit(i)

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
      sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, terminating_error))
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
          sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e.content))
        if soft_errors:
          return
        sys.exit(5)
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
            error = {u'error': {u'errors': [{u'reason': u'invalid', u'message': message}]}}
          else:
            systemErrorExit(5, str(error))
        else:
          systemErrorExit(5, str(error))
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
      sys.stderr.write(u'{0}{1}: {2} - {3}\n'.format(ERROR_PREFIX, http_status, message, reason))
      if soft_errors:
        if n != 1:
          sys.stderr.write(u' - Giving up.\n')
        return
      else:
        sys.exit(int(http_status))
    except oauth2client.client.AccessTokenRefreshError, e:
      sys.stderr.write(u'{0}Authentication Token Error: {1}\n'.format(ERROR_PREFIX, e))
      sys.exit(403)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
    except TypeError, e:
      sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
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
      discovery = readFile(disc_file)
      service = googleapiclient.discovery.build_from_document(discovery, base=u'https://www.googleapis.com', http=http)
    else:
      print MESSAGE_NO_DISCOVERY_INFORMATION.format(disc_file)
      raise
  except httplib2.CertificateValidationUnsupported:
    noPythonSSLExit()
  except httplib2.ServerNotFoundError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sys.exit(8)
  if GC_Values[GC_DOMAIN] and not GC_Values[GC_CUSTOMER_ID]:
    resp, result = service._http.request(u'https://www.googleapis.com/admin/directory/v1/users?domain=%s&maxResults=1&fields=users(customerId)' % GC_Values[GC_DOMAIN])
    try:
      resultObj = json.loads(result)
    except ValueError:
      sys.stderr.write(u'{0}Unexpected response: {1}\n'.format(ERROR_PREFIX, result))
      sys.exit(8)
    if resp[u'status'] == u'403':
      try:
        message = resultObj[u'error'][u'errors'][0][u'message']
      except KeyError:
        message = resultObj[u'error'][u'message']
      sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, message))
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
  if not GC_Values[GC_OAUTH2SERVICE_KEY]:
    json_string = readFile(GC_Values[GC_OAUTH2SERVICE_JSON], continueOnError=True, displayError=True)
    if not json_string:
      printLine(MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON)
      printLine(GAM_WIKI_CREATE_CLIENT_SECRETS)
      systemErrorExit(15, None)
    json_data = json.loads(json_string)
    try:
      GC_Values[GC_OAUTH2SERVICE_ACCOUNT_EMAIL] = json_data[u'web'][u'client_email']
      GC_Values[GC_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = json_data[u'web'][u'client_id']
      GC_Values[GC_OAUTH2SERVICE_KEY] = readFile(GC_Values[GC_OAUTH2SERVICE_JSON].replace(u'.json', u'.p12'))
    except KeyError:
      # new format with config and data in the .json file...
      try:
        GC_Values[GC_OAUTH2SERVICE_ACCOUNT_EMAIL] = json_data[u'client_email']
        GC_Values[GC_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = json_data[u'client_id']
        GC_Values[GC_OAUTH2SERVICE_KEY] = json_data[u'private_key']
      except KeyError:
        printLine(MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON)
        printLine(GAM_WIKI_CREATE_CLIENT_SECRETS)
        systemErrorExit(17, NESSAGE_OAUTH2SERVICE_JSON_INVALID.format(GC_Values[GC_OAUTH2SERVICE_JSON]))
  scope = getAPIScope(api)
  if act_as == None:
    credentials = oauth2client.client.SignedJwtAssertionCredentials(GC_Values[GC_OAUTH2SERVICE_ACCOUNT_EMAIL], GC_Values[GC_OAUTH2SERVICE_KEY], scope=scope)
  else:
    credentials = oauth2client.client.SignedJwtAssertionCredentials(GC_Values[GC_OAUTH2SERVICE_ACCOUNT_EMAIL], GC_Values[GC_OAUTH2SERVICE_KEY], scope=scope, sub=act_as)
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
      systemErrorExit(18, MESSAGE_CLIENT_API_ACCESS_DENIED.format(GC_Values[GC_OAUTH2SERVICE_ACCOUNT_CLIENT_ID], u','.join(scope)))
      sys.exit(5)
    else:
      sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
      if soft_errors:
        return False
      sys.exit(4)

def buildActivityGAPIServiceObject(user, soft_errors=True):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'appsactivity', act_as=userEmail, soft_errors=soft_errors))

def buildCalendarGAPIServiceObject(user, soft_errors=True):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'calendar', act_as=userEmail, soft_errors=soft_errors))

def buildDriveGAPIServiceObject(user, soft_errors=True):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'drive', act_as=userEmail, soft_errors=soft_errors))

def buildGmailGAPIServiceObject(user, soft_errors=True):
  userEmail = convertUserUIDtoEmailAddress(user)
  return (userEmail, buildGAPIServiceObject(u'gmail', act_as=userEmail, soft_errors=soft_errors))

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
    sys.stderr.write(u'{0}Failed to parse as JSON: {1}\n'.format(ERROR_PREFIX, content))
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

#
# Convert User UID to email address
def convertUserUIDtoEmailAddress(emailAddressOrUID):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find(u'@') > 0:
    return normalizedEmailAddressOrUID
  try:
    cd = buildGAPIObject(u'directory')
    result = callGAPI(service=cd.users(), function=u'get',
                      throw_reasons=[u'userNotFound'],
                      userKey=normalizedEmailAddressOrUID, fields=u'primaryEmail')
    if u'primaryEmail' in result:
      return result[u'primaryEmail'].lower()
  except googleapiclient.errors.HttpError:
    pass
  return normalizedEmailAddressOrUID
#
# Add domain to foo or convert uid:xxx to foo
# Return (foo@bar.com, foo, bar.com)
def splitEmailAddressOrUID(emailAddressOrUID):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  atLoc = normalizedEmailAddressOrUID.find(u'@')
  if atLoc > 0:
    return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  try:
    cd = buildGAPIObject(u'directory')
    result = callGAPI(service=cd, function=u'get',
                      throw_reasons=[u'userNotFound'],
                      userKey=normalizedEmailAddressOrUID, fields=u'primaryEmail')
    if u'primaryEmail' in result:
      normalizedEmailAddressOrUID = result[u'primaryEmail'].lower()
      atLoc = normalizedEmailAddressOrUID.find(u'@')
      return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID[:atLoc], normalizedEmailAddressOrUID[atLoc+1:])
  except googleapiclient.errors.HttpError:
    pass
  return (normalizedEmailAddressOrUID, normalizedEmailAddressOrUID, GC_Values[GC_DOMAIN])
#
# Add domain to foo or convert uid:xxx to foo
# Return foo@bar.com
def addDomainToEmailAddressOrUID(emailAddressOrUID, addDomain):
  if emailAddressOrUID.find(u':') == -1:
    atLoc = emailAddressOrUID.find(u'@')
    if atLoc == -1:
      return u'{0}@{1}'.format(emailAddressOrUID, addDomain)
    if atLoc == len(emailAddressOrUID)-1:
      return u'{0}{1}'.format(emailAddressOrUID, addDomain)
    return emailAddressOrUID
  if emailAddressOrUID[:4].lower() == u'uid:':
    normalizedEmailAddressOrUID = emailAddressOrUID[4:]
  elif emailAddressOrUID[:3].lower() == u'id:':
    normalizedEmailAddressOrUID = emailAddressOrUID[3:]
  else:
    return u'{0}@{1}'.format(emailAddressOrUID, addDomain)
  try:
    cd = buildGAPIObject(u'directory')
    result = callGAPI(service=cd, function=u'get',
                      throw_reasons=[u'userNotFound'],
                      userKey=normalizedEmailAddressOrUID, fields=u'primaryEmail')
    if u'primaryEmail' in result:
      return result[u'primaryEmail'].lower()
  except googleapiclient.errors.HttpError:
    pass
  return normalizedEmailAddressOrUID

def geturl(url, dst):
  import urllib2
  u = urllib2.urlopen(url)
  f = openFile(dst, 'wb')
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
  closeFile(f)

def addTitleToCSVfile(title, titles, csvRows):
  if title not in csvRows[0]:
    csvRows[0][title] = title
    titles.append(title)
#
# fieldName is command line argument
# fieldNameTitleMap maps fieldName to API field name and CSV file header
#ARGUMENT_TO_FIELD_NAME_TITLE_MAP = {
#  u'admincreated': [u'adminCreated', u'Admin_Created'],
#  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
#  }
# fieldsList is the list of API fields
# fieldsTitles maps the API field name to the CSV file header
#
def addFieldToCSVfile(fieldName, fieldNameTitleMap, fieldsList, fieldsTitles, titles, csvRows):
  ftList = fieldNameTitleMap[fieldName]
  for i in range(0, len(ftList), 2):
    if ftList[i] not in fieldsTitles:
      fieldsList.append(ftList[i])
      fieldsTitles[ftList[i]] = ftList[i+1]
      addTitleToCSVfile(ftList[i+1], titles, csvRows)

def initializeTitlesCSVfile(baseTitles=None):
  titles = []
  csvRows = [{}]
  if baseTitles is not None:
    for title in baseTitles:
      addTitleToCSVfile(title, titles, csvRows)
  return (titles, csvRows)

def writeCSVfile(csvRows, titles, list_type, todrive):
  csv.register_dialect(u'nixstdout', lineterminator=u'\n')
  if todrive:
    string_file = StringIO.StringIO()
    writer = csv.DictWriter(string_file, fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  else:
    writer = csv.DictWriter(GC_Values[GC_CSVFILE], fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(csvRows)
  if todrive:
    columns = len(csvRows[0])
    rows = len(csvRows)
    cell_count = rows * columns
    if cell_count > 500000 or columns > 256:
      print u'{0}{1}'.format(WARNING_PREFIX, MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET)
      convert = False
    else:
      convert = True
    drive = buildGAPIObject(u'drive')
    string_data = string_file.getvalue()
    media = googleapiclient.http.MediaInMemoryUpload(string_data, mimetype=u'text/csv')
    result = callGAPI(service=drive.files(), function=u'insert', convert=convert,
                      body={u'description': makeQuotedList(sys.argv), u'title': u'%s - %s' % (GC_Values[GC_DOMAIN], list_type), u'mimeType': u'text/csv'},
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

REPORTS_PARAMETERS_SIMPLE_TYPES = [u'intValue', u'boolValue', u'datetimeValue', u'stringValue']

REPORT_CUSTOMER = u'customer'
REPORT_USER = u'user'

REPORT_CHOICES_MAP = {
  u'admin': u'admin',
  u'calendar': u'calendar',
  u'calendars': u'calendar',
  u'doc': u'drive',
  u'docs': u'drive',
  u'drive': u'drive',
  u'login': u'login',
  u'logins': u'login',
  u'token': u'token',
  u'tokens': u'token',
  u'customer': REPORT_CUSTOMER,
  u'customers': REPORT_CUSTOMER,
  u'domain': REPORT_CUSTOMER,
  u'user': REPORT_USER,
  u'users': REPORT_USER,
}

def showReport():
  rep = buildGAPIObject(u'reports')
  report = getChoice(2, REPORT_CHOICES_MAP, mapChoice=True)
  if GC_Values[GC_CUSTOMER_ID] == MY_CUSTOMER:
    GC_Values[GC_CUSTOMER_ID] = None
  date = filters = parameters = actorIpAddress = startTime = endTime = eventName = None
  to_drive = False
  userKey = 'all'
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'date':
      date = getYYYYMMDD(i+1)
      i += 2
    elif my_arg == u'start':
      startTime = getTime(i+1)
      i += 2
    elif my_arg == u'end':
      endTime = getTime(i+1)
      i += 2
    elif my_arg == u'event':
      eventName = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'user':
      userKey = getString(i+1, OBJECT_EMAIL_ADDRESS)
      if userKey != u'all':
        userKey = normalizeEmailAddressOrUID(userKey)
      i += 2
    elif my_arg in [u'filter', u'filters']:
      filters = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg in [u'fields', u'parameters']:
      parameters = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'ip':
      actorIpAddress = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'todrive':
      to_drive = True
      i += 1
    else:
      unknownArgumentExit(i)
  try_date = date
  if try_date == None:
    try_date = datetime.date.today()
  if report == REPORT_USER:
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
        sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, message))
        sys.exit(4)
      else:
        try_date = match_date.group(1)
    titles, csvRows = initializeTitlesCSVfile([u'email', u'date'])
    for user_report in usage:
      row = {u'email': user_report[u'entity'][u'userEmail'], u'date': str(try_date)}
      for item in user_report[u'parameters']:
        name = item[u'name']
        if name not in csvRows[0]:
          addTitleToCSVfile(name, titles, csvRows)
        for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
          if ptype in item:
            row[name] = item[ptype]
            break
        else:
          row[name] = u''
      csvRows.append(row)
    writeCSVfile(csvRows, titles, u'User Reports - {0}'.format(try_date), to_drive)
  elif report == REPORT_CUSTOMER:
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
        sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, message))
        sys.exit(4)
      else:
        try_date = match_date.group(1)
    titles, csvRows = initializeTitlesCSVfile([u'name', u'value', u'client_id'])
    auth_apps = list()
    for item in usage[0][u'parameters']:
      name = item[u'name']
      for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
        if ptype in item:
          csvRows.append({u'name': name, u'value': item[ptype]})
          break
      else:
        if u'msgValue' in item:
          if name == u'accounts:authorized_apps':
            for subitem in item[u'msgValue']:
              app = {}
              for an_item in subitem:
                if an_item == u'client_name':
                  app[u'name'] = u'App: {0}'.format(subitem[an_item])
                elif an_item == u'num_users':
                  app[u'value'] = u'{0} users'.format(subitem[an_item])
                elif an_item == u'client_id':
                  app[u'client_id'] = subitem[an_item]
              auth_apps.append(app)
    for app in auth_apps: # put apps at bottom
      csvRows.append(app)
    writeCSVfile(csvRows, titles, u'Customer Report - {0}'.format(try_date), to_drive)
  else:     # admin, calendar, drive, login, token
    page_message = getPageMessage(u'items', showTotal=False)
    activities = callGAPIpages(service=rep.activities(), function=u'list', page_message=page_message,
                               applicationName=report, userKey=userKey, customerId=GC_Values[GC_CUSTOMER_ID], actorIpAddress=actorIpAddress,
                               startTime=startTime, endTime=endTime, eventName=eventName, filters=filters)
    if len(activities) > 0:
      titles, csvRows = initializeTitlesCSVfile()
      for activity in activities:
        events = activity[u'events']
        del activity[u'events']
        activity_row = flatten_json(activity)
        for event in events:
          row = flatten_json(event)
          row.update(activity_row)
          for item in row:
            if item not in csvRows[0]:
              addTitleToCSVfile(item, titles, csvRows)
          csvRows.append(row)
      titles = [u'name'] + sorted(titles.remove(u'name'))
      writeCSVfile(csvRows, titles, u'{0} Activity Report'.format(report.capitalize()), to_drive)

def doDelegates(users):
  import gdata.apps.service
  cd = buildGAPIObject(u'directory')
  emailsettings = getEmailSettingsObject()
  getChoice(4, [u'to'])
  delegateEmail, _, delegateDomain = splitEmailAddressOrUID(getEmailAddress(5))
  count = len(users)
  i = 1
  for delegator in users:
    delegatorEmail, delegator, delegatorDomain = splitEmailAddressOrUID(delegator)
    emailsettings.domain = delegatorDomain
    print u"Giving %s delegate access to %s (%s of %s)" % (delegateEmail, delegatorEmail, i, count)
    i += 1
    delete_alias = False
    if delegateDomain == delegatorDomain:
      use_delegate_address = delegateEmail
    else:
      # Need to use an alias in delegator domain, first check to see if delegate already has one...
      aliases = callGAPI(service=cd.users().aliases(), function=u'list', userKey=delegateEmail)
      found_alias_in_delegatorDomain = False
      try:
        for alias in aliases[u'aliases']:
          aliasDomain = alias[u'alias'][alias[u'alias'].find(u'@')+1:].lower()
          if aliasDomain == delegatorDomain:
            use_delegate_address = alias[u'alias']
            print u'  Using existing alias %s for delegation' % use_delegate_address
            found_alias_in_delegatorDomain = True
            break
      except KeyError:
        pass
      if not found_alias_in_delegatorDomain:
        delete_alias = True
        use_delegate_address = u'%s@%s' % (''.join(random.sample(u'abcdefghijklmnopqrstuvwxyz0123456789', 25)), delegatorDomain)
        print u'  Giving %s temporary alias %s for delegation' % (delegateEmail, use_delegate_address)
        callGAPI(service=cd.users().aliases(), function=u'insert', userKey=delegateEmail, body={u'alias': use_delegate_address})
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
          if get_delegate[u'address'].lower() == delegateEmail: # Delegation is already in place
            print u'That delegation is already in place...'
            if delete_alias:
              print u'  Deleting temporary alias...'
              doDeleteAlias(alias_email=use_delegate_address)
            sys.exit(0) # Emulate functionality of duplicate delegation between users in same domain, returning clean
        # Now check if either user account is suspended or requires password change
        delegate_user_details = callGAPI(service=cd.users(), function=u'get', userKey=delegateEmail)
        delegator_user_details = callGAPI(service=cd.users(), function=u'get', userKey=delegatorEmail)
        if delegate_user_details[u'suspended'] == True:
          sys.stderr.write(u'{0}User {1} is suspended. You must unsuspend for delegation.\n'.format(ERROR_PREFIX, delegateEmail))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegator_user_details[u'suspended'] == True:
          sys.stderr.write(u'{0}User {1} is suspended. You must unsuspend for delegation.\n'.format(ERROR_PREFIX, delegatorEmail))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegate_user_details[u'changePasswordAtNextLogin'] == True:
          sys.stderr.write(u'{0}User {1} is required to change password at next login. You must change password or clear changepassword flag for delegation.\n'.format(ERROR_PREFIX, delegateEmail))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegator_user_details[u'changePasswordAtNextLogin'] == True:
          sys.stderr.write(u'{0}User {1} is required to change password at next login. You must change password or clear changepassword flag for delegation.\n'.format(ERROR_PREFIX, delegatorEmail))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)

        # Guess it was just a normal backoff error then?
        if n == retries:
          sys.stderr.write(u' - Giving up.\n')
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
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'csv':
      csv_format = True
      i += 1
    else:
      unknownArgumentExit(i)
  for user in users:
    delegatorEmail, delegatorName, emailsettings.domain = splitEmailAddressOrUID(user)
    printGettingMessage(u"Getting delegates for %s...\n" % (delegatorEmail))
    delegates = callGData(service=emailsettings, function=u'GetDelegates', soft_errors=True, delegator=delegatorName)
    try:
      for delegate in delegates:
        if csv_format:
          print u'%s,%s,%s' % (delegatorEmail + u'@' + emailsettings.domain, delegate[u'address'], delegate[u'status'])
        else:
          print u"Delegator: %s\n Delegate: %s\n Status: %s\n Delegate Email: %s\n Delegate ID: %s\n" % (delegatorEmail, delegate[u'delegate'],
                                                                                                         delegate[u'status'], delegate[u'address'],
                                                                                                         delegate[u'delegationId'])
    except TypeError:
      pass

def deleteDelegate(users):
  emailsettings = getEmailSettingsObject()
  delegate = getEmailAddress(5)
  count = len(users)
  i = 1
  for user in users:
    delegatorEmail, delegatorName, emailsettings.domain = splitEmailAddressOrUID(user)
    delegateEmail = addDomainToEmailAddressOrUID(delegate, emailsettings.domain)
    print u"Deleting %s delegate access to %s (%s of %s)" % (delegateEmail, delegatorEmail, i, count)
    i += 1
    callGData(service=emailsettings, function=u'DeleteDelegate', delegate=delegateEmail, delegator=delegatorName)

PARTICIPANT_TYPES_MAP = {
  u'alias': u'alias',
  u'student': CL_ENTITY_STUDENTS,
  u'students': CL_ENTITY_STUDENTS,
  u'teacher': CL_ENTITY_TEACHERS,
  u'teachers': CL_ENTITY_TEACHERS,
  }
#
PARTICIPANT_ENTITY_NAME_MAP = {
  CL_ENTITY_STUDENTS: u'student',
  CL_ENTITY_TEACHERS: u'teacher',
  }

def doAddCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  courseId = getCourseId(2)
  cleanedCourseId = cleanCourseId(courseId)
  participant_type = getChoice(4, PARTICIPANT_TYPES_MAP, mapChoice=True)
  if participant_type == u'alias':
    service = croom.courses().aliases()
    body = {u'alias': normalizeCourseId(getString(5, OBJECT_COURSE_ALIAS))}
    callGAPI(service=service, function=u'create', courseId=courseId, body=body)
    print u'Added %s as a %s of course %s' % (cleanCourseId(body[u'alias']), participant_type, cleanedCourseId)
  else:
    if participant_type == CL_ENTITY_TEACHERS:
      service = croom.courses().teachers()
    else:
      service = croom.courses().students()
    _, entityList = getEntityToModify(5, defaultEntityType=CL_ENTITY_USERS, typeMap={CL_ENTITY_COURSEPARTICIPANTS: participant_type})
    role = PARTICIPANT_ENTITY_NAME_MAP[participant_type]
    for user in entityList:
      body = {'userId': normalizeEmailAddressOrUID(user)}
      callGAPI(service=service, function=u'create', courseId=courseId, body=body)
      print u'Added %s as a %s of course %s' % (cleanCourseId(body[u'userId']), role, cleanedCourseId)

def doSyncCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  courseId = getCourseId(2)
  cleanedCourseId = cleanCourseId(courseId)
  participant_type = getChoice(4, PARTICIPANT_TYPES_MAP, mapChoice=True)
  print
  currentParticipantsSet = set()
  for user in getUsersToModify(participant_type, courseId):
    currentParticipantsSet.add(normalizeEmailAddressOrUID(user))
  print
  _, syncParticipants = getEntityToModify(5, defaultEntityType=CL_ENTITY_USERS, typeMap={CL_ENTITY_COURSEPARTICIPANTS: participant_type})
  syncParticipantsSet = set()
  for user in syncParticipants:
    syncParticipantsSet.add(normalizeEmailAddressOrUID(user))
  if participant_type == CL_ENTITY_TEACHERS:
    service = croom.courses().teachers()
  else:
    service = croom.courses().students()
  role = PARTICIPANT_ENTITY_NAME_MAP[participant_type]
  for user in syncParticipantsSet-currentParticipantsSet:
    body = {'userId': normalizeEmailAddressOrUID(user)}
    callGAPI(service=service, function=u'create', courseId=courseId, body=body)
    print u'Added %s as a %s of course %s' % (cleanCourseId(body[u'userId']), role, cleanedCourseId)
  for user in currentParticipantsSet-syncParticipantsSet:
    kwargs = {'userId': normalizeEmailAddressOrUID(user)}
    callGAPI(service=service, function=u'delete', courseId=courseId, **kwargs)
    print u'Removed %s as a %s of course %s' % (cleanCourseId(kwargs[u'userId']), role, cleanedCourseId)

def doDeleteCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  courseId = getCourseId(2)
  cleanedCourseId = cleanCourseId(courseId)
  participant_type = getChoice(4, PARTICIPANT_TYPES_MAP, mapChoice=True)
  if participant_type == u'alias':
    service = croom.courses().aliases()
    kwargs = {u'alias': normalizeCourseId(getString(5, OBJECT_COURSE_ALIAS))}
    callGAPI(service=service, function=u'delete', courseId=courseId, **kwargs)
    print u'Removed %s as a %s of course %s' % (cleanCourseId(kwargs[u'alias']), participant_type, cleanedCourseId)
  else:
    if participant_type == CL_ENTITY_TEACHERS:
      service = croom.courses().teachers()
    else:
      service = croom.courses().students()
    _, entityList = getEntityToModify(5, defaultEntityType=CL_ENTITY_USERS, typeMap={CL_ENTITY_COURSEPARTICIPANTS: participant_type})
    role = PARTICIPANT_ENTITY_NAME_MAP[participant_type]
    for user in entityList:
      kwargs = {'userId': normalizeEmailAddressOrUID(user)}
      callGAPI(service=service, function=u'delete', courseId=courseId, **kwargs)
      print u'Removed %s as a %s of course %s' % (cleanCourseId(kwargs[u'userId']), role, cleanedCourseId)

def doDelCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = getCourseId(3)
  callGAPI(service=croom.courses(), function=u'delete', id=courseId)
  print u'Deleted Course %s' % courseId

COURSE_STATE_OPTIONS_MAP = {
  u'active': u'ACTIVE',
  u'archived': u'ARCHIVED',
  u'provisioned': u'PROVISIONED',
  u'declined': u'DECLINED',
  }

def doUpdateCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = getCourseId(3)
  body = {}
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'name':
      body[u'name'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'section':
      body[u'section'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'heading':
      body[u'descriptionHeading'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'description':
      body[u'description'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'room':
      body[u'room'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg in [u'state', u'status']:
      body[u'courseState'] = getChoice(i+1, COURSE_STATE_OPTIONS_MAP, mapChoice=True)
      i += 2
    else:
      unknownArgumentExit(i)
  updateMask = u','.join(body.keys())
  body[u'id'] = courseId
  result = callGAPI(service=croom.courses(), function=u'patch', id=courseId, body=body, updateMask=updateMask)
  print u'Updated Course %s' % result[u'id']

def doCreateCourse():
  croom = buildGAPIObject(u'classroom')
  body = dict()
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'name':
      body[u'name'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg in [u'alias', u'id']:
      body[u'id'] = getCourseAlias(i+1)
      i += 2
    elif my_arg == u'section':
      body[u'section'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'heading':
      body[u'descriptionHeading'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'description':
      body[u'description'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'room':
      body[u'room'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'teacher':
      body[u'ownerId'] = getEmailAddress(i+1)
      i += 2
    elif my_arg in [u'state', u'status']:
      body[u'courseState'] = getChoice(i+1, COURSE_STATE_OPTIONS_MAP, mapChoice=True)
      i += 2
    else:
      unknownArgumentExit(i)
  if not u'ownerId' in body:
    body['ownerId'] = u'me'
  if not u'name' in body:
    body['name'] = u'Unknown Course'
  result = callGAPI(service=croom.courses(), function=u'create', body=body)
  print u'Created course %s' % result[u'id']

def doGetCourseInfo():
  croom = buildGAPIObject(u'classroom')
  courseId = getCourseId(3)
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
      print u'  %s' % cleanCourseId(alias[u'alias'])
  print u'Participants:'
  print u' Teachers:'
  for teacher in teachers:
    try:
      print convertUTF8(u'  %s - %s' % (teacher[u'profile'][u'name'][u'fullName'], teacher[u'profile'][u'emailAddress']))
    except KeyError:
      print convertUTF8(u'  %s' % teacher[u'profile'][u'name'][u'fullName'])
  print u' Students:'
  for student in students:
    try:
      print convertUTF8(u'  %s - %s' % (student[u'profile'][u'name'][u'fullName'], student[u'profile'][u'emailAddress']))
    except KeyError:
      print convertUTF8(u'  %s' % student[u'profile'][u'name'][u'fullName'])

def doPrintCourses():
  croom = buildGAPIObject(u'classroom')
  titles, csvRows = initializeTitlesCSVfile([u'id'])
  todrive = False
  teacherId = None
  studentId = None
  get_aliases = False
  aliasesDelimiter = u' '
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'teacher':
      teacherId = getEmailAddress(i+1)
      i += 2
    elif my_arg == u'student':
      studentId = getEmailAddress(i+1)
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg in [u'alias', u'aliases']:
      get_aliases = True
      i += 1
    elif my_arg == u'delimiter':
      aliasesDelimiter = getString(i+1, OBJECT_STRING)
      i == 2
    else:
      unknownArgumentExit(i)
  printGettingMessage(u'Retrieving courses for organization (may take some time for large accounts)...\n')
  page_message = getPageMessage(u'courses')
  all_courses = callGAPIpages(service=croom.courses(), function=u'list', items=u'courses', page_message=page_message, teacherId=teacherId, studentId=studentId)
  for course in all_courses:
    csvRows.append(flatten_json(course))
    for item in csvRows[-1]:
      if item not in csvRows[0]:
        addTitleToCSVfile(item, titles, csvRows)
  if get_aliases:
    addTitleToCSVfile(u'Aliases', titles, csvRows)
    count = len(csvRows)-1
    i = 1
    for course in csvRows[1:]:
      i += 1
      courseId = course[u'id']
      printGettingMessage('Getting aliases for course %s (%s/%s)\n' % (courseId, i, count))
      course_aliases = callGAPIpages(service=croom.courses().aliases(), function=u'list', items=u'aliases', courseId=courseId)
      my_aliases = []
      for alias in course_aliases:
        my_aliases.append(cleanCourseId(alias[u'alias']))
      course[u'Aliases'] = aliasesDelimiter.join(my_aliases)
  writeCSVfile(csvRows, titles, u'Courses', todrive)

def doPrintCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  titles, csvRows = initializeTitlesCSVfile([u'courseId'])
  todrive = False
  courses = []
  teacherId = None
  studentId = None
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg in [u'course', u'class']:
      courses.append(getCourseId(i+1))
      i += 2
    elif my_arg == u'teacher':
      teacherId = getEmailAddress(i+1)
      i += 2
    elif my_arg == u'student':
      studentId = getEmailAddress(i+1)
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      unknownArgumentExit(i)
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
      csvRows.append(participant)
      for item in participant:
        if item not in titles:
          addTitleToCSVfile(item, titles, csvRows)
    for student in students:
      participant = flatten_json(student)
      participant[u'courseId'] = course_id
      participant[u'courseName'] = course[u'name']
      participant[u'userRole'] = u'STUDENT'
      csvRows.append(participant)
      for item in participant:
        if item not in titles:
          addTitleToCSVfile(item, titles, csvRows)
    y += 1
  writeCSVfile(csvRows, titles, u'Course Participants', todrive)

PRINTJOB_STATUS_MAP = {
  u'done': u'DONE',
  u'error': u'ERROR',
  u'held': u'HELD',
  u'inprogress': u'IN_PROGRESS',
  u'queued': u'QUEUED',
  u'submitted': u'SUBMITTED',
  }
# Map argument to API value
PRINTJOB_ASCENDINGORDER_MAP = {
  u'createtime': u'CREATE_TIME',
  u'status': u'STATUS',
  u'title': u'TITLE',
  }
# Map API value from ascending to descending
PRINTJOB_DESCENDINGORDER_MAP = {
  u'CREATE_TIME': u'CREATE_TIME_DESC',
  u'STATUS':  u'STATUS_DESC',
  u'TITLE': u'TITLE_DESC',
  }

def doPrintPrintJobs():
  cp = buildGAPIObject(u'cloudprint')
  titles, csvRows = initializeTitlesCSVfile([u'id', u'printerid'])
  todrive = False
  printerid = None
  owner = None
  status = None
  sortorder = None
  ascDesc = None
  query = None
  age = None
  older_or_newer = 0
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'olderthan':
      older_or_newer = 1
      age = getAgeTime(i+1)
      i += 2
    elif my_arg == u'newerthan':
      older_or_newer = -1
      age = getAgeTime(i+1)
      i += 2
    elif my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'status':
      status = getChoice(i+1, PRINTJOB_STATUS_MAP, mapChoice=True)
      i += 2
    elif my_arg in SORTORDER_CHOICES_MAP:
      ascDesc = SORTORDER_CHOICES_MAP[my_arg]
      i += 1
    elif my_arg == u'orderby':
      sortorder = getChoice(i+1, PRINTJOB_ASCENDINGORDER_MAP, mapChoice=True)
      i += 2
    elif my_arg in [u'printer', u'printerid']:
      printerid = getString(i+1, OBJECT_PRINTER_ID)
      i += 2
    elif my_arg in [u'owner', u'user']:
      owner = getEmailAddress(i+1, noUid=True)
      i += 2
    else:
      unknownArgumentExit(i)
  if sortorder and (ascDesc == u'DESCENDING'):
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  jobs = callGAPI(service=cp.jobs(), function=u'list', q=query, status=status, sortorder=sortorder, printerid=printerid, owner=owner)
  checkCloudPrintResult(jobs)
  for job in jobs[u'jobs']:
    createTime = int(job[u'createTime'])/1000
    if older_or_newer > 0:
      if createTime > age:
        continue
    elif older_or_newer < 0:
      if createTime < age:
        continue
    updateTime = int(job[u'updateTime'])/1000
    job[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
    job[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
    job[u'tags'] = u' '.join(job[u'tags'])
    csvRows.append(flatten_json(job))
    for item in csvRows[-1]:
      if item not in csvRows[0]:
        addTitleToCSVfile(item, titles, csvRows)
  writeCSVfile(csvRows, titles, u'Print Jobs', todrive)

def doPrintPrinters():
  cp = buildGAPIObject(u'cloudprint')
  titles, csvRows = initializeTitlesCSVfile([u'id'])
  todrive = False
  query = None
  printer_type = None
  connection_status = None
  extra_fields = None
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'type':
      printer_type = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'status':
      connection_status = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'extrafields':
      extra_fields = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      unknownArgumentExit(i)
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
    csvRows.append(flatten_json(printer))
    for item in csvRows[-1]:
      if item not in csvRows[0]:
        addTitleToCSVfile(item, titles, csvRows)
  writeCSVfile(csvRows, titles, u'Printers', todrive)

def changeCalendarAttendees(users):
  do_it = True
  i = 5
  allevents = False
  start_date = end_date = None
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'csv':
      csv_file = getString(i+1, OBJECT_FILE_NAME)
      i += 2
    elif my_arg == u'dryrun':
      do_it = False
      i += 1
    elif my_arg == u'start':
      start_date = getYYYYMMDD(i+1)
      i += 2
    elif my_arg == u'end':
      end_date = getYYYYMMDD(i+1)
      i += 2
    elif my_arg == u'allevents':
      allevents = True
      i += 1
    else:
      unknownArgumentExit(i)
  if not csv_file:
    usageErrorExit(i, u'csv <Filename> required')
  attendee_map = dict()
  f = openFile(csv_file)
  csvFile = csv.reader(f)
  for row in csvFile:
    attendee_map[row[0].lower()] = row[1].lower()
  closeFile(f)
  for user in users:
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    sys.stdout.write(u'Checking user %s\n' % user)
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
        if u'attendees' in event:
          for attendee in event[u'attendees']:
            if u'email' in attendee:
              old_email = attendee[u'email'].lower()
              if old_email in attendee_map:
                new_email = attendee_map[old_email]
                print u' SWITCHING attendee %s to %s for %s' % (old_email, new_email, event_summary)
                event[u'attendees'].remove(attendee)
                event[u'attendees'].append({u'email': new_email})
                needs_update = True
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
  calendarId = getEmailAddress(5)
  for user in users:
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    callGAPI(service=cal.calendarList(), function=u'delete', calendarId=calendarId)

CALENDAR_MIN_COLOR_INDEX = 1
CALENDAR_MAX_COLOR_INDEX = 24

CALENDAR_EVENT_MIN_COLOR_INDEX = 1
CALENDAR_EVENT_MAX_COLOR_INDEX = 11

CALENDAR_LIST_DEFAULT_REMINDERS_METHOD_MAP = {
  u'email': u'email',
  u'sms': u'sms',
  u'popup': u'popup',
  }
CALENDAR_LIST_NOTIFICATION_SETTINGS_NOTIFICATIONS_METHOD_MAP = {
  u'email': u'email',
  u'sms': u'_sms',
  }
CALENDAR_LIST_NOTIFICATION_SETTINGS_NOTIFICATIONS_TYPE_MAP = {
  u'eventcreation': u'eventCreation',
  u'eventchange': u'eventChange',
  u'eventcancellation': u'eventCancellation',
  u'eventresponse': u'eventResponse',
  u'agenda': u'agenda',
  }

def getCalendarAttributes(i, body):
  colorRgbFormat = False
  i = 6
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'selected':
      body[u'selected'] = getBoolean(i+1)
      i += 2
    elif my_arg == u'hidden':
      body[u'hidden'] = getBoolean(i+1)
      i += 2
    elif my_arg == u'summary':
      body[u'summaryOverride'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg in [u'colorindex', u'colorid']:
      body[u'colorId'] = str(getInteger(i+1, CALENDAR_MIN_COLOR_INDEX, CALENDAR_MAX_COLOR_INDEX))
      i += 2
    elif my_arg == u'backgroundcolor':
      body[u'backgroundColor'] = getColorHexAttribute(i+1)
      colorRgbFormat = True
      i += 2
    elif my_arg == u'foregroundcolor':
      body[u'foregroundColor'] = getColorHexAttribute(i+1)
      colorRgbFormat = True
      i += 2
    elif my_arg == u'reminder':
      body.setdefault(u'defaultReminders', [])
      body[u'defaultReminders'].append({u'method': getChoice(i+1, CALENDAR_LIST_DEFAULT_REMINDERS_METHOD_MAP, mapChoice=True),
                                        u'minutes': getInteger(i+2, minVal=0)})
      i += 3
    elif my_arg == u'notification':
      body.setdefault(u'notifications', [])
      body[u'notifications'].append({u'method': getChoice(i+1, CALENDAR_LIST_NOTIFICATION_SETTINGS_NOTIFICATIONS_METHOD_MAP, mapChoice=True),
                                     u'type': getChoice(i+2, CALENDAR_LIST_NOTIFICATION_SETTINGS_NOTIFICATIONS_TYPE_MAP, mapChoice=True)})
      i += 3
    else:
      unknownArgumentExit(i)
  return colorRgbFormat

def addCalendar(users):
  body = {u'id': getEmailAddress(5), u'selected': True, u'hidden': False}
  colorRgbFormat = getCalendarAttributes(6, body)
  i = 1
  count = len(users)
  for user in users:
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    print u"Subscribing %s to %s calendar (%s of %s)" % (user, body['id'], i, count)
    callGAPI(service=cal.calendarList(), function=u'insert', body=body, colorRgbFormat=colorRgbFormat)
    i += 1

def updateCalendar(users):
  calendarId = getEmailAddress(5)
  body = {}
  colorRgbFormat = getCalendarAttributes(6, body)
  i = 1
  count = len(users)
  for user in users:
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    print u"Updating %s's subscription to calendar %s (%s of %s)" % (user, calendarId, i, count)
    callGAPI(service=cal.calendarList(), function=u'update', calendarId=calendarId, body=body, colorRgbFormat=colorRgbFormat)

def doPrinterShowACL():
  cp = buildGAPIObject(u'cloudprint')
  show_printer = getString(2, OBJECT_PRINTER_ID)
  printer_info = callGAPI(service=cp.printers(), function=u'get', printerid=show_printer)
  checkCloudPrintResult(printer_info)
  for acl in printer_info[u'printers'][0][u'access']:
    if u'key' in acl:
      acl[u'accessURL'] = u'https://www.google.com/cloudprint/addpublicprinter.html?printerid=%s&key=%s' % (show_printer, acl[u'key'])
    print_json(None, acl)
    print

PRINTER_ROLE_MAP = {
  u'manager': u'MANAGER',
  u'owner': u'OWNER',
  u'user': u'USER',
}

def doPrinterAddACL():
  cp = buildGAPIObject(u'cloudprint')
  printer = getString(2, OBJECT_PRINTER_ID)
  role = getChoice(4, PRINTER_ROLE_MAP, mapChoice=True)
  scope = getString(5, OBJECT_EMAIL_ADDRESS).lower()
  public = None
  skip_notification = True
  if scope.lower() == u'public':
    public = True
    scope = None
    role = None
    skip_notification = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  result = callGAPI(service=cp.printers(), function=u'share', printerid=printer, role=role, scope=scope, public=public, skip_notification=skip_notification)
  checkCloudPrintResult(result)
  who = scope
  if who == None:
    who = 'public'
    role = 'user'
  print u'Added %s %s' % (role, who)

def doPrinterDelACL():
  cp = buildGAPIObject(u'cloudprint')
  printer = getString(2, OBJECT_PRINTER_ID)
  scope = getString(4, OBJECT_EMAIL_ADDRESS).lower()
  public = None
  if scope.lower() == u'public':
    public = True
    scope = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
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
  printerid = getString(2, OBJECT_PRINTER_ID)
  if printerid == u'any':
    printerid = None
  owner = None
  status = None
  sortorder = None
  ascDesc = None
  query = None
  age = None
  older_or_newer = 0
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'olderthan':
      older_or_newer = 1
      age = getAgeTime(i+1)
      i += 2
    elif my_arg == u'newerthan':
      older_or_newer = -1
      age = getAgeTime(i+1)
      i += 2
    elif my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'status':
      status = getChoice(i+1, PRINTJOB_STATUS_MAP, mapChoice=True)
      i += 2
    elif my_arg in SORTORDER_CHOICES_MAP:
      ascDesc = SORTORDER_CHOICES_MAP[my_arg]
      i += 1
    elif my_arg == u'orderby':
      sortorder = getChoice(i+1, PRINTJOB_ASCENDINGORDER_MAP, mapChoice=True)
      i += 2
    elif my_arg in [u'owner', u'user']:
      owner = getEmailAddress(i+1, noUid=True)
      i += 2
    else:
      unknownArgumentExit(i)
  if sortorder and (ascDesc == u'DESCENDING'):
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  result = callGAPI(service=cp.jobs(), function=u'list', q=query, status=status, sortorder=sortorder, printerid=printerid, owner=owner)
  if u'errorCode' in result and result[u'errorCode'] == 413:
    print u'No print jobs.'
    sys.exit(0)
  checkCloudPrintResult(result)
  valid_chars = u'-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  ssd = '''{
  "state": {"type": "DONE"}
}'''
  for job in result[u'jobs']:
    createTime = int(job[u'createTime'])/1000
    if older_or_newer > 0:
      if createTime > age:
        continue
    elif older_or_newer < 0:
      if createTime < age:
        continue
    fileUrl = job[u'fileUrl']
    jobid = job[u'id']
    fileName = job[u'title']
    fileName = u''.join(c if c in valid_chars else u'_' for c in fileName)
    fileName = u'%s-%s' % (fileName, jobid)
    _, content = cp._http.request(uri=fileUrl, method='GET')
    if writeFile(fileName, content, continueOnError=True):
#      ticket = callGAPI(service=cp.jobs(), function=u'getticket', jobid=jobid, use_cjt=True)
      result = callGAPI(service=cp.jobs(), function=u'update', jobid=jobid, semantic_state_diff=ssd)
      checkCloudPrintResult(result)
    print u'Printed job %s to %s' % (jobid, fileName)

def doDelPrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = getString(3, OBJECT_PRINTER_ID)
  result = callGAPI(service=cp.printers(), function=u'delete', printerid=printerid)
  checkCloudPrintResult(result)

def doGetPrinterInfo():
  cp = buildGAPIObject(u'cloudprint')
  printerid = getString(3, OBJECT_PRINTER_ID)
  everything = False
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'everything':
      everything = True
      i += 1
    else:
      unknownArgumentExit(i)
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
#
PRINTER_UPDATE_ITEMS_CHOICES_MAP = {
  u'currentquota': u'currentQuota',
  u'dailyquota': u'dailyQuota',
  u'defaultdisplayname': u'defaultDisplayName',
  u'description': u'description',
  u'displayname': u'displayName',
  u'firmware': u'firmware',
  u'gcpversion': u'gcpVersion',
  u'istosaccepted': u'isTosAccepted',
  u'manufacturer': u'manufacturer',
  u'model': u'model',
  u'name': u'name',
  u'ownerid': u'ownerId',
  u'proxy': u'proxy',
  u'public': u'public',
  u'quotaenabled': u'quotaEnabled',
  u'setupurl': u'setupUrl',
  u'status': u'status',
  u'supporturl': u'supportUrl',
  u'type': u'type',
  u'updateurl': u'updateUrl',
  u'uuid': u'uuid',
  }

def doUpdatePrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = getString(3, OBJECT_PRINTER_ID)
  kwargs = {}
  i = 4
  while i < len(sys.argv):
    my_arg = getChoice(i, PRINTER_UPDATE_ITEMS_CHOICES_MAP, mapChoice=True)
    if my_arg in [u'isTosAccepted', u'public', u'quotaEnabled']:
      value = getBoolean(i+1)
      i += 2
    elif my_arg in [u'currentQuota', u'dailyQuota', u'status']:
      value = getInteger(i+1, minVal=0)
      i += 2
    else:
      value = getString(i+1, OBJECT_STRING)
      i += 2
    kwargs[my_arg] = value
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
  cp = buildGAPIObject(u'cloudprint')
  jobid = getString(2, OBJECT_PRINTJOB_ID)
  printerid = getString(4, OBJECT_PRINTER_ID)
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
  cp = buildGAPIObject(u'cloudprint')
  printer = getString(2, OBJECT_PRINTER_ID)
  content = getString(4, OBJECT_STRING)
  form_fields = {u'printerid': printer,
                 u'title': content,
                 u'ticket': u'{"version": "1.0"}',
                 u'tags': [u'GAM', u'http://git.io/gam']}
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'tag':
      form_fields[u'tags'].append(getString(i+1, OBJECT_STRING))
      i += 2
    elif my_arg in [u'name', u'title']:
      form_fields[u'title'] = getString(i+1, OBJECT_STRING)
      i += 2
    else:
      unknownArgumentExit(i)
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
    filecontent = readFile(filepath)
    form_files[u'content'] = {u'filename': content, u'content': filecontent, u'mimetype': mimetype}
  #result = callGAPI(service=cp.printers(), function=u'submit', body=body)
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(service=cp.printers(), function=u'get', printerid=printer)
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/submit', method='POST', body=body, headers=headers)
  checkCloudPrintResult(result)
  if isinstance(result, str):
    result = json.loads(result)
  print u'Submitted print job %s' % result[u'job'][u'id']

def doDeletePrintJob():
  cp = buildGAPIObject(u'cloudprint')
  job = getString(2, OBJECT_PRINTJOB_ID)
  result = callGAPI(service=cp.jobs(), function=u'delete', jobid=job)
  checkCloudPrintResult(result)
  print u'Print Job %s deleted' % job

def doCancelPrintJob():
  cp = buildGAPIObject(u'cloudprint')
  job = getString(2, OBJECT_PRINTJOB_ID)
  ssd = '{"state": {"type": "ABORTED", "user_action_cause": {"action_code": "CANCELLED"}}}'
  result = callGAPI(service=cp.jobs(), function=u'update', jobid=job, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  print u'Print Job %s cancelled' % job

def checkCloudPrintResult(result):
  if isinstance(result, str):
    try:
      result = json.loads(result)
    except ValueError:
      sys.stderr.write(u'{0}Unexpected response: {1}\n'.format(ERROR_PREFIX, result))
      sys.exit(4)
  if not result[u'success']:
    sys.stderr.write(u'{0}{1}: {2}\n'.format(ERROR_PREFIX, result[u'errorCode'], result[u'message']))
    sys.exit(result[u'errorCode'])

def doCalendarShowACL():
  cal = buildGAPIObject(u'calendar')
  show_cal = getEmailAddress(2)
  acls = callGAPI(service=cal.acl(), function=u'list', calendarId=show_cal)
  try:
    for rule in acls[u'items']:
      print u'  Scope %s - %s' % (rule[u'scope'][u'type'], rule[u'scope'][u'value'])
      print u'  Role: %s' % (rule[u'role'])
      print u''
  except IndexError:
    pass

CALENDAR_ACL_ROLE_FREEBUSYREADER = u'freeBusyReader'
CALENDAR_ACL_ROLE_READER = u'reader'
CALENDAR_ACL_ROLE_WRITER = u'writer'
CALENDAR_ACL_ROLE_OWNER = u'owner'
CALENDAR_ACL_ROLE_NONE = u'none'

CALENDAR_ACL_ROLE_CHOICES_MAP = {
  u'freebusyreader': CALENDAR_ACL_ROLE_FREEBUSYREADER,
  u'freebusy': CALENDAR_ACL_ROLE_FREEBUSYREADER,
  u'read': CALENDAR_ACL_ROLE_READER,
  u'reader': CALENDAR_ACL_ROLE_READER,
  u'writer': CALENDAR_ACL_ROLE_WRITER,
  u'editor': CALENDAR_ACL_ROLE_WRITER,
  u'owner': CALENDAR_ACL_ROLE_OWNER,
  }

CALENDAR_ACL_SCOPE_DEFAULT = u'default'
CALENDAR_ACL_SCOPE_DOMAIN = u'domain'
CALENDAR_ACL_SCOPE_GROUP = u'group'
CALENDAR_ACL_SCOPE_USER = u'user'

CALENDAR_ACL_SCOPE_CHOICES_MAP = {
  u'default': CALENDAR_ACL_SCOPE_DEFAULT,
  u'user': CALENDAR_ACL_SCOPE_USER,
  u'group': CALENDAR_ACL_SCOPE_GROUP,
  u'domain': CALENDAR_ACL_SCOPE_DOMAIN,
  }

def getCalendarACLScope(cli):
  i = cli
  scopeType = getChoice(i, CALENDAR_ACL_SCOPE_CHOICES_MAP, defaultChoice=None, mapChoice=True)
  if scopeType:
    i += 1
  else:
    scopeType = CALENDAR_ACL_SCOPE_USER
  if scopeType == CALENDAR_ACL_SCOPE_DOMAIN:
    entity = getString(i, OBJECT_DOMAIN_NAME, optional=True)
    if entity:
      scopeValue = entity.lower()
    else:
      scopeValue = GC_Values[GC_DOMAIN]
  elif scopeType != CALENDAR_ACL_SCOPE_DEFAULT:
    scopeValue = getEmailAddress(i, noUid=True)
  else:
    scopeValue = None
  return (scopeType, scopeValue)

def getCalendarACLRuleId(i):
  scopeType, scopeValue = getCalendarACLScope(i)
  if scopeType != CALENDAR_ACL_SCOPE_DEFAULT:
    ruleId = u'{0}:{1}'.format(scopeType, scopeValue)
  else:
    ruleId = scopeType
  return ruleId

def doCalendarAddACL():
  cal = buildGAPIObject(u'calendar')
  calendarId = getEmailAddress(2)
  role = getChoice(4, CALENDAR_ACL_ROLE_CHOICES_MAP, mapChoice=True)
  scopeType, scopeValue = getCalendarACLScope(5)
  body = {u'role': role, u'scope': {u'type': scopeType}}
  if scopeType != CALENDAR_ACL_SCOPE_DEFAULT:
    body[u'scope'][u'value'] = scopeValue
  callGAPI(service=cal.acl(), function=u'insert', calendarId=calendarId, body=body)

def doCalendarUpdateACL():
  cal = buildGAPIObject(u'calendar')
  calendarId = getEmailAddress(2)
  body = {u'role': getChoice(4, CALENDAR_ACL_ROLE_CHOICES_MAP, mapChoice=True)}
  ruleId = getCalendarACLRuleId(5)
  callGAPI(service=cal.acl(), function=u'patch',
           calendarId=calendarId, ruleId=ruleId, body=body)

def doCalendarDeleteACL():
  cal = buildGAPIObject(u'calendar')
  calendarId = getEmailAddress(2)
  ruleId = getCalendarACLRuleId(4)
  callGAPI(service=cal.acl(), function=u'delete',
           calendarId=calendarId, ruleId=ruleId)

def doCalendarWipeEvents():
  cal = buildGAPIObject(u'calendar')
  calendarId = getEmailAddress(2)
  cal = buildGAPIServiceObject(u'calendar', calendarId)
  callGAPI(service=cal.calendars(), function=u'clear', calendarId=calendarId)

CALENDAR_EVENT_VISIBILITY_CHOICES_MAP = {
  u'default': u'default',
  u'public': u'public',
  u'private': u'private',
  }
CALENDAR_EVENT_REMINDERS_OVERRIDES_METHOD_MAP = {
  u'email': u'email',
  u'ssm': u'sms',
  u'popup': u'popup',
  }

def doCalendarAddEvent():
  cal = buildGAPIObject(u'calendar')
  calendarId = getEmailAddress(2)
  calendarId, cal = buildCalendarGAPIServiceObject(calendarId)
  if not cal:
    entityServiceNotApplicableWarning(u'Calerdar', calendarId)
    return
  sendNotifications = timeZone = None
  body = {}
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'notifyattendees':
      sendNotifications = True
      i += 1
    elif my_arg == u'attendee':
      body.setdefault(u'attendees', [])
      body[u'attendees'].append({u'email': getEmailAddress(i+1, noUid=True)})
      i += 2
    elif my_arg == u'optionalattendee':
      body.setdefault(u'attendees', [])
      body[u'attendees'].append({u'email': getEmailAddress(i+1, noUid=True), u'optional': True})
      i += 2
    elif my_arg == u'anyonecanaddself':
      body[u'anyoneCanAddSelf'] = True
      i += 1
    elif my_arg == u'description':
      body[u'description'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'start':
      body[u'start'] = getEventTime(i+1)
      i += 3 if u'date' in body[u'start'] else 2
    elif my_arg == u'end':
      body[u'end'] = getEventTime(i+1)
      i += 3 if u'date' in body[u'end'] else 2
    elif my_arg == u'guestscantinviteothers':
      body[u'guestsCanInviteOthers'] = False
      i += 1
    elif my_arg == u'guestscantseeothers':
      body[u'guestsCanSeeOtherGuests'] = False
      i += 1
    elif my_arg == u'id':
      body[u'id'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'summary':
      body[u'summary'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'location':
      body[u'location'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'available':
      body[u'transparency'] = u'transparent'
      i += 1
    elif my_arg == u'visibility':
      body[u'visibility'] = getChoice(i+1, CALENDAR_EVENT_VISIBILITY_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg == u'tentative':
      body[u'status'] = u'tentative'
      i += 1
    elif my_arg == u'source':
      body[u'source'] = {u'title': getString(i+1, OBJECT_STRING), u'url': getString(i+2, OBJECT_STRING)}
      i += 3
    elif my_arg == u'noreminders':
      body[u'reminders'] = {u'useDefault': False}
      i += 1
    elif my_arg == u'reminder':
      body.setdefault(u'reminders', {u'overrides': [], u'useDefault': False})
      body[u'reminders'][u'overrides'].append({u'method': getChoice(i+1, CALENDAR_EVENT_REMINDERS_OVERRIDES_METHOD_MAP, mapChoice=True),
                                               u'minutes': getInteger(i+2, minVal=0)})
      body[u'reminders'][u'useDefault'] = False
      i += 3
    elif my_arg == u'recurrence':
      body.setdefault(u'recurrence', [])
      body[u'recurrence'].append(getString(i+1, OBJECT_RECURRENCE))
      i += 2
    elif my_arg == u'timezone':
      timeZone = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'privateproperty':
      body.setdefault(u'extendedProperties', {u'private': {}, u'shared': {}})
      body[u'extendedProperties']['private'][getString(i+1, OBJECT_PROPERTY_KEY)] = getString(i+2, OBJECT_PROPERTY_KEY)
      i += 3
    elif my_arg == u'sharedproperty':
      body.setdefault(u'extendedProperties', {u'private': {}, u'shared': {}})
      body[u'extendedProperties']['shared'][getString(i+1, OBJECT_PROPERTY_KEY)] = getString(i+2, OBJECT_PROPERTY_KEY)
      i += 3
    elif my_arg in [u'colorindex', u'colorid']:
      body[u'colorId'] = str(getInteger(i+1, CALENDAR_EVENT_MIN_COLOR_INDEX, CALENDAR_EVENT_MAX_COLOR_INDEX))
      i += 2
    else:
      unknownArgumentExit(i)
  if not timeZone and u'recurrence' in body:
    timeZone = callGAPI(service=cal.calendars(), function=u'get', calendarId=calendarId, fields=u'timeZone')[u'timeZone']
  if u'recurrence' in body:
    for a_time in [u'start', u'end']:
      try:
        body[a_time][u'timeZone'] = timeZone
      except KeyError:
        pass
  callGAPI(service=cal.events(), function=u'insert', calendarId=calendarId, sendNotifications=sendNotifications, body=body)

PROFILE_SHARING_CHOICES_MAP = {
  u'share': True,
  u'shared': True,
  u'unshare': False,
  u'unshared': False,
  }

def doProfile(users):
  cd = buildGAPIObject(u'directory')
  body = {u'includeInGlobalAddressList': getChoice(4, PROFILE_SHARING_CHOICES_MAP, mapChoice=True)}
  count = len(users)
  i = 1
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    print u'Setting Profile Sharing to %s for %s (%s of %s)' % (body[u'includeInGlobalAddressList'], user, i, count)
    callGAPI(service=cd.users(), function=u'patch', soft_errors=True, userKey=user, body=body)
    i += 1

def showProfile(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    result = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'includeInGlobalAddressList')
    try:
      print u'User: %s  Profile Shared: %s (%s/%s)' % (user, result[u'includeInGlobalAddressList'], i, count)
    except IndexError:
      pass
    i += 1

def doPhoto(users):
  cd = buildGAPIObject(u'directory')
  filenamePattern = getString(5, OBJECT_PHOTO_FILENAME_PATTERN)
  i = 1
  count = len(users)
  for user in users:
    user, userName, _ = splitEmailAddressOrUID(user)
    filename = filenamePattern.replace(u'#user#', user)
    filename = filename.replace(u'#email#', user)
    filename = filename.replace(u'#username#', userName)
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
        with open(filename, 'rb') as f:
          image_data = f.read()
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
    user = normalizeEmailAddressOrUID(user)
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
    user = normalizeEmailAddressOrUID(user)
    print u"Deleting photo for %s (%s of %s)" % (user, i, count)
    callGAPI(service=cd.users().photos(), function='delete', userKey=user)
    i += 1

def printCalendar(userCalendar):
  print u'  Name: %s' % userCalendar['id']
  print convertUTF8(u'    Summary: %s' % userCalendar['summary'])
  print convertUTF8(u'    Description: %s' % userCalendar.get('description', u''))
  print u'    Access Level: %s' % userCalendar['accessRole']
  print u'    Timezone: %s' % userCalendar['timeZone']
  print convertUTF8(u'    Location: %s' % userCalendar.get('location', u''))
  print u'    Hidden: %s' % userCalendar.get('hidden', u'False')
  print u'    Selected: %s' % userCalendar.get('selected', u'False')
  print u'    Color ID: %s, Background Color: %s, Foreground Color: %s' % (userCalendar['colorId'], userCalendar['backgroundColor'], userCalendar['foregroundColor'])
  print u'    Default Reminders:'
  for reminder in userCalendar.get(u'defaultReminders', []):
    print u'      Type: %s  Minutes: %s' % (reminder['method'], reminder['minutes'])
  print u'    Notifications:'
  if u'notificationSettings' in userCalendar:
    for notification in userCalendar[u'notificationSettings'][u'notifications']:
      print u'      Method: %s, Type: %s' % (notification[u'method'], notification[u'type'])
  print u''

def showCalendars(users):
  for user in users:
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    feed = callGAPI(service=cal.calendarList(), function=u'list')
    print u'User: {0}'.format(user)
    for userCalendar in feed[u'items']:
      printCalendar(userCalendar)

def showCalSettings(users):
  for user in users:
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    feed = callGAPI(service=cal.settings(), function='list')
    for setting in feed[u'items']:
      print u'%s: %s' % (setting[u'id'], setting[u'value'])

def normalizeCalendarId(calendarId, user):
  if calendarId.lower() != u'primary':
    return calendarId
  return user
#
# <CalendarSettings> ::==
#	[description <String>] [location <String>] [summary <String>] [timezone <String>]
#
def getCalendarSettings(i, summaryRequired=False):
  body = {}
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'description':
      body[u'description'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'location':
      body[u'location'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'summary':
      body[u'summary'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'timezone':
      body[u'timeZone'] = getString(i+1, OBJECT_STRING)
      i += 2
    else:
      unknownArgumentExit(i)
  if summaryRequired and not body.get(u'summary', None):
    usageErrorExit(i, u'summary <String> required')
  return body
#
# gam <UserTypeEntity> create calendar <CalendarSettings>
#
def createCalendar(users):
  body = getCalendarSettings(5, summaryRequired=True)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    try:
      result = callGAPI(service=cal.calendars(), function=u'insert',
                        throw_reasons=[u'notFound'],
                        body=body)
      print u"Created %s's calendar %s (%s of %s)" % (user, result[u'id'], i, count)
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      if reason == u'notFound':
        print u'Error: The user %s does not exist (%s of %s)' % (user, i, count)
#
# gam <UserTypeEntity> modify calendar <EmailAddress>|primary <CalendarSettings>
#
def modifyCalendar(users):
  calendarIds = getString(5, OBJECT_EMAIL_ADDRESS)
  body = getCalendarSettings(6, summaryRequired=False)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    calendarId = normalizeCalendarId(calendarIds, user)
    try:
      callGAPI(service=cal.calendars(), function=u'patch',
               throw_reasons=[u'notFound'],
               calendarId=calendarId, body=body)
      print u"Modified %s's calendar %s (%s of %s)" % (user, calendarId, i, count)
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      message = error[u'error'][u'errors'][0][u'message']
      if reason == u'notFound':
        if u'userKey' in message:
          print u'Error: The user %s does not exist (%s of %s)' % (user, i, count)
        else:
          print u"Error: User %s's calendar %s does not exist (%s of %s)" % (user, calendarId, i, count)
#
# gam <UserTypeEntity> remove calendar <EmailAddress>
#
def removeCalendar(users):
  calendarIds = getString(5, OBJECT_EMAIL_ADDRESS)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    calendarId = normalizeCalendarId(calendarIds, user)
    try:
      callGAPI(service=cal.calendars(), function=u'delete',
               throw_reasons=[u'notFound', u'cannotDeletePrimaryCalendar', u'forbidden'],
               calendarId=calendarId)
      print u"Removed %s's calendar %s (%s of %s)" % (user, calendarId, i, count)
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      message = error[u'error'][u'errors'][0][u'message']
      if reason == u'notFound':
        if u'userKey' in message:
          print u'Error: The user %s does not exist (%s of %s)' % (user, i, count)
        else:
          print u"Error: User %s's calendar %s does not exist (%s of %s)" % (user, calendarId, i, count)
      else:
        print u"Error: Remove user %s's calendar %s not allowed (%s of %s)" % (user, calendarId, i, count)
#
# gam <UserTypeEntity> info calendar <EmailAddress>|primary
#
def infoCalendar(users):
  calendarIds = getString(5, OBJECT_EMAIL_ADDRESS)
  i = 0
  count = len(users)
  for user in users:
    i += 1
    user, cal = buildCalendarGAPIServiceObject(user)
    if not cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    calendarId = normalizeCalendarId(calendarIds, user)
    try:
      userCalendar = callGAPI(service=cal.calendarList(), function=u'get',
                              throw_reasons=[u'notFound'],
                              calendarId=calendarId)
      print u'User: {0}'.format(user)
      printCalendar(userCalendar)
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      message = error[u'error'][u'errors'][0][u'message']
      if reason == u'notFound':
        if u'userKey' in message:
          print u'Error: The user %s does not exist (%s of %s)' % (user, i, count)
        else:
          print u"Error: User %s's calendar %s does not exist (%s of %s)" % (user, calendarId, i, count)

def showDriveSettings(users):
  todrive = False
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      unknownArgumentExit(i)
  dont_show = [u'kind', u'selfLink', u'exportFormats', u'importFormats', u'maxUploadSizes', u'additionalRoleInfo', u'etag', u'features', u'user', u'isCurrentAppInstalled']
  count = 1
  titles, csvRows = initializeTitlesCSVfile([u'email'])
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    printGettingMessage(u'Getting Drive settings for %s (%s of %s)\n' % (user, count, len(users)))
    count += 1
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
          row[my_name] = formatByteCount(int(subsetting[u'bytesUsed']))
          if my_name not in csvRows[0]:
            addTitleToCSVfile(my_name, titles, csvRows)
        continue
      row[setting] = feed[setting]
      if setting not in csvRows[0]:
        addTitleToCSVfile(setting, titles, csvRows)
    csvRows.append(row)
  writeCSVfile(csvRows, titles, u'User Drive Settings', todrive)

def doDriveActivity(users):
  drive_ancestorId = u'root'
  drive_fileId = None
  todrive = False
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'fileid':
      drive_fileId = getString(i+1, OBJECT_DRIVE_FILE_ID)
      drive_ancestorId = None
      i += 2
    elif my_arg == u'folderid':
      drive_ancestorId = getString(i+1, OBJECT_DRIVE_FOLDER_ID)
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      unknownArgumentExit(i)
  titles, csvRows = initializeTitlesCSVfile()
  for user in users:
    user, activity = buildActivityGAPIServiceObject(user)
    if not activity:
      entityServiceNotApplicableWarning('User', user)
      continue
    page_message = getPageMessage(u'activities', forWhom=user, noNL=True)
    feed = callGAPIpages(service=activity.activities(), function=u'list', items=u'activities',
                         page_message=page_message, source=u'drive.google.com', userId=u'me',
                         drive_ancestorId=drive_ancestorId, groupingStrategy=u'none',
                         drive_fileId=drive_fileId, pageSize=500)
    for item in feed:
      csvRows.append(flatten_json(item[u'combinedEvent']))
      for an_item in csvRows[-1]:
        if an_item not in csvRows[0]:
          addTitleToCSVfile(an_item, titles, csvRows)
  writeCSVfile(csvRows, titles, u'Drive Activity', todrive)

def showDriveFileACL(users):
  fileId = getString(5, OBJECT_DRIVE_FILE_ID)
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    feed = callGAPI(service=drive.permissions(), function=u'list', fileId=fileId)
    for permission in feed[u'items']:
      try:
        print permission[u'name']
      except KeyError:
        pass
      for key in permission:
        if key in [u'name', u'kind', u'etag', u'selfLink',]:
          continue
        print u' %s: %s' % (key, permission[key])
      print u''

def delDriveFileACL(users):
  fileId = getString(5, OBJECT_DRIVE_FILE_ID)
  isEmail, permissionId = getPermissionId(6, anyoneAllowed=False)
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if isEmail:
      permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=permissionId, fields=u'id')[u'id']
    print u'Removing permission for %s from %s' % (permissionId, fileId)
    callGAPI(service=drive.permissions(), function=u'delete', fileId=fileId, permissionId=permissionId)

DRIVEFILE_ACL_ROLE_READER = u'reader'
DRIVEFILE_ACL_ROLE_COMMENTER = u'commenter'
DRIVEFILE_ACL_ROLE_WRITER = u'writer'
DRIVEFILE_ACL_ROLE_OWNER = u'owner'

DRIVEFILE_ACL_ROLES_MAP = {
  u'commenter': DRIVEFILE_ACL_ROLE_COMMENTER,
  u'editor': DRIVEFILE_ACL_ROLE_WRITER,
  u'owner': DRIVEFILE_ACL_ROLE_OWNER,
  u'reader': DRIVEFILE_ACL_ROLE_READER,
  u'writer': DRIVEFILE_ACL_ROLE_WRITER,
  }

DRIVEFILE_ACL_TYPE_USER = u'user'
DRIVEFILE_ACL_TYPE_GROUP = u'group'
DRIVEFILE_ACL_TYPE_DOMAIN = u'domain'
DRIVEFILE_ACL_TYPE_ANYONE = u'anyone'

DRIVEFILE_ACL_PERMISSION_TYPES_MAP = {
  u'anyone': DRIVEFILE_ACL_TYPE_ANYONE,
  u'domain': DRIVEFILE_ACL_TYPE_DOMAIN,
  u'group': DRIVEFILE_ACL_TYPE_GROUP,
  u'user': DRIVEFILE_ACL_TYPE_USER,
  }

def addDriveFileACL(users):
  sendNotificationEmails = False
  emailMessage = None
  fileId = getString(5, OBJECT_DRIVE_FILE_ID)
  body = {u'type': getChoice(6, DRIVEFILE_ACL_PERMISSION_TYPES_MAP, mapChoice=True)}
  if body[u'type'] == DRIVEFILE_ACL_TYPE_ANYONE:
    i = 7
  else:
    if body[u'type'] != DRIVEFILE_ACL_TYPE_DOMAIN:
      body[u'value'] = getEmailAddress(7)
    else:
      body[u'value'] = getString(7, OBJECT_DOMAIN_NAME)
    i = 8
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'withlink':
      body[u'withLink'] = True
      i += 1
    elif my_arg == u'role':
      body[u'role'] = getChoice(i+1, DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if body[u'role'] == DRIVEFILE_ACL_ROLE_COMMENTER:
        body[u'role'] = DRIVEFILE_ACL_ROLE_READER
        body[u'additionalRoles'] = [DRIVEFILE_ACL_ROLE_COMMENTER]
      i += 2
    elif my_arg == u'sendemail':
      sendNotificationEmails = True
      i += 1
    elif my_arg == u'emailmessage':
      sendNotificationEmails = True
      emailMessage = getString(i+1, OBJECT_STRING)
      i += 2
    else:
      unknownArgumentExit(i)
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    result = callGAPI(service=drive.permissions(), function=u'insert', fileId=fileId, sendNotificationEmails=sendNotificationEmails, emailMessage=emailMessage, body=body)
    print result

def updateDriveFileACL(users):
  fileId = getString(5, OBJECT_DRIVE_FILE_ID)
  isEmail, permissionId = getPermissionId(6, anyoneAllowed=False)
  transferOwnership = None
  body = {}
  i = 7
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'withlink':
      body[u'withLink'] = True
      i += 1
    elif my_arg == u'role':
      body[u'role'] = getChoice(i+1, DRIVEFILE_ACL_ROLES_MAP, mapChoice=True)
      if body[u'role'] == DRIVEFILE_ACL_ROLE_COMMENTER:
        body[u'role'] = DRIVEFILE_ACL_ROLE_READER
        body[u'additionalRoles'] = [DRIVEFILE_ACL_ROLE_COMMENTER]
      i += 2
    elif my_arg == u'transferownership':
      transferOwnership = getBoolean(i+1)
      i += 2
    else:
      unknownArgumentExit(i)
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if isEmail:
      permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=permissionId, fields=u'id')[u'id']
    print u'updating permissions for %s to file %s' % (permissionId, fileId)
    result = callGAPI(service=drive.permissions(), function=u'patch', fileId=fileId, permissionId=permissionId, transferOwnership=transferOwnership, body=body)
    print result

DRIVEFILE_FIELDS_CHOICES_MAP = {
  u'createddate': u'createdDate',
  u'description': u'description',
  u'fileextension': u'fileExtension',
  u'filesize': u'fileSize',
  u'id': u'id',
  u'lastmodifyinguser': u'lastModifyingUserName',
  u'lastmodifyingusername': u'lastModifyingUserName',
  u'lastviewedbyuser': u'lastViewedByMeDate',
  u'lastviewedbymedate': u'lastViewedByMeDate',
  u'md5': u'md5Checksum',
  u'md5sum': u'md5Checksum',
  u'md5checksum': u'md5Checksum',
  u'mimetype': u'mimeType',
  u'mime': u'mimeType',
  u'modifiedbyuser': u'modifiedByMeDate',
  u'modifiedbymedate': u'modifiedByMeDate',
  u'modifieddate': u'modifiedDate',
  u'originalfilename': u'originalFilename',
  u'quotaused': u'quotaBytesUsed',
  u'quotabytesused': u'quotaBytesUsed',
  u'shared': u'shared',
  u'writerscanshare': u'writersCanShare',
  }

DRIVEFILE_LABEL_CHOICES_MAP = {
  u'restricted': u'restricted',
  u'restrict': u'restricted',
  u'starred': u'starred',
  u'star': u'starred',
  u'trashed': u'trashed',
  u'trash': u'trashed',
  u'viewed': u'viewed',
  u'view': u'viewed',
}

def showDriveFiles(users):
  titles, csvRows = initializeTitlesCSVfile([u'Owner'])
  fieldsList = [u'title', u'owners', u'alternateLink']
  labelsList = []
  todrive = False
  query = u'"me" in owners'
  user_query = u''
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'anyowner':
      query = u''
      i += 1
    elif my_arg == u'query':
      user_query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'allfields':
      fieldsList = []
      i += 1
    elif my_arg in DRIVEFILE_FIELDS_CHOICES_MAP:
      fieldsList.append(DRIVEFILE_FIELDS_CHOICES_MAP[my_arg])
      i += 1
    elif my_arg in DRIVEFILE_LABEL_CHOICES_MAP:
      labelsList.append(DRIVEFILE_LABEL_CHOICES_MAP[my_arg])
      i += 1
    else:
      unknownArgumentExit(i)
  if user_query:
    if query:
      query = u'{0} and {1}'.format(query, user_query)
    else:
      query = user_query
  if fieldsList or labelsList:
    fields = u'nextPageToken'
    fields += u',items('
    if fieldsList:
      fields += u','.join(set(fieldsList))
      if labelsList:
        fields += u','
    if labelsList:
      fields += u'labels({0})'.format(u','.join(set(labelsList)))
    fields += u')'
  else:
    fields = u'*'
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    printGettingMessage(u'Getting files for %s...\n' % user)
    page_message = getPageMessage(u'files', forWhom=user)
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, soft_errors=True, q=query, maxResults=1000, fields=fields)
    for f_file in feed:
      a_file = {u'Owner': user}
      for attrib in f_file:
        if attrib in [u'kind', u'etags', u'etag', u'owners', u'parents', u'permissions']:
          continue
        if not isinstance(f_file[attrib], dict):
          if attrib not in csvRows[0]:
            addTitleToCSVfile(attrib, titles, csvRows)
          if isinstance(f_file[attrib], list):
            if isinstance(f_file[attrib][0], (unicode, bool)):
              a_file[attrib] = u' '.join(f_file[attrib])
            else:
              for j, l_attrib in enumerate(f_file[attrib]):
                for list_attrib in l_attrib:
                  if list_attrib in [u'kind', u'etags', u'etag']:
                    continue
                  x_attrib = u'{0}.{1}.{2}'.format(attrib, j, list_attrib)
                  if x_attrib not in csvRows[0]:
                    addTitleToCSVfile(x_attrib, titles, csvRows)
                  a_file[x_attrib] = l_attrib[list_attrib]
          elif isinstance(f_file[attrib], (unicode, bool)):
            a_file[attrib] = f_file[attrib]
          else:
            print u'File ID: {0}, Attribute: {1}, Unknown type: {2}'.format(f_file[u'id'], attrib, type(f_file[attrib]))
        else:
          for dict_attrib in f_file[attrib]:
            if dict_attrib in [u'kind', u'etags', u'etag']:
              continue
            if dict_attrib not in csvRows[0]:
              addTitleToCSVfile(dict_attrib, titles, csvRows)
            a_file[dict_attrib] = f_file[attrib][dict_attrib]
      csvRows.append(a_file)
  writeCSVfile(csvRows, titles, u'{0} {1} {2} Drive Files'.format(GC_Values[GC_DOMAIN], sys.argv[1], sys.argv[2]), todrive)

def doDriveSearch(drive, query=None):
  printGettingMessage(u'Searching for files with query: "%s"...\n' % query)
  page_message = getPageMessage(u'files')
  files = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, q=query, fields=u'nextPageToken,items(id)', maxResults=1000)
  ids = list()
  for f_file in files:
    ids.append(f_file[u'id'])
  return ids

DELETE_DRIVEFILE_CHOICES_MAP = {
  u'purge': u'delete',
  u'trash': u'trash',
  }
DRIVEFILE_FUNCTION_TO_ACTION_MAP = {
  u'delete': u'purging',
  u'trash': u'trashing',
  u'untrash': u'untrashing',
  }

def deleteDriveFile(users, function=None):
  fileId = getString(5, OBJECT_DRIVE_FILE_ID)
  if not function:
    function = getChoice(6, DELETE_DRIVEFILE_CHOICES_MAP, defaultChoice=u'trash', mapChoice=True)
  action = DRIVEFILE_FUNCTION_TO_ACTION_MAP[function]
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if fileId[:6].lower() == u'query:':
      fileIds = doDriveSearch(drive, query=fileId[6:])
    elif fileId[:14].lower() == u'drivefilename:':
      fileIds = doDriveSearch(drive, query=u'"me" in owners and title = "%s"' % fileId[14:])
    else:
      if fileId[:8].lower() == u'https://' or fileId[:7].lower() == u'http://':
        fileId = fileId[fileId.find(u'/d/')+3:]
        if fileId.find(u'/') != -1:
          fileId = fileId[:fileId.find(u'/')]
      fileIds = [fileId,]
    if not fileIds:
      print u'No files to %s for %s' % (function, user)
      continue
    i = 0
    count = len(fileIds)
    for fileId in fileIds:
      i += 1
      print u'%s %s for %s (%s of %s)' % (action, fileId, user, i, count)
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
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    root_folder = callGAPI(service=drive.about(), function=u'get', fields=u'rootFolderId')[u'rootFolderId']
    printGettingMessage(u'Getting all files for %s...\n' % user)
    page_message = getPageMessage(u'files', forWhom=user)
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message, maxResults=1000, fields=u'items(id,title,parents(id),mimeType),nextPageToken')
    printDriveFolderContents(feed, root_folder, 0)

def deleteEmptyDriveFolders(users):
  query = u'"me" in owners and mimeType = "application/vnd.google-apps.folder"'
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
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
#
# MIME types
APPLICATION_VND_GOOGLE_APPS = u'application/vnd.google-apps.'
MIME_TYPE_GA_DOCUMENT = APPLICATION_VND_GOOGLE_APPS+u'document'
MIME_TYPE_GA_DRAWING = APPLICATION_VND_GOOGLE_APPS+u'drawing'
MIME_TYPE_GA_FOLDER = APPLICATION_VND_GOOGLE_APPS+u'folder'
MIME_TYPE_GA_FORM = APPLICATION_VND_GOOGLE_APPS+u'form'
MIME_TYPE_GA_FUSIONTABLE = APPLICATION_VND_GOOGLE_APPS+u'fusiontable'
MIME_TYPE_GA_PRESENTATION = APPLICATION_VND_GOOGLE_APPS+u'presentation'
MIME_TYPE_GA_SCRIPT = APPLICATION_VND_GOOGLE_APPS+u'script'
MIME_TYPE_GA_SITES = APPLICATION_VND_GOOGLE_APPS+u'sites'
MIME_TYPE_GA_SPREADSHEET = APPLICATION_VND_GOOGLE_APPS+u'spreadsheet'

MIMETYPE_CHOICES_MAP = {
  u'gdoc': MIME_TYPE_GA_DOCUMENT,
  u'gdocument': MIME_TYPE_GA_DOCUMENT,
  u'gdrawing': MIME_TYPE_GA_DRAWING,
  u'gfolder': MIME_TYPE_GA_FOLDER,
  u'gdirectory': MIME_TYPE_GA_FOLDER,
  u'gform': MIME_TYPE_GA_FORM,
  u'gfusion': MIME_TYPE_GA_FUSIONTABLE,
  u'gpresentation': MIME_TYPE_GA_PRESENTATION,
  u'gscript': MIME_TYPE_GA_SCRIPT,
  u'gsite': MIME_TYPE_GA_SITES,
  u'gsheet': MIME_TYPE_GA_SPREADSHEET,
  u'gspreadsheet': MIME_TYPE_GA_SPREADSHEET,
  }

DFA_CONVERT = u'convert'
DFA_LOCALFILEPATH = u'localFilepath'
DFA_LOCALFILENAME = u'localFilename'
DFA_LOCALMIMETYPE = u'localMimeType'
DFA_OCR = u'ocr'
DFA_OCRLANGUAGE = u'ocrLanguage'
DFA_PARENTQUERY = u'parentQuery'

def initializeDriveFileAttributes():
  return ({}, {DFA_LOCALFILEPATH: None, DFA_LOCALFILENAME: None, DFA_LOCALMIMETYPE: None, DFA_CONVERT: None, DFA_OCR: None, DFA_OCRLANGUAGE: None, DFA_PARENTQUERY: None})

def getDriveFileAttribute(i, body, parameters, my_arg, update=False):
  if my_arg == u'localfile':
    parameters[DFA_LOCALFILEPATH] = getString(i, OBJECT_FILE_NAME)
    parameters[DFA_LOCALFILENAME] = ntpath.basename(parameters[DFA_LOCALFILEPATH])
    body.setdefault(u'title', parameters[DFA_LOCALFILENAME])
    body[u'mimeType'] = mimetypes.guess_type(parameters[DFA_LOCALFILEPATH])[0]
    if body[u'mimeType'] == None:
      body[u'mimeType'] = u'application/octet-stream'
    parameters[DFA_LOCALMIMETYPE] = body[u'mimeType']
    i += 2
  elif my_arg == u'convert':
    parameters[DFA_CONVERT] = True
    i += 1
  elif my_arg == u'ocr':
    parameters[DFA_OCR] = True
    i += 1
  elif my_arg == u'ocrlanguage':
    parameters[DFA_OCRLANGUAGE] = getChoice(i, LANGUAGE_CODES_MAP, mapChoice=True)
    i += 2
  elif my_arg in DRIVEFILE_LABEL_CHOICES_MAP:
    body.setdefault(u'labels', {})
    if update:
      body[u'labels'][DRIVEFILE_LABEL_CHOICES_MAP[my_arg]] = getBoolean(i+1)
      i += 2
    else:
      body[u'labels'][DRIVEFILE_LABEL_CHOICES_MAP[my_arg]] = True
      i += 1
  elif my_arg == u'lastviewedbyme':
    body[u'lastViewedByMeDate'] = getTime(i)
    i += 2
  elif my_arg == u'modifieddate':
    body[u'modifiedDate'] = getTime(i)
    i += 2
  elif my_arg == u'description':
    body[u'description'] = getString(i, OBJECT_STRING)
    i += 2
  elif my_arg == u'mimetype':
    body[u'mimeType'] = getChoice(i, MIMETYPE_CHOICES_MAP, mapChoice=True)
    i += 2
  elif my_arg == u'parentid':
    body.setdefault(u'parents', [])
    body[u'parents'].append({u'id': getString(i, OBJECT_DRIVE_FOLDER_ID)})
    i += 2
  elif my_arg == u'parentname':
    parameters[DFA_PARENTQUERY] = u"'me' in owners and mimeType = '{0}' and title = '{1}'".format(MIME_TYPE_GA_FOLDER, getString(i, OBJECT_DRIVE_FOLDER_NAME))
    i += 2
  elif my_arg == u'writerscantshare':
    body[u'writersCanShare'] = False
    i += 1
  else:
    unknownArgumentExit(i)
  return i

def doUpdateDriveFile(users):
  media_body = fileId = query = None
  operation = u'update'
  body, parameters = initializeDriveFileAttributes()
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'copy':
      operation = u'copy'
      i += 1
    elif my_arg == u'id':
      fileId = getString(i+1, OBJECT_DRIVE_FILE_ID)
      i += 2
    elif my_arg == 'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'drivefilename':
      query = u'"me" in owners and title = "%s"' % getString(i+1, OBJECT_DRIVE_FILE_NAME)
      i += 2
    elif my_arg == u'newfilename':
      body[u'title'] = getString(i+1, OBJECT_DRIVE_FILE_NAME)
      i += 2
    else:
      i = getDriveFileAttribute(i, body, parameters, my_arg, update=True)
  if not query and not fileId:
    usageErrorExit(i, u'You must specify a file ID with id argument, a file name with the drivefilename argument, or a search query with the query argument.')
  elif query and fileId:
    usageErrorExit(i, u'You cannot specify both the id and query/drivefilename arguments at the same time.')
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if parameters[DFA_PARENTQUERY]:
      more_parents = doDriveSearch(drive, query=parameters[DFA_PARENTQUERY])
      body.setdefault(u'parents', [])
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if query:
      fileIds = doDriveSearch(drive, query=query)
    else:
      if fileId[:8].lower() == 'https://' or fileId[:7].lower() == 'http://':
        fileId = fileId[fileId.find('/d/')+3:]
        if fileId.find('/') != -1:
          fileId = fileId[:fileId.find('/')]
      fileIds = [fileId,]
    if not fileIds:
      print u'No files to update for %s' % user
      continue
    if parameters[DFA_LOCALFILEPATH]:
      media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
    for fileId in fileIds:
      if operation == u'update':
        if media_body:
          result = callGAPI(service=drive.files(), function=u'update',
                            fileId=fileId, convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE], media_body=media_body, body=body, fields='id')
        else:
          result = callGAPI(service=drive.files(), function=u'patch',
                            fileId=fileId, convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE], body=body, fields='id,labels')
        if media_body:
          print u'Successfully updated %s drive file with content from %s' % (result[u'id'], parameters[DFA_LOCALFILENAME])
        else:
          print u'Successfully updated drive file/folder ID %s' % (result[u'id'])
      else:
        result = callGAPI(service=drive.files(), function=u'copy',
                          fileId=fileId, convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE], body=body, fields=u'id,labels')
        print u'Successfully copied %s to %s' % (fileId, result[u'id'])

def createDriveFile(users):
  media_body = None
  body, parameters = initializeDriveFileAttributes()
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'drivefilename':
      body[u'title'] = getString(i+1, OBJECT_DRIVE_FOLDER_NAME)
      i += 2
    else:
      i = getDriveFileAttribute(i, body, parameters, my_arg)
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if parameters[DFA_PARENTQUERY]:
      more_parents = doDriveSearch(drive, query=parameters[DFA_PARENTQUERY])
      body.setdefault(u'parents', [])
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if parameters[DFA_LOCALFILEPATH]:
      media_body = googleapiclient.http.MediaFileUpload(parameters[DFA_LOCALFILEPATH], mimetype=parameters[DFA_LOCALMIMETYPE], resumable=True)
    result = callGAPI(service=drive.files(), function=u'insert',
                      convert=parameters[DFA_CONVERT], ocr=parameters[DFA_OCR], ocrLanguage=parameters[DFA_OCRLANGUAGE], media_body=media_body, body=body, fields='id')
    if media_body:
      print u'Successfully uploaded %s to Drive file ID %s' % (parameters[DFA_LOCALFILENAME], result[u'id'])
    else:
      print u'Successfully created drive file/folder ID %s' % (result[u'id'])

DOCUMENT_FORMATS_MAP = {
  u'csv': [{u'mime': u'text/csv', u'.ext': u'.csv'}],
  u'html': [{u'mime': u'text/html', u'.ext': u'.html'}],
  u'txt': [{u'mime': u'text/plain', u'.ext': u'.txt'}],
  u'tsv': [{u'mime': u'text/tsv', u'.ext': u'.tsv'}],
  u'jpeg': [{u'mime': u'image/jpeg', u'.ext': u'.jpeg'}],
  u'jpg': [{u'mime': u'image/jpeg', u'.ext': u'.jpg'}],
  u'png': [{u'mime': u'image/png', u'.ext': u'.png'}],
  u'svg': [{u'mime': u'image/svg+xml', u'.ext': u'.svg'}],
  u'pdf': [{u'mime': u'application/pdf', u'.ext': u'.pdf'}],
  u'rtf': [{u'mime': u'application/rtf', u'.ext': u'.rtf'}],
  u'zip': [{u'mime': u'application/zip', u'.ext': u'.zip'}],
  u'pptx': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'.ext': u'.pptx'}],
  u'xlsx': [{u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'.ext': u'.xlsx'}],
  u'docx': [{u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'.ext': u'.docx'}],
  u'ms': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'.ext': u'.pptx'},
          {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'.ext': u'.xlsx'},
          {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'.ext': u'.docx'}],
  u'microsoft': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'.ext': u'.pptx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'.ext': u'.xlsx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'.ext': u'.docx'}],
  u'micro$oft': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'.ext': u'.pptx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'.ext': u'.xlsx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'.ext': u'.docx'}],
  u'odt': [{u'mime': u'application/vnd.oasis.opendocument.text', u'.ext': u'.odt'}],
  u'ods': [{u'mime': u'application/x-vnd.oasis.opendocument.spreadsheet', u'.ext': u'.ods'}],
  u'openoffice': [{u'mime': u'application/vnd.oasis.opendocument.text', u'.ext': u'.odt'},
                  {u'mime': u'application/x-vnd.oasis.opendocument.spreadsheet', u'.ext': u'.ods'}],
  }

def downloadDriveFile(users):
  query = fileId = None
  exportFormatName = u'openoffice'
  exportFormats = DOCUMENT_FORMATS_MAP[exportFormatName]
  target_folder = GC_Values[GC_DRIVE_DIR]
  safe_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'id':
      fileId = getString(i+1, OBJECT_DRIVE_FILE_ID)
      i += 2
    elif my_arg == 'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'drivefilename':
      query = u'"me" in owners and title = "%s"' % getString(i+1, OBJECT_DRIVE_FILE_NAME)
      i += 2
    elif my_arg == u'format':
      exportFormatChoices = getString(i+1, OBJECT_FORMAT_LIST).replace(u',', u' ').split()
      exportFormats = []
      for exportFormat in exportFormatChoices:
        if exportFormat in DOCUMENT_FORMATS_MAP:
          exportFormats.extend(DOCUMENT_FORMATS_MAP[exportFormat])
        else:
          invalidChoiceExit(i+1, DOCUMENT_FORMATS_MAP)
      i += 2
    elif my_arg == u'targetfolder':
      target_folder = getString(i+1, OBJECT_FILE_PATH)
      if not os.path.isdir(target_folder):
        os.makedirs(target_folder)
      i += 2
    else:
      unknownArgumentExit(i)
  if not query and not fileId:
    usageErrorExit(i, u'You must specify a file ID with id argument, a file name with the drivefilename argument, or a search query with the query argument.')
  elif query and fileId:
    usageErrorExit(i, u'You cannot specify both the id and query/drivefilename arguments at the same time.')
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if query:
      fileIds = doDriveSearch(drive, query=query)
    else:
      if fileId[:8].lower() == 'https://' or fileId[:7].lower() == 'http://':
        fileId = fileId[fileId.find('/d/')+3:]
        if fileId.find('/') != -1:
          fileId = fileId[:fileId.find('/')]
      fileIds = [fileId,]
    if not fileIds:
      print u'No files to download for %s' % user
      continue
    i = 0
    for fileId in fileIds:
      extension = None
      result = callGAPI(service=drive.files(), function=u'get', fileId=fileId, fields=u'fileSize,title,mimeType,downloadUrl,exportLinks')
      if result[u'mimeType'] == u'application/vnd.google-apps.folder':
        print convertUTF8(u'Skipping download of folder {0}'.format(result[u'title']))
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
            extension = exportFormat[u'.ext']
            break
        else:
          print convertUTF8(u'Skipping download of file {0}, Format {1} not available'.format(result[u'title'], ','.join(exportFormatChoices)))
          continue
      else:
        print convertUTF8(u'Skipping download of file {0}, No export link')
        continue
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
      print convertUTF8(my_line % filename)
      _, content = drive._http.request(download_url)
      writeFile(filename, content, continueOnError=True)

def showDriveFileInfo(users):
  fileId = getString(5, OBJECT_DRIVE_FILE_ID)
  for user in users:
    user, drive = buildDriveGAPIServiceObject(user)
    if not drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    if fileId[:6].lower() == u'query:':
      fileIds = doDriveSearch(drive, query=fileId[6:])
    elif fileId[:14].lower() == u'drivefilename:':
      fileIds = doDriveSearch(drive, query=u'"me" in owners and title = "%s"' % fileId[14:])
    else:
      if fileId[:8].lower() == u'https://' or fileId[:7].lower() == u'http://':
        fileId = fileId[fileId.find(u'/d/')+3:]
        if fileId.find(u'/') != -1:
          fileId = fileId[:fileId.find(u'/')]
      fileIds = [fileId,]
    if not fileIds:
      print u'No files to show for %s' % user
      continue
    for fileId in fileIds:
      feed = callGAPI(service=drive.files(), function=u'get', fileId=fileId)
      for setting in feed:
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
              for setti in settin:
                if setti == u'kind':
                  continue
                print convertUTF8(u' %s: %s' % (setti, settin[setti]))
              print ''
        elif setting_type == u"<type 'dict'>":
          print u'%s:' % setting
          for settin in feed[setting]:
            if settin == u'kind':
              continue
            print convertUTF8(u' %s: %s' % (settin, feed[setting][settin]))
        else:
          print convertUTF8(u'%s: %s' % (setting, feed[setting]))

def transferSecCals(users):
  target_user = getEmailAddress(5)
  addBody = {u'role': CALENDAR_ACL_ROLE_OWNER, u'scope': {u'type': CALENDAR_ACL_SCOPE_USER, u'value': target_user}}
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'keepuser':
      remove_source_user = False
      i += 1
    else:
      unknownArgumentExit(i)
  if remove_source_user:
    target_user, target_cal = buildCalendarGAPIServiceObject(target_user)
    if not target_cal:
      entityServiceNotApplicableWarning(u'User', u'{0} (Target)'.format(target_user))
      return
  for user in users:
    user, source_cal = buildCalendarGAPIServiceObject(user)
    if not source_cal:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    source_calendars = callGAPIpages(service=source_cal.calendarList(), function=u'list',
                                     minAccessRole=CALENDAR_ACL_ROLE_OWNER, showHidden=True, fields=u'items(id),nextPageToken')
    for source_cal in source_calendars:
      calendarId = source_cal[u'id']
      if calendarId.find(u'@group.calendar.google.com') != -1:
        callGAPI(service=source_cal.acl(), function=u'insert',
                 calendarId=calendarId, body=addBody)
        if remove_source_user:
          ruleId = u'{0}:{1}'.format(CALENDAR_ACL_SCOPE_USER, user)
          callGAPI(service=target_cal.acl(), function=u'delete',
                   calendarId=calendarId, ruleId=ruleId)

def transferDriveFiles(users):
  target_user = getEmailAddress(5)
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'keepuser':
      remove_source_user = False
      i += 1
    else:
      unknownArgumentExit(i)
  target_user, target_drive = buildDriveGAPIServiceObject(target_user)
  if not target_drive:
    entityServiceNotApplicableWarning(u'User', u'{0} (Target)'.format(target_user))
    return
  target_about = callGAPI(service=target_drive.about(), function=u'get', fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId')
  target_drive_free = int(target_about[u'quotaBytesTotal']) - int(target_about[u'quotaBytesUsed'])
  for user in users:
    counter = 0
    user, source_drive = buildDriveGAPIServiceObject(user)
    if not source_drive:
      entityServiceNotApplicableWarning(u'User', user)
      continue
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
  emailsettings = getEmailSettingsObject()
  enable = getBoolean(4)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting IMAP Access to %s for %s (%s of %s)" % (str(enable), user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateImap', soft_errors=True, username=userName, enable=enable)

def getImap(users):
  emailsettings = getEmailSettingsObject()
  i = 1
  count = len(users)
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    imapsettings = callGData(service=emailsettings, function=u'GetImap', soft_errors=True, username=userName)
    try:
      print u'User %s  IMAP Enabled:%s (%s of %s)' % (user, imapsettings[u'enable'], i, count)
    except TypeError:
      pass
    i += 1

def doLicense(users, operation):
  lic = buildGAPIObject(u'licensing')
  skuId = getGoogleSKUMap(5)
  productId = GOOGLE_SKUS[skuId]
  if operation == u'patch':
    i = 6
    if getChoice(i, FROM_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
      i += 1
    oldSkuId = getGoogleSKUMap(i)
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    if operation == u'delete':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=skuId, userId=user)
    elif operation == u'insert':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=skuId, body={u'userId': user})
    elif operation == u'patch':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=oldSkuId, userId=user, body={u'skuId': skuId})

EMAILSETTINGS_POP_ACTION_KEEP = u'KEEP'
EMAILSETTINGS_POP_ACTION_ARCHIVE = u'ARCHIVE'
EMAILSETTINGS_POP_ACTION_DELETE = u'DELETE'

EMAILSETTINGS_POP_ENABLE_FOR_ALL_MAIL = u'ALL_MAIL'
EMAILSETTINGS_POP_ENABLE_FOR_MAIL_FROM_NOW_ON = u'MAIL_FROM_NOW_ON'

EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP = {
  u'allmail': u'ALL_MAIL',
  u'newmail': u'MAIL_FROM_NOW_ON',
  u'mailfromnowon': u'MAIL_FROM_NOW_ON',
  }

EMAILSETTINGS_POP_ACTION_CHOICES_MAP = {
  u'keep': u'KEEP',
  u'archive': u'ARCHIVE',
  u'delete': u'DELETE',
  }

def doPop(users):
  emailsettings = getEmailSettingsObject()
  enable = getBoolean(4)
  enable_for = u'ALL_MAIL'
  action = u'KEEP'
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'for':
      enable_for = getChoice(i+1, EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg == u'action':
      action = getChoice(i+1, EMAILSETTINGS_POP_ACTION_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg == u'confirm':
      i += 1
    else:
      unknownArgumentExit(i)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting POP Access to %s for %s (%s of %s)" % (str(enable), user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdatePop', soft_errors=True, username=userName, enable=enable, enable_for=enable_for, action=action)

def getPop(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    popsettings = callGData(service=emailsettings, function=u'GetPop', soft_errors=True, username=userName)
    try:
      print u'User %s  POP Enabled:%s  Action:%s' % (user, popsettings[u'enable'], popsettings[u'action'])
    except TypeError:
      pass

def doSendAs(users):
  emailsettings = getEmailSettingsObject()
  sendas = getEmailAddress(4, noUid=True)
  sendasName = getEmailAddress(5, noUid=True)
  make_default = reply_to = None
  i = 6
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'default':
      make_default = True
      i += 1
    elif my_arg == u'replyto':
      reply_to = getEmailAddress(i+1, noUid=True)
      i += 2
    else:
      unknownArgumentExit(i)
  if sendas.find(u'@') < 0:
    sendas = sendas+u'@'+GC_Values[GC_DOMAIN]
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Allowing %s to send as %s (%s of %s)" % (user, sendas, i, count)
    i += 1
    callGData(service=emailsettings, function=u'CreateSendAsAlias', soft_errors=True, username=userName, name=sendasName, address=sendas, make_default=make_default, reply_to=reply_to)

def showSendAs(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u'%s has the following send as aliases:' %  (user)
    sendases = callGData(service=emailsettings, function=u'GetSendAsAlias', soft_errors=True, username=userName)
    try:
      for sendas in sendases:
        if sendas[u'isDefault'] == TRUE:
          default = u'yes'
        else:
          default = u'no'
        if sendas[u'replyTo']:
          replyto = u' Reply To:<'+sendas[u'replyTo']+'>'
        else:
          replyto = u''
        if sendas[u'verified'] == TRUE:
          verified = u'yes'
        else:
          verified = u'no'
        print u' "%s" <%s>%s Default:%s Verified:%s' % (sendas[u'name'], sendas[u'address'], replyto, default, verified)
    except TypeError:
      pass
    print u''

def doLanguage(users):
  emailsettings = getEmailSettingsObject()
  language = getChoice(4, LANGUAGE_CODES_MAP, mapChoice=True)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting the language for %s to %s (%s of %s)" % (user, language, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateLanguage', soft_errors=True, username=userName, language=language)

def doUTF(users):
  emailsettings = getEmailSettingsObject()
  SetUTF = getBoolean(4)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting UTF-8 to %s for %s (%s of %s)" % (str(SetUTF), user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=userName, unicode=SetUTF)

VALID_PAGESIZES = [u'25', u'50', u'100']

def doPageSize(users):
  emailsettings = getEmailSettingsObject()
  PageSize = getChoice(4, VALID_PAGESIZES)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting Page Size to %s for %s (%s of %s)" % (PageSize, user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=userName, page_size=PageSize)

def doShortCuts(users):
  emailsettings = getEmailSettingsObject()
  SetShortCuts = getBoolean(4)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting Keyboard Short Cuts to %s for %s (%s of %s)" % (str(SetShortCuts), user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=userName, shortcuts=SetShortCuts)

def doArrows(users):
  emailsettings = getEmailSettingsObject()
  SetArrows = getBoolean(4)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting Personal Indicator Arrows to %s for %s (%s of %s)" % (str(SetArrows), user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=userName, arrows=SetArrows)

def doSnippets(users):
  emailsettings = getEmailSettingsObject()
  SetSnippets = getBoolean(4)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting Preview Snippets to %s for %s (%s of %s)" % (str(SetSnippets), user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=userName, snippets=SetSnippets)

LABEL_LABEL_LIST_VISIBILITY_CHOICES_MAP = {
  u'hide': u'labelHide',
  u'show': u'labelShow',
  u'showifunread': u'labelShowIfUnread',
  }
LABEL_MESSAGE_LIST_VISIBILITY_CHOICES_MAP = {
  u'hide': u'hide',
  u'show': u'show',
  }

def doLabel(users, cli):
  i = cli
  label = getString(i, OBJECT_LABEL_NAME)
  body = {u'name': label}
  i += 1
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'labellistvisibility':
      body[u'labelListVisibility'] = getChoice(i+1, LABEL_LABEL_LIST_VISIBILITY_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg == u'messagelistvisibility':
      body[u'messageListVisibility'] = getChoice(i+1, LABEL_MESSAGE_LIST_VISIBILITY_CHOICES_MAP, mapChoice=True)
      i += 2
    else:
      unknownArgumentExit(i)
  i = 1
  count = len(users)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user, soft_errors=True)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    print u"Creating label %s for %s (%s of %s)" % (label, user, i, count)
    i += 1
    callGAPI(service=gmail.users().labels(), function=u'create', soft_errors=True, userId=user, body=body)

def doDeleteMessages(users, trashOrDelete):
  query = None
  doIt = False
  maxToProcess = 1
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'doit':
      doIt = True
      i += 1
    elif my_arg in [u'maxtodelete', u'maxtotrash', u'maxtomove']:
      maxToProcess = getInteger(i+1, minVal=0)
      i += 2
    else:
      unknownArgumentExit(i)
  if not query:
    missingArgumentExit(OBJECT_QUERY)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user, soft_errors=True)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
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
  maxToProcess = 1
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'doit':
      doIt = True
      i += 1
    elif my_arg in [u'maxtodelete', u'maxtotrash', u'maxtomove']:
      maxToProcess = getInteger(i+1, minVal=0)
      i += 2
    else:
      unknownArgumentExit(i)
  if not query:
    missingArgumentExit(OBJECT_QUERY)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user, soft_errors=True)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
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

LABEL_TYPE_SYSTEM = u'system'
LABEL_TYPE_USER = u'user'

def doDeleteLabel(users):
  label = getString(5, OBJECT_LABEL_NAME)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user, soft_errors=True)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    printGettingMessage(u'Getting all labels for %s...\n' % user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user, fields=u'labels(name,id,type)')
    del_labels = []
    if label == u'--ALL_LABELS--':
      for del_label in labels[u'labels']:
        if del_label[u'type'] == LABEL_TYPE_SYSTEM:
          continue
        del_labels.append(del_label)
    elif label[:6].lower() == u'regex:':
      regex = label[6:]
      p = re.compile(regex)
      for del_label in labels[u'labels']:
        if del_label[u'type'] == LABEL_TYPE_SYSTEM:
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
  onlyUser = False
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'onlyuser':
      onlyUser = True
      i += 1
    else:
      unknownArgumentExit(i)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user, soft_errors=True)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user)
    for label in labels[u'labels']:
      if onlyUser and (label[u'type'] == LABEL_TYPE_SYSTEM):
        continue
      print convertUTF8(label[u'name'])
      for a_key in label:
        if a_key == u'name':
          continue
        print u' %s: %s' % (a_key, label[a_key])
      print u''

def showGmailProfile(users):
  todrive = False
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      unknownArgumentExit(i)
  titles, csvRows = initializeTitlesCSVfile([u'messagesTotal', u'emailAddress', u'historyId', u'threadsTotal'])
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user, soft_errors=True)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    printGettingMessage('Getting Gmail profile for %s\n' % user)
    results = callGAPI(service=gmail.users(), function=u'getProfile', userId=u'me', soft_errors=True)
    for item in results:
      if item not in csvRows[0]:
        addTitleToCSVfile(item, titles, csvRows)
    csvRows.append(results)
  writeCSVfile(csvRows, titles, u'Gmail Profiles', todrive)

def updateLabels(users):
  label_name = getString(5, OBJECT_LABEL_NAME)
  body = {}
  i = 6
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'name':
      body[u'name'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'labellistvisibility':
      body[u'labelListVisibility'] = getChoice(i+1, LABEL_LABEL_LIST_VISIBILITY_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg == u'messagelistvisibility':
      body[u'messageListVisibility'] = getChoice(i+1, LABEL_MESSAGE_LIST_VISIBILITY_CHOICES_MAP, mapChoice=True)
      i += 2
    else:
      unknownArgumentExit(i)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
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
    my_arg = getArgument(i)
    if my_arg == u'search':
      search = getString(i+1, OBJECT_RE_PATTERN)
      i += 2
    elif my_arg == u'replace':
      replace = getString(i+1, OBJECT_LABEL_REPLACEMENT)
      i += 2
    elif my_arg == u'merge':
      merge = True
      i += 1
    else:
      unknownArgumentExit(i)
  pattern = re.compile(search, re.IGNORECASE)
  for user in users:
    user, gmail = buildGmailGAPIServiceObject(user)
    if not gmail:
      entityServiceNotApplicableWarning(u'User', user)
      continue
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user)
    for label in labels[u'labels']:
      if label[u'type'] == LABEL_TYPE_SYSTEM:
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

FILTER_CONDITION_FROM = u'from'
FILTER_CONDITION_HASWORDS = u'haswords'
FILTER_CONDITION_MUSTHAVEATTACHMENT = u'musthaveattachment'
FILTER_CONDITION_NOWORDS = u'nowords'
FILTER_CONDITION_SUBJECT = u'subject'
FILTER_CONDITION_TO = u'to'

FILTER_CONDITION_CHOICES = [
  FILTER_CONDITION_FROM,
  FILTER_CONDITION_HASWORDS,
  FILTER_CONDITION_MUSTHAVEATTACHMENT,
  FILTER_CONDITION_NOWORDS,
  FILTER_CONDITION_SUBJECT,
  FILTER_CONDITION_TO,
  ]

FILTER_ACTION_ARCHIVE = u'archive'
FILTER_ACTION_FORWARD = u'forward'
FILTER_ACTION_LABEL = u'label'
FILTER_ACTION_MARKREAD = u'markread'
FILTER_ACTION_NEVERSPAM = u'neverspam'
FILTER_ACTION_STAR = u'star'
FILTER_ACTION_TRASH = u'trash'

FILTER_ACTION_CHOICES = [
  FILTER_ACTION_ARCHIVE,
  FILTER_ACTION_FORWARD,
  FILTER_ACTION_LABEL,
  FILTER_ACTION_MARKREAD,
  FILTER_ACTION_NEVERSPAM,
  FILTER_ACTION_STAR,
  FILTER_ACTION_TRASH,
  ]

def doFilter(users):
  emailsettings = getEmailSettingsObject()
  from_ = to = subject = has_the_word = does_not_have_the_word = has_attachment = label = should_mark_as_read = should_archive = should_star = forward_to = should_trash = should_not_spam = None
  haveCondition = False
  i = 4
  while i < len(sys.argv):
    value = getArgument(i)
    if value not in FILTER_CONDITION_CHOICES:
      break
    haveCondition = True
    if value == FILTER_CONDITION_FROM:
      from_ = getEmailAddress(i+1, noUid=True)
      i += 2
    elif value == FILTER_CONDITION_TO:
      to = getEmailAddress(i+1, noUid=True)
      i += 2
    elif value == FILTER_CONDITION_SUBJECT:
      subject = getString(i+1, OBJECT_STRING)
      i += 2
    elif value == FILTER_CONDITION_HASWORDS:
      has_the_word = getString(i+1, OBJECT_STRING)
      i += 2
    elif value == FILTER_CONDITION_NOWORDS:
      does_not_have_the_word = getString(i+1, OBJECT_STRING)
      i += 2
    elif value == FILTER_CONDITION_MUSTHAVEATTACHMENT:
      has_attachment = True
      i += 1
  if not haveCondition:
    missingChoiceExit(i, FILTER_CONDITION_CHOICES)
  haveAction = False
  while i < len(sys.argv):
    value = getChoice(i, FILTER_ACTION_CHOICES)
    haveAction = True
    if value == FILTER_ACTION_LABEL:
      label = getString(i+1, OBJECT_STRING)
      i += 2
    elif value == FILTER_ACTION_MARKREAD:
      should_mark_as_read = True
      i += 1
    elif value == FILTER_ACTION_ARCHIVE:
      should_archive = True
      i += 1
    elif value == FILTER_ACTION_STAR:
      should_star = True
      i += 1
    elif value == FILTER_ACTION_FORWARD:
      forward_to = getEmailAddress(i+1, noUid=True)
      i += 2
    elif value == FILTER_ACTION_TRASH:
      should_trash = True
      i += 1
    elif value == FILTER_ACTION_NEVERSPAM:
      should_not_spam = True
      i += 1
  if not haveAction:
    missingChoiceExit(i, FILTER_ACTION_CHOICES)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Creating filter for %s (%s of %s)" % (user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'CreateFilter', soft_errors=True,
              username=userName, from_=from_, to=to, subject=subject, has_the_word=has_the_word, does_not_have_the_word=does_not_have_the_word,
              has_attachment=has_attachment, label=label, should_mark_as_read=should_mark_as_read, should_archive=should_archive,
              should_star=should_star, forward_to=forward_to, should_trash=should_trash, should_not_spam=should_not_spam)

EMAILSETTINGS_FORWARD_ACTION_CHOICES_MAP = {
  u'archive': u'ARCHIVE',
  u'delete': u'DELETE',
  u'keep': u'KEEP',
  }

def doForward(users):
  emailsettings = getEmailSettingsObject()
  action = forward_to = None
  enable = getBoolean(4)
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg in EMAILSETTINGS_FORWARD_ACTION_CHOICES_MAP:
      action = EMAILSETTINGS_FORWARD_ACTION_CHOICES_MAP[my_arg]
      i += 1
    elif my_arg == u'confirm':
      i += 1
    elif my_arg.find(u'@') != -1:
      forward_to = sys.argv[i]
      i += 1
    else:
      unknownArgumentExit(i)
  if enable:
    if not action:
      missingChoiceExit(i, EMAILSETTINGS_FORWARD_ACTION_CHOICES_MAP)
    if not forward_to:
      missingArgumentExit(OBJECT_EMAIL_ADDRESS)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Turning forward %s for %s, emails will be %s (%s of %s)" % (enable, user, action, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateForwarding', soft_errors=True, username=userName, enable=enable, action=action, forward_to=forward_to)

def getForward(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    forward = callGData(service=emailsettings, function=u'GetForward', soft_errors=True, username=userName)
    try:
      print u"User %s:  Forward To:%s  Enabled:%s  Action:%s" % (user, forward[u'forwardTo'], forward[u'enable'], forward[u'action'])
    except TypeError:
      pass

def doSignature(users):
  import cgi
  emailsettings = getEmailSettingsObject()
  if getChoice(4, FILE_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    signature = cgi.escape(readFile(getString(5, OBJECT_FILE_NAME)).replace(u'\\n', u'&#xA;').replace(u'"', u"'"))
  else:
    signature = cgi.escape(getString(4, OBJECT_STRING, emptyOK=True)).replace(u'\\n', u'&#xA;').replace(u'"', u"'")
  xmlsig = u'''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <apps:property name="signature" value="%s" />
</atom:entry>''' % signature
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting Signature for %s (%s of %s)" % (user, i, count)
    uri = u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/signature' % (emailsettings.domain, userName)
    i += 1
    callGData(service=emailsettings, function=u'Put', soft_errors=True, data=xmlsig, uri=uri)

def getSignature(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    signature = callGData(service=emailsettings, function=u'GetSignature', soft_errors=True, username=userName)
    try:
      sys.stdout.write(u"User %s signature:\n  " % (user))
      print u" %s" % signature[u'signature']
    except TypeError:
      pass

def doWebClips(users):
  emailsettings = getEmailSettingsObject()
  enable = getBoolean(4)
  count = len(users)
  i = 1
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Turning Web Clips %s for %s (%s of %s)" % (enable, user, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateWebClipSettings', soft_errors=True, username=userName, enable=enable)

def doVacation(users):
  import cgi
  emailsettings = getEmailSettingsObject()
  subject = message = u''
  enable = getBoolean(4)
  contacts_only = domain_only = FALSE
  start_date = end_date = None
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'subject':
      subject = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'message':
      message = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'contactsonly':
      contacts_only = TRUE
      i += 1
    elif my_arg == u'domainonly':
      domain_only = TRUE
      i += 1
    elif my_arg == u'startdate':
      start_date = getYYYYMMDD(i+1)
      i += 2
    elif my_arg == u'enddate':
      end_date = getYYYYMMDD(i+1)
      i += 2
    elif my_arg == u'file':
      message = readFile(getString(i+1, OBJECT_FILE_NAME))
      i += 2
    else:
      unknownArgumentExit(i)
  i = 1
  count = len(users)
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
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    print u"Setting Vacation for %s (%s of %s)" % (user, i, count)
    uri = u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/vacation' % (emailsettings.domain, userName)
    i += 1
    callGData(service=emailsettings, function=u'Put', soft_errors=True, data=vacxml, uri=uri)

def getVacation(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    user, userName, emailsettings.domain = splitEmailAddressOrUID(user)
    vacationsettings = callGData(service=emailsettings, function=u'GetVacation', soft_errors=True, username=userName)
    print u'User {0}'.format(user)
    print u'Enabled: {0}'.format(vacationsettings[u'enable'])
    print u'Contacts Only: {0}'.format(vacationsettings[u'contactsOnly'])
    print u'Domain Only: {0}'.format(vacationsettings[u'domainOnly'])
    print u'Subject: {0}'.format(vacationsettings.get(u'subject', u'None'))
    print u'Message: {0}'.format(vacationsettings.get(u'message', u'None'))
    print u'Start Date: {0}'.format(vacationsettings[u'startDate'] if vacationsettings[u'startDate'] != NEVER_START_DATE else NEVER)
    print u'End Date: {0}'.format(vacationsettings[u'endDate'] if vacationsettings[u'endDate'] != NEVER_END_DATE else NEVER)

SCHEMA_FIELDTYPE_CHOICES_MAP = {
  u'bool': u'BOOL',
  u'date': u'DATE',
  u'double': u'DOUBLE',
  u'email': u'EMAIL',
  u'int64': u'INT64',
  u'phone': u'PHONE',
  u'string': u'STRING',
  }

DOMAIN_TYPE_CHOICES_MAP = {
  u'alias': u'DOMAIN_ALIAS',
  u'mirror': u'DOMAIN_ALIAS',
  u'domainalias': u'DOMAIN_ALIAS',
  u'aliasdomain': u'DOMAIN_ALIAS',
  u'secondary': u'MULTI_DOMAIN',
  u'separate': u'MULTI_DOMAIN',
  u'multidomain': u'MULTI_DOMAIN',
  u'multi': u'MULTI_DOMAIN',
  u'primary': u'PRIMARY',
  u'primarydomain': u'PRIMARY',
  u'home': u'PRIMARY',
  u'unknown': u'UNKNOWN',
  }

def doCreateDomain():
  cd = buildGAPIObject(u'directory')
  domain_name = getString(3, OBJECT_DOMAIN_NAME)
  domain_type = getChoice(4, DOMAIN_TYPE_CHOICES_MAP, mapChoice=True)
  body = {u'domain_name': domain_name, u'domain_type': domain_type}
  callGAPI(service=cd.domains(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'Added domain %s' % domain_name

def doDelSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = getString(3, OBJECT_SCHEMA_NAME)
  callGAPI(service=cd.schemas(), function=u'delete', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Deleted schema %s' % schemaKey

def doCreateOrUpdateUserSchema(function):
  cd = buildGAPIObject(u'directory')
  schemaName = getString(3, OBJECT_SCHEMA_NAME)
  body = {u'schemaName': schemaName, u'fields': []}
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'field':
      a_field = {u'fieldName': getString(i+1, OBJECT_FIELD_NAME), u'fieldType': u'STRING'}
      i += 2
      while i < len(sys.argv):
        my_arg = getArgument(i)
        if my_arg == u'type':
          a_field[u'fieldType'] = getChoice(i, SCHEMA_FIELDTYPE_CHOICES_MAP, mapChoice=True)
          i += 2
        elif my_arg in [u'multivalued', u'multivalue']:
          a_field[u'multiValued'] = True
          i += 1
        elif my_arg == u'indexed':
          a_field[u'indexed'] = True
          i += 1
        elif my_arg == u'restricted':
          a_field[u'readAccessType'] = u'ADMINS_AND_SELF'
          i += 1
        elif my_arg == u'range':
          a_field[u'numericIndexingSpec'] = {u'minValue': getInteger(i+1), u'maxValue': getInteger(i+2)}
          i += 3
        elif my_arg == u'endfield':
          body[u'fields'].append(a_field)
          i += 1
          break
        else:
          unknownArgumentExit(i)
    else:
      unknownArgumentExit(i)
  if function == u'insert':
    result = callGAPI(service=cd.schemas(), function=function, customerId=GC_Values[GC_CUSTOMER_ID], body=body)
    print 'Created user schema %s' % result[u'schemaName']
  else:
    result = callGAPI(service=cd.schemas(), function=function, customerId=GC_Values[GC_CUSTOMER_ID], body=body, schemaKey=schemaName)
    print 'Updated user schema %s' % result[u'schemaName']

def doPrintUserSchemas():
  cd = buildGAPIObject(u'directory')
  schemas = callGAPI(service=cd.schemas(), function=u'list', customerId=GC_Values[GC_CUSTOMER_ID])
  if not schemas or u'schemas' not in schemas:
    return
  for schema in schemas[u'schemas']:
    print u'Schema: %s' % schema[u'schemaName']
    for a_key in schema:
      if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
        print '%s: %s' % (a_key, schema[a_key])
    print
    for field in schema[u'fields']:
      print u' Field: %s' % field[u'fieldName']
      for a_key in field:
        if a_key not in [u'fieldName', u'kind', u'etag']:
          print '  %s: %s' % (a_key, field[a_key])
      print
    print

def doGetUserSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = getString(3, OBJECT_SCHEMA_NAME)
  schema = callGAPI(service=cd.schemas(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Schema: %s' % schema[u'schemaName']
  for a_key in schema:
    if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
      print '%s: %s' % (a_key, schema[a_key])
  print
  for field in schema[u'fields']:
    print u' Field: %s' % field[u'fieldName']
    for a_key in field:
      if a_key not in [u'fieldName', u'kind', u'etag']:
        print '  %s: %s' % (a_key, field[a_key])
    print

IM_TYPES = [u'custom', u'home', u'other', u'work']
IM_PROTOCOLS = [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'yahoo']
ADDRESS_TYPES = [u'custom', u'home', u'other', u'work']
ORGANIZATION_TYPES = [u'domain_only', u'school', u'unknown', u'work']
PHONE_TYPES = [u'assistant', u'callback', u'car', u'company_main', u'custom', u'grand_central', u'home', u'home_fax', u'isdn', u'main', u'mobile', u'other', u'other_fax', u'pager', u'radio', u'telex', u'tty_tdd', u'work', u'work_fax', u'work_mobile', u'work_pager']
RELATION_TYPES = [u'mother', u'father', u'sister', u'brother', u'manager', u'assistant', u'partner']
OTHEREMAIL_TYPES = [u'custom', u'home', u'other', u'work']
EXTERNALID_TYPES = [u'account', u'customer', u'network', u'organization']
WEBSITE_TYPES = [u'home_page', u'blog', u'profile', u'work', u'home', u'other', u'ftp', u'reservations', u'app_install_page']
NOTE_TYPES = [u'text_plain', u'text_html']

HASH_FUNCTION_MAP = {
  u'sha': u'SHA-1',
  u'sha1': u'SHA-1',
  u'sha-1': u'SHA-1',
  u'md5': u'MD5',
  u'crypt': u'crypt',
}

def clearBodyList(body, itemName):
  if itemName in body:
    del body[itemName]
  body.setdefault(itemName, None)

def appendItemToBodyList(body, itemName, itemValue):
  if (itemName in body) and (body[itemName] == None):
    del body[itemName]
  body.setdefault(itemName, [])
  body[itemName].append(itemValue)

def getUserAttributes(i, updateCmd=False, noUid=False):
  if not updateCmd:
    body = {u'name': {u'givenName': u'Unknown', u'familyName': u'Unknown'}}
    body[u'primaryEmail'] = getEmailAddress(i, noUid=noUid)
    i += 1
    need_password = True
  else:
    body = {}
    need_password = False
  need_to_hash_password = True
  admin_body = {}
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'firstname':
      body[u'name'][u'givenName'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'lastname':
      body[u'name'][u'familyName'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'password':
      body[u'password'] = getString(i+1, OBJECT_STRING)
      need_password = False
      i += 2
    elif my_arg == u'suspended':
      body[u'suspended'] = getBoolean(i+1)
      i += 2
    elif my_arg == u'gal':
      body[u'includeInGlobalAddressList'] = getBoolean(i+1)
      i += 2
    elif my_arg in HASH_FUNCTION_MAP:
      body[u'hashFunction'] = HASH_FUNCTION_MAP[my_arg]
      need_to_hash_password = False
      i += 1
    elif my_arg == u'nohash':
      need_to_hash_password = False
      i += 1
    elif my_arg == u'changepassword':
      body[u'changePasswordAtNextLogin'] = getBoolean(i+1)
      i += 2
    elif my_arg == u'ipwhitelisted':
      body[u'ipWhitelisted'] = getBoolean(i+1)
      i += 2
    elif my_arg == u'admin':
      admin_body = {u'status': getBoolean(i+1)}
      i += 2
    elif my_arg == u'agreedtoterms':
      body[u'agreedToTerms'] = getBoolean(i+1)
      i += 2
    elif my_arg in [u'org', u'ou']:
      body[u'orgUnitPath'] = getOrgUnitPath(i+1)
      i += 2
    elif my_arg == u'im':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'ims')
        continue
      im = dict()
      getChoice(i, [u'type'])
      i += 1
      im[u'type'] = getChoice(i, IM_TYPES)
      i += 1
      if im[u'type'] == u'custom':
        im[u'customType'] = getString(i, OBJECT_STRING)
        i += 1
      getChoice(i, [u'protocol'])
      i += 1
      im[u'protocol'] = getChoice(i, IM_PROTOCOLS)
      i += 1
      if im[u'protocol'] == u'custom_protocol':
        im[u'customProtocol'] = getString(i, OBJECT_STRING)
        i += 1
      im[u'primary'] = getChoice(i, PRIMARY_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True)
      if im[u'primary']:
        i += 1
      im[u'im'] = getString(i, OBJECT_STRING)
      i += 1
      appendItemToBodyList(body, u'ims', im)
    elif my_arg == u'address':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'addresses')
        continue
      address = dict()
      getChoice(i, [u'type'])
      i += 1
      address[u'type'] = getChoice(i, ADDRESS_TYPES)
      i += 1
      if address[u'type'] == u'custom':
        address[u'customType'] = getString(i, OBJECT_STRING)
        i += 1
      if getChoice(i, UNSTRUCTURED_FORMATTED_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        address[u'sourceIsStructured'] = False
        address[u'formatted'] = getString(i, OBJECT_STRING)
        i += 1
      while i < len(sys.argv):
        argument = getArgument(i)
        if argument == u'pobox':
          address[u'poBox'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'extendedaddress':
          address[u'extendedAddress'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'streetaddress':
          address[u'streetAddress'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'locality':
          address[u'locality'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'region':
          address[u'region'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'postalcode':
          address[u'postalCode'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'country':
          address[u'country'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'countrycode':
          address[u'countryCode'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          address[u'primary'] = True
          i += 1
          break
        else:
          unknownArgumentExit(i)
      appendItemToBodyList(body, u'addresses', address)
    elif my_arg == u'organization':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'organizations')
        continue
      organization = dict()
      while i < len(sys.argv):
        argument = getArgument(i)
        if argument == u'name':
          organization[u'name'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'title':
          organization[u'title'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'customtype':
          organization[u'customType'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'type':
          organization[u'type'] = getChoice(i+1, ORGANIZATION_TYPES)
          i += 2
        elif argument == u'department':
          organization[u'department'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'symbol':
          organization[u'symbol'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'costcenter':
          organization[u'costCenter'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'location':
          organization[u'location'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'description':
          organization[u'description'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'domain':
          organization[u'domain'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          organization[u'primary'] = True
          i += 1
          break
        else:
          unknownArgumentExit(i)
      appendItemToBodyList(body, u'organizations', organization)
    elif my_arg == u'phone':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'phones')
        continue
      phone = dict()
      while i < len(sys.argv):
        argument = getArgument(i)
        if argument == u'value':
          phone[u'value'] = getString(i+1, OBJECT_STRING)
          i += 2
        elif argument == u'type':
          phone[u'type'] = getChoice(i+1, PHONE_TYPES)
          i += 2
          if phone[u'type'] == u'custom':
            phone[u'customType'] = getString(i, OBJECT_STRING)
            i += 1
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          phone[u'primary'] = True
          i += 1
          break
        else:
          unknownArgumentExit(i)
      appendItemToBodyList(body, u'phones', phone)
    elif my_arg == u'relation':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'relations')
        continue
      relation = dict()
      relation[u'type'] = getString(i, OBJECT_STRING)
      if relation[u'type'].lower() not in RELATION_TYPES:
        relation[u'customType'] = relation[u'type']
        relation[u'type'] = u'custom'
      else:
        relation[u'type'] = relation[u'type'].lower()
      i += 1
      relation[u'value'] = getString(i, OBJECT_STRING)
      i += 1
      appendItemToBodyList(body, u'relations', relation)
    elif my_arg == u'otheremail':
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'emails')
        continue
      an_email = dict()
      i += 1
      an_email[u'type'] = getString(i, OBJECT_STRING)
      if an_email[u'type'].lower() not in OTHEREMAIL_TYPES:
        an_email[u'customType'] = an_email[u'type']
        an_email[u'type'] = u'custom'
      else:
        an_email[u'type'] = an_email[u'type'].lower()
      i += 1
      an_email[u'address'] = getString(i, OBJECT_STRING)
      i += 1
      appendItemToBodyList(body, u'emails', an_email)
    elif my_arg == u'externalid':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'externalIds')
        continue
      externalid = dict()
      externalid[u'type'] = getString(i, OBJECT_STRING)
      if externalid[u'type'].lower() not in EXTERNALID_TYPES:
        externalid[u'customType'] = externalid[u'type']
        externalid[u'type'] = u'custom'
      else:
        externalid[u'type'] = externalid[u'type'].lower()
      i += 1
      externalid[u'value'] = getString(i, OBJECT_STRING)
      i += 1
      appendItemToBodyList(body, u'externalIds', externalid)
    elif my_arg == u'website':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'websites')
        continue
      website = dict()
      website[u'type'] = getString(i, OBJECT_STRING)
      if website[u'type'].lower() not in WEBSITE_TYPES:
        website[u'customType'] = website[u'type']
        website[u'type'] = u'custom'
      else:
        website[u'type'] = website[u'type'].lower()
      i += 1
      website[u'value'] = getString(i, OBJECT_URL)
      i += 1
      appendItemToBodyList(body, u'websites', website)
    elif my_arg == u'note':
      i += 1
      if getChoice(i, CLEAR_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        clearBodyList(body, u'notes')
        continue
      note = dict()
      note[u'contentType'] = getChoice(i, NOTE_TYPES)
      i += 1
      if getChoice(i, FILE_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
        i += 1
        note[u'value'] = readFile(getString(i, OBJECT_FILE_NAME))
      else:
        note[u'value'] = getString(i, OBJECT_STRING, emptyOK=True).replace(u'\\n', u'\n')
      i += 1
      appendItemToBodyList(body, u'notes', note)
    else:
      body.setdefault(u'customSchemas', {})
      try:
        (schemaName, fieldName) = sys.argv[i].split(u'.')
      except ValueError:
        unknownArgumentExit(i)
      body[u'customSchemas'].setdefault(schemaName, {})
      i += 1
      is_multivalue = getChoice(i, MULTIVALUE_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True)
      if is_multivalue:
        i += 1
        body[u'customSchemas'][schemaName].setdefault(fieldName, [])
        body[u'customSchemas'][schemaName][fieldName].append({u'value': getString(i, OBJECT_STRING)})
      else:
        body[u'customSchemas'][schemaName][fieldName] = getString(i, OBJECT_STRING)
      i += 1
  if need_password:
    body[u'password'] = u''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if u'password' in body and need_to_hash_password:
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  return (body, admin_body)

def doCreateUser():
  cd = buildGAPIObject(u'directory')
  body, admin_body = getUserAttributes(3, updateCmd=False, noUid=True)
  print u"Creating account for %s" % body[u'primaryEmail']
  callGAPI(service=cd.users(), function='insert', body=body, fields=u'primaryEmail')
  if admin_body:
    print u' Changing admin status for %s to %s' % (body[u'primaryEmail'], admin_body[u'status'])
    callGAPI(service=cd.users(), function=u'makeAdmin', userKey=body[u'primaryEmail'], body=admin_body)

def getGroupAttrValue(i, gsDiscoveryObject, attribute, skipAttributes, gs_body):
  value = getString(i, OBJECT_STRING)
  for (attrib, params) in gsDiscoveryObject[u'schemas'][u'Groups'][u'properties'].items():
    if attrib in skipAttributes:
      continue
    if attribute == attrib.lower():
      if params[u'type'] == u'integer':
        try:
          if value[-1:].upper() == u'M':
            value = int(value[:-1]) * ONE_MEGA_BYTES
          elif value[-1:].upper() == u'K':
            value = int(value[:-1]) * ONE_KILO_BYTES
          elif value[-1].upper() == u'B':
            value = int(value[:-1])
          else:
            value = int(value)
        except ValueError:
          invalidArgumentExit(i, u'A number ending with M (megabytes), K (kilobytes), B (bytes) or nothing (bytes)')
      elif params[u'type'] == u'string':
        if params[u'description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
          value = value.upper()
        elif value.lower() in TRUE_VALUES:
          value = TRUE
        elif value.lower() in FALSE_VALUES:
          value = FALSE
      gs_body[attrib] = value
      break
  else:
    unknownArgumentExit(i)

def doCreateGroup():
  cd = buildGAPIObject(u'directory')
  gs_object = None
  use_gs_api = False
  body = {u'email':  getEmailAddress(3, noUid=True)}
  gs_body = dict()
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'name':
      body[u'name'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'description':
      body[u'description'] = getString(i+1, OBJECT_STRING)
      i += 2
    else:
      if not gs_object:
        gs_object = buildDiscoveryObject(u'groupssettings')
      getGroupAttrValue(i+1, gs_object, my_arg, [u'kind', u'etag', u'email', u'name', u'description'], gs_body)
      use_gs_api = True
      i += 2
  body.setdefault(u'name', body[u'email'])
  print u"Creating group %s" % body[u'email']
  callGAPI(service=cd.groups(), function=u'insert', body=body, fields=u'email')
  if use_gs_api:
    gs = buildGAPIObject(u'groupssettings')
    callGAPI(service=gs.groups(), function=u'patch', retry_reasons=[u'serviceLimit'], groupUniqueId=body[u'email'], body=gs_body)

ALIAS_TARGET_TYPE_USER = u'user'
ALIAS_TARGET_TYPE_GROUP = u'group'
ALIAS_TARGET_TYPE_TARGET = u'target'

ALIAS_TARGET_TYPES = [
  ALIAS_TARGET_TYPE_USER,
  ALIAS_TARGET_TYPE_GROUP,
  ALIAS_TARGET_TYPE_TARGET,
  ]

def doCreateAlias():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'alias'] = getEmailAddress(3)
  target_type = getChoice(4, ALIAS_TARGET_TYPES)
  targetKey = getEmailAddress(5)
  print u'Creating alias %s for %s %s' % (body[u'alias'], target_type, targetKey)
  if target_type == ALIAS_TARGET_TYPE_USER:
    callGAPI(service=cd.users().aliases(), function=u'insert', userKey=targetKey, body=body)
  elif target_type == ALIAS_TARGET_TYPE_GROUP:
    callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=targetKey, body=body)
  elif target_type == ALIAS_TARGET_TYPE_TARGET:
    try:
      callGAPI(service=cd.users().aliases(), function=u'insert', throw_reasons=[u'invalid'], userKey=targetKey, body=body)
    except googleapiclient.errors.HttpError:
      callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=targetKey, body=body)

def doCreateOrg():
  cd = buildGAPIObject(u'directory')
  name = getOrgUnitPath(3, absolutePath=False)
  parent = u''
  body = {}
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'description':
      body[u'description'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'parent':
      parent = getOrgUnitPath(i+1)
      i += 2
    elif my_arg == u'noinherit':
      body[u'blockInheritance'] = True
      i += 1
    else:
      unknownArgumentExit(i)
  if parent.endswith(u'/'):
    parent = parent[:-1]
  orgUnitPath = u'/'.join([parent, name])
  if orgUnitPath.count(u'/') > 1:
    body[u'parentOrgUnitPath'], body[u'name'] = orgUnitPath.rsplit(u'/', 1)
  else:
    body[u'parentOrgUnitPath'] = u'/'
    body[u'name'] = orgUnitPath[1:]
  callGAPI(service=cd.orgunits(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)

def doCreateResource():
  rescal = getResCalObject()
  resId = getString(3, OBJECT_RESOURCE_ID)
  common_name = getString(4, OBJECT_NAME)
  description = None
  resType = None
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'description':
      description = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'restype':
      resType = getString(i+1, OBJECT_STRING)
      i += 2
    else:
      unknownArgumentExit(i)
  callGData(service=rescal, function=u'CreateResourceCalendar', id=resId, common_name=common_name, description=description, type=resType)

def doUpdateSingleUser():
  cd = buildGAPIObject(u'directory')
  doUpdateUser([getEmailAddress(3),], cd=cd, i=4)

def doUpdateUser(users, cd=None, i=5):
  if not cd:
    cd = buildGAPIObject(u'directory')
  body, admin_body = getUserAttributes(i, updateCmd=True)
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    if u'primaryEmail' in body and body[u'primaryEmail'][:4].lower() == u'vfe@':
      user_primary = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'primaryEmail,id')
      user = user_primary[u'id']
      user_primary = user_primary[u'primaryEmail']
      user_name, user_domain = splitEmailAddress(user_primary)
      body[u'primaryEmail'] = u'vfe.%s.%05d@%s' % (user_name, random.randint(1, 99999), user_domain)
      body[u'emails'] = [{u'type': u'custom', u'customType': u'former_employee', u'primary': False, u'address': user_primary}]
    sys.stdout.write(u'updating user %s...\n' % user)
    if body:
      callGAPI(service=cd.users(), function=u'update', userKey=user, body=body)
    if admin_body:
      callGAPI(service=cd.users(), function=u'makeAdmin', userKey=user, body=admin_body)

def doRemoveUsersAliases(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user = normalizeEmailAddressOrUID(user)
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
    user = normalizeEmailAddressOrUID(user)
    user_groups = callGAPIpages(service=cd.groups(), items=u'groups', function=u'list', userKey=user, fields=u'groups(id,email)')
    num_groups = len(user_groups)
    print u'%s is in %s groups' % (user, num_groups)
    i = 1
    for user_group in user_groups:
      print u' removing %s from %s (%s/%s)' % (user, user_group[u'email'], i, num_groups)
      callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=user_group[u'id'], memberKey=user)
      i += 1
    print u''

UPDATE_GROUP_CMD_ADD = u'add'
UPDATE_GROUP_CMD_CLEAR = u'clear'
UPDATE_GROUP_CMD_UPDATE = u'update'
UPDATE_GROUP_CMD_SYNC = u'sync'
UPDATE_GROUP_CMD_REMOVE = u'remove'
UPDATE_GROUP_SUBCMDS = [
  UPDATE_GROUP_CMD_ADD,
  UPDATE_GROUP_CMD_CLEAR,
  UPDATE_GROUP_CMD_UPDATE,
  UPDATE_GROUP_CMD_SYNC,
  UPDATE_GROUP_CMD_REMOVE,
  ]

UPDATE_GROUP_ROLE_CHOICES_MAP = {
  u'owner': ROLE_OWNER,
  u'owners': ROLE_OWNER,
  u'manager': ROLE_MANAGER,
  u'managers': ROLE_MANAGER,
  u'member': ROLE_MEMBER,
  u'members': ROLE_MEMBER,
  }

def doUpdateGroup():
  cd = buildGAPIObject(u'directory')
  gs_object = None
  group = getEmailAddress(3)
  my_arg = getChoice(4, UPDATE_GROUP_SUBCMDS, defaultChoice=None)
  if not my_arg:
    use_cd_api = False
    use_gs_api = False
    gs_body = dict()
    cd_body = dict()
    i = 4
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg == u'email':
        use_cd_api = True
        cd_body[u'email'] = getEmailAddress(i+1, noUid=True)
        i += 2
      elif my_arg == u'admincreated':
        use_cd_api = True
        cd_body[u'adminCreated'] = getBoolean(i+1)
        i += 2
      else:
        if not gs_object:
          gs_object = buildDiscoveryObject(u'groupssettings')
        getGroupAttrValue(i+1, gs_object, my_arg, [u'kind', u'etag', u'email'], gs_body)
        use_gs_api = True
        i += 2
    if group.find(u'@') == -1: # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
      use_cd_api = True
    if use_cd_api:
      cd_result = callGAPI(service=cd.groups(), function=u'update', groupKey=group, body=cd_body)
      group = cd_result[u'email']
    if use_gs_api:
      gs = buildGAPIObject(u'groupssettings')
      callGAPI(service=gs.groups(), function=u'patch', retry_reasons=[u'serviceLimit'], groupUniqueId=group, body=gs_body)
    print u'updated group %s' % group
  elif my_arg == UPDATE_GROUP_CMD_ADD:
    i = 5
    role = getChoice(i, UPDATE_GROUP_ROLE_CHOICES_MAP, defaultChoice=None, mapChoice=True)
    if role:
      i += 1
    else:
      role = ROLE_MEMBER
    _, addMembers = getEntityToModify(i, defaultEntityType=CL_ENTITY_USERS)
    for member in addMembers:
      sys.stderr.write(u' adding %s %s...' % (role.lower(), member))
      try:
        member = normalizeEmailAddressOrUID(member)
        if member.find(u'@') != -1:
          body = {u'role': role, u'email': member}
        else:
          body = {u'role': role, u'id': member}
        result = callGAPI(service=cd.members(), function=u'insert', soft_errors=True, groupKey=group, body=body)
        try:
          if str(result[u'email']).lower() != member.lower():
            print u'added %s (primary address) to group' % result[u'email']
          else:
            print u'added %s to group' % result[u'email']
        except TypeError:
          pass
      except googleapiclient.errors.HttpError:
        pass
  elif my_arg == UPDATE_GROUP_CMD_SYNC:
    i = 5
    role = getChoice(i, UPDATE_GROUP_ROLE_CHOICES_MAP, defaultChoice=None, mapChoice=True)
    if role:
      i += 1
    else:
      role = ROLE_MEMBER
    _, syncMembers = getEntityToModify(i, defaultEntityType=CL_ENTITY_USERS)
    syncMembersSet = set()
    for member in syncMembers:
      syncMembersSet.add(normalizeEmailAddressOrUID(member))
    currentMembersSet = set(getUsersToModify(CL_ENTITY_GROUP, group, memberRole=role))
    addMembers = list(syncMembersSet-currentMembersSet)
    removeMembers = list(currentMembersSet-syncMembersSet)
    for member in addMembers:
      sys.stderr.write(u' adding %s %s\n' % (role, member))
      try:
        result = callGAPI(service=cd.members(), function=u'insert', soft_errors=True, throw_reasons=[u'duplicate'], groupKey=group, body={u'email': member, u'role': role})
      except googleapiclient.errors.HttpError:
        result = callGAPI(service=cd.members(), function=u'update', soft_errors=True, groupKey=group, memberKey=member, body={u'email': member, u'role': role})
    for member in removeMembers:
      sys.stderr.write(u' removing %s\n' % member)
      result = callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=group, memberKey=member)
  elif my_arg == UPDATE_GROUP_CMD_REMOVE:
    i = 5
    role = getChoice(i, UPDATE_GROUP_ROLE_CHOICES_MAP, defaultChoice=None, mapChoice=True)
    if role:
      i += 1
    _, removeMembers = getEntityToModify(i, defaultEntityType=CL_ENTITY_USERS)
    for member in removeMembers:
      member = normalizeEmailAddressOrUID(member)
      sys.stderr.write(u' removing %s\n' % member)
      result = callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=group, memberKey=member)
  elif my_arg == UPDATE_GROUP_CMD_CLEAR:
    roles = []
    i = 5
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg in UPDATE_GROUP_ROLE_CHOICES_MAP:
        roles.append(UPDATE_GROUP_ROLE_CHOICES_MAP[my_arg])
        i += 1
      else:
        invalidChoiceExit(i, UPDATE_GROUP_ROLE_CHOICES_MAP)
    if not roles:
      roles.append(ROLE_MEMBER)
    roles = u','.join(sorted(set(roles)))
    removeMembers = getUsersToModify(CL_ENTITY_GROUP, group, memberRole=roles)
    for member in removeMembers:
      sys.stderr.write(u' removing %s\n' % member)
      result = callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=group, memberKey=member)
  elif my_arg == UPDATE_GROUP_CMD_UPDATE:
    i = 5
    role = getChoice(i, UPDATE_GROUP_ROLE_CHOICES_MAP, defaultChoice=None, mapChoice=True)
    if role:
      i += 1
    else:
      role = ROLE_MEMBER
    body = {u'role': role}
    _, updateMembers = getEntityToModify(i, defaultEntityType=CL_ENTITY_USERS)
    for member in updateMembers:
      member = normalizeEmailAddressOrUID(member)
      sys.stderr.write(u' updating %s %s...' % (role.lower(), member))
      try:
        result = callGAPI(service=cd.members(), function=u'update', soft_errors=True, groupKey=group, memberKey=member, body=body)
        try:
          if str(result[u'email']).lower() != member.lower():
            print u'added %s (primary address) to group' % result[u'email']
          else:
            print u'added %s to group' % result[u'email']
        except TypeError:
          pass
      except googleapiclient.errors.HttpError:
        pass

def doUpdateAlias():
  cd = buildGAPIObject(u'directory')
  alias = getEmailAddress(3)
  target_type = getChoice(4, ALIAS_TARGET_TYPES)
  target_email = getEmailAddress(5)
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
  rescal = getResCalObject()
  resId = getString(3, OBJECT_RESOURCE_ID)
  common_name = None
  description = None
  resType = None
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'name':
      common_name = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'description':
      description = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'type':
      resType = getString(i+1, OBJECT_STRING)
      i += 2
    else:
      unknownArgumentExit(i)
  callGData(service=rescal, function=u'UpdateResourceCalendar', id=resId, common_name=common_name, description=description, type=resType)
  print u'updated resource %s' % resId

CROS_STATUS_CHOICES_MAP = {
  u'active': u'ACTIVE',
  u'deprovisioned': u'DEPROVISIONED',
  u'inactive': u'INACTIVE',
  u'returnapproved': u'RETURN_APPROVED',
  u'returnrequested': u'RETURN_REQUESTED',
  u'shipped': u'SHIPPED',
  u'unknown': u'UNKNOWN',
  }

def doUpdateSingleCros():
  cd = buildGAPIObject(u'directory')
  deviceId = getString(3, OBJECT_CROS_DEVICE_ENTITY)
  if deviceId[:6].lower() == u'query:':
    query = deviceId[6:]
    devices_result = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices', query=query, customerId=GC_Values[GC_CUSTOMER_ID], fields=u'chromeosdevices/deviceId,nextPageToken')
    devices = list()
    for a_device in devices_result:
      devices.append(a_device[u'deviceId'])
  else:
    devices = [deviceId,]
  doUpdateCros(devices, cd=cd)

def doUpdateCros(devices, cd=None):
  if not cd:
    cd = buildGAPIObject(u'directory')
  body = dict()
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'user':
      body[u'annotatedUser'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'location':
      body[u'annotatedLocation'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'notes':
      body[u'notes'] = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'status':
      body[u'status'] = getChoice(i+1, CROS_STATUS_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg in [u'tag', u'asset', u'assetid']:
      body[u'annotatedAssetId'] = getString(i+1, OBJECT_STRING)
      #annotatedAssetId - Handle Asset Tag Field 2015-04-13
      i += 2
    elif my_arg in [u'ou', u'org']:
      body[u'orgUnitPath'] = getOrgUnitPath(i+1)
      i += 2
    else:
      unknownArgumentExit(i)
  device_count = len(devices)
  i = 1
  for this_device in devices:
    print u' updating %s (%s of %s)' % (this_device, i, device_count)
    callGAPI(service=cd.chromeosdevices(), function=u'patch', deviceId=this_device, body=body, customerId=GC_Values[GC_CUSTOMER_ID])
    i += 1

MOBILE_ACTION_CHOICE_MAP = {
  u'accountwipe': u'admin_account_wipe',
  u'adminaccountwipe': u'admin_account_wipe',
  u'wipeaccount': u'admin_account_wipe',
  u'adminremotewipe': u'admin_remote_wipe',
  u'wipe': u'admin_remote_wipe',
  u'approve': u'approve',
  u'block': u'action_block',
  u'cancelremotewipethenactivate': u'cancel_remote_wipe_then_activate',
  u'cancelremotewipethenblock': u'cancel_remote_wipe_then_block',
  }

def doUpdateMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = getString(3, OBJECT_MOBILE_DEVICE_ENTITY)
  action_body = patch_body = dict()
  doPatch = doAction = False
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'action':
      action_body[u'action'] = getChoice(i+1, MOBILE_ACTION_CHOICE_MAP, mapChoice=True)
      doAction = True
      i += 2
    elif my_arg == u'model':
      patch_body[u'model'] = getString(i+1, OBJECT_STRING)
      i += 2
      doPatch = True
    elif my_arg == u'os':
      patch_body[u'os'] = getString(i+1, OBJECT_STRING)
      i += 2
      doPatch = True
    elif my_arg == u'useragent':
      patch_body[u'userAgent'] = getString(i+1, OBJECT_STRING)
      i += 2
      doPatch = True
    else:
      unknownArgumentExit(i)
  if doPatch:
    callGAPI(service=cd.mobiledevices(), function=u'patch', resourceId=resourceId, body=patch_body, customerId=GC_Values[GC_CUSTOMER_ID])
  if doAction:
    callGAPI(service=cd.mobiledevices(), function=u'action', resourceId=resourceId, body=action_body, customerId=GC_Values[GC_CUSTOMER_ID])

def doDeleteMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = getString(3, OBJECT_MOBILE_DEVICE_ENTITY)
  callGAPI(service=cd.mobiledevices(), function='delete', resourceId=resourceId, customerId=GC_Values[GC_CUSTOMER_ID])

def doUpdateOrg():
  cd = buildGAPIObject(u'directory')
  orgUnitPath = getOrgUnitPath(3)
  if getChoice(4, MOVE_ADD_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    entityType, items = getEntityToModify(5, defaultEntityType=CL_ENTITY_USERS, crosAllowed=True)
    i = 0
    count = len(items)
    if entityType == CL_ENTITY_CROS:
      for cros in items:
        i += 1
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (cros, orgUnitPath, i, count))
        callGAPI(service=cd.chromeosdevices(), function=u'update', soft_errors=True, customerId=GC_Values[GC_CUSTOMER_ID], deviceId=cros, body={u'orgUnitPath': orgUnitPath})
    else:
      for user in items:
        i += 1
        user = normalizeEmailAddressOrUID(user)
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (user, orgUnitPath, i, count))
        try:
          callGAPI(service=cd.users(), function=u'update', throw_reasons=[u'conditionNotMet'], userKey=user, body={u'orgUnitPath': orgUnitPath})
        except googleapiclient.errors.HttpError:
          pass
  else:
    body = dict()
    i = 4
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg == u'name':
        body[u'name'] = getString(i+1, OBJECT_STRING)
        i += 2
      elif my_arg == u'description':
        body[u'description'] = getString(i+1, OBJECT_STRING)
        i += 2
      elif my_arg == u'parent':
        parent = getOrgUnitPath(i+1)
        if parent.startswith(u'id:'):
          body[u'parentOrgUnitId'] = parent
        else:
          body[u'parentOrgUnitPath'] = parent
        i += 2
      elif my_arg == u'noinherit':
        body[u'blockInheritance'] = True
        i += 1
      elif my_arg == u'inherit':
        body[u'blockInheritance'] = False
        i += 1
      else:
        unknownArgumentExit(i)
    callGAPI(service=cd.orgunits(), function=u'update',
             customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(orgUnitPath), body=body)

def doWhatIs():
  cd = buildGAPIObject(u'directory')
  email = getEmailAddress(2)
  show_info = not getChoice(3, NOINFO_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True)
  try:
    result = callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'notFound', u'badRequest', u'invalid'],
                      userKey=email, fields=u'primaryEmail,id')
    if (result[u'primaryEmail'].lower() == email) or (result[u'id'] == email):
      sys.stderr.write(u'%s is a user\n\n' % email)
      if show_info:
        doGetUserInfo(user_email=email)
      return
    else:
      sys.stderr.write(u'%s is a user alias\n\n' % email)
      if show_info:
        doGetAliasInfo(alias_email=email)
      return
  except googleapiclient.errors.HttpError:
    sys.stderr.write(u'%s is not a user...\n' % email)
    sys.stderr.write(u'%s is not a user alias...\n' % email)
  try:
    result = callGAPI(service=cd.groups(), function=u'get', throw_reasons=[u'notFound', u'badRequest'], groupKey=email, fields=u'email,id')
  except googleapiclient.errors.HttpError:
    sys.stderr.write(u'%s is not a group either!\n\nDoesn\'t seem to exist!\n\n' % email)
    sys.exit(1)
  if (result[u'email'].lower() == email) or (result[u'id'] == email):
    sys.stderr.write(u'%s is a group\n\n' % email)
    if show_info:
      doGetGroupInfo(group_name=email)
  else:
    sys.stderr.write(u'%s is a group alias\n\n' % email)
    if show_info:
      doGetAliasInfo(alias_email=email)

USER_PROJECTION_BASIC = u'basic'
USER_PROJECTION_CUSTOM = u'custom'
USER_PROJECTION_FULL = u'full'

def doGetUserInfo(user_email=None):
  cd = buildGAPIObject(u'directory')
  if user_email == None:
    user_email = getEmailAddress(3, optional=True)
    if not user_email:
      storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
      credentials = storage.get()
      if credentials is None or credentials.invalid:
        doRequestOAuth()
        credentials = storage.get()
      user_email = credentials.id_token[u'email']
  getSchemas = getAliases = getGroups = getLicenses = True
  projection = USER_PROJECTION_FULL
  customFieldMask = viewType = None
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'noaliases':
      getAliases = False
      i += 1
    elif my_arg == u'nogroups':
      getGroups = False
      i += 1
    elif my_arg in [u'nolicenses', u'nolicences']:
      getLicenses = False
      i += 1
    elif my_arg == u'noschemas':
      getSchemas = False
      projection = USER_PROJECTION_BASIC
      i += 1
    elif my_arg == u'schemas':
      getSchemas = True
      projection = USER_PROJECTION_CUSTOM
      customFieldMask = getString(i+1, OBJECT_SCHEMA_NAME_LIST)
      i += 2
    elif my_arg == u'userview':
      viewType = u'domain_public'
      getGroups = getLicenses = False
      i += 1
    else:
      unknownArgumentExit(i)
  user = callGAPI(service=cd.users(), function=u'get', userKey=user_email, projection=projection, customFieldMask=customFieldMask, viewType=viewType)
  print u'User: %s' % user[u'primaryEmail']
  if u'name' in user and u'givenName' in user[u'name']:
    print convertUTF8(u'First Name: %s' % user[u'name'][u'givenName'])
  if u'name' in user and u'familyName' in user[u'name']:
    print convertUTF8(u'Last Name: %s' % user[u'name'][u'familyName'])
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
    if user[u'lastLoginTime'] == NEVER_TIME:
      print u'Last login time: %s' % NEVER
    else:
      print u'Last login time: %s' % user[u'lastLoginTime']
  if u'orgUnitPath' in user:
    print u'Google Org Unit Path: %s\n' % user[u'orgUnitPath']
  if u'thumbnailPhotoUrl' in user:
    print u'Photo URL: %s\n' % user[u'thumbnailPhotoUrl']
  if u'ims' in user:
    print u'IMs:'
    for im in user[u'ims']:
      for key in im:
        print u' %s: %s' % (key, im[key])
      print u''
  if u'addresses' in user:
    print u'Addresses:'
    for address in user[u'addresses']:
      for key in address:
        print convertUTF8(u' %s: %s' % (key, address[key]))
      print ''
  if u'organizations' in user:
    print u'Organizations:'
    for org in user[u'organizations']:
      for key in org:
        if key == u'customType' and not org[key]:
          continue
        print convertUTF8(u' %s: %s' % (key, org[key]))
      print u''
  if u'phones' in user:
    print u'Phones:'
    for phone in user[u'phones']:
      for key in phone:
        print u' %s: %s' % (key, phone[key])
      print u''
  if u'emails' in user:
    if len(user[u'emails']) > 1:
      print u'Other Emails:'
      for an_email in user[u'emails']:
        if an_email[u'address'].lower() == user[u'primaryEmail'].lower():
          continue
        if (u'type' not in an_email) and (u'customType' not in an_email):
          if not getAliases:
            continue
          print u' type: alias'
        for key in an_email:
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
      for key in relation:
        if key == u'type' and relation[key] == u'custom':
          continue
        elif key == u'customType':
          print convertUTF8(u' %s: %s' % (u'type', relation[key]))
        else:
          print convertUTF8(u' %s: %s' % (key, relation[key]))
      print u''
  if u'externalIds' in user:
    print u'External IDs:'
    for externalId in user[u'externalIds']:
      for key in externalId:
        if key == u'type' and externalId[key] == u'custom':
          continue
        elif key == u'customType':
          print convertUTF8(u' %s: %s' % (u'type', externalId[key]))
        else:
          print convertUTF8(u' %s: %s' % (key, externalId[key]))
      print u''
  if u'websites' in user:
    print u'Websites:'
    for website in user[u'websites']:
      for key in website:
        if key == u'type' and website[key] == u'custom':
          continue
        elif key == u'customType':
          print u' %s: %s' % (u'type', website[key])
        else:
          print u' %s: %s' % (key, website[key])
      print u''
  if u'notes' in user:
    note = user[u'notes']
    if len(note) > 0:
      print u'Notes:'
      if isinstance(note, dict):
        if (u'contentType' in note) and (note[u'contentType'] == u'text_html'):
          print u'  %s: %s' % (note[u'type'])
          print u'  %s' % (dehtml(note[u'value']).replace(u'\n', u'\n  '))
        else:
          print convertUTF8(u'  %s' % (note[u'value'].replace(u'\n', u'\n  ')))
      else:
        print convertUTF8(u'  %s' % (note.replace(u'\n', u'\n  ')))
      print u''
  if getSchemas:
    if u'customSchemas' in user:
      print u'Custom Schemas:'
      for schema in user[u'customSchemas']:
        print u' Schema: %s' % schema
        for field in user[u'customSchemas'][schema]:
          if isinstance(user[u'customSchemas'][schema][field], list):
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
    groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups',
                           userKey=user_email, fields=u'groups(name,email),nextPageToken')
    if groups and len(groups) > 0:
      print u'Groups: (%s)' % len(groups)
      for group in groups:
        print u'   %s <%s>' % (group[u'name'], group[u'email'])
  if getLicenses:
    print u'Licenses:'
    lic = buildGAPIObject(api='licensing')
    for skuId in sorted(GOOGLE_SKUS):
      try:
        result = callGAPI(service=lic.licenseAssignments(), function=u'get', throw_reasons=['notFound'],
                          userId=user_email, productId=GOOGLE_SKUS[skuId], skuId=skuId)
      except googleapiclient.errors.HttpError:
        continue
      print u' %s' % result[u'skuId']

def doGetGroupInfo(group_name=None):
  cd = buildGAPIObject(u'directory')
  if group_name == None:
    group_name = getEmailAddress(3)
  get_users = True
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'nousers':
      get_users = False
      i += 1
    else:
      unknownArgumentExit(i)
  gs = buildGAPIObject(u'groupssettings')
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
    if isinstance(value, list):
      print u' %s:' % key
      for val in value:
        print u'  %s' % val
    else:
      print convertUTF8(u' %s: %s' % (key, value))
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
  cd = buildGAPIObject(u'directory')
  if alias_email == None:
    alias_email = getEmailAddress(3)
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
  rescal = getResCalObject()
  resId = getString(3, OBJECT_RESOURCE_ID)
  result = callGData(service=rescal, function=u'RetrieveResourceCalendar', id=resId)
  print u' Resource ID: '+result[u'resourceId']
  print u' Common Name: '+result[u'resourceCommonName']
  print u' Email: '+result[u'resourceEmail']
  print u' Type: '+result.get(u'resourceType', u'')
  print u' Description: '+result.get(u'resourceDescription', u'')

def doGetCrosInfo():
  cd = buildGAPIObject(u'directory')
  deviceId = getString(3, OBJECT_CROS_DEVICE_ENTITY)
  info = callGAPI(service=cd.chromeosdevices(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId)
  print_json(None, info)

def doGetMobileInfo():
  deviceId = getString(3, OBJECT_MOBILE_DEVICE_ENTITY)
  cd = buildGAPIObject(u'directory')
  try:
    info = callGAPI(service=cd.mobiledevices(), function=u'get', throw_reasons=[u'internalError'], customerId=GC_Values[GC_CUSTOMER_ID], resourceId=deviceId)
    print_json(None, info)
  except:
    sys.stderr.write(u'{0}Resource Not Found: {1} - notFound\n'.format(ERROR_PREFIX, deviceId))

def print_json(object_name, object_value, spacing=u''):
  if object_name in [u'kind', u'etag', u'etags']:
    return
  if object_name != None:
    sys.stdout.write(u'%s%s: ' % (spacing, object_name))
  if isinstance(object_value, list):
    if len(object_value) == 1 and isinstance(object_value[0], (str, unicode, int, bool)):
      sys.stdout.write(u'%s\n' % object_value[0])
      return
    sys.stdout.write(u'\n')
    for a_value in object_value:
      if isinstance(a_value, (str, unicode, int, bool)):
        print u' %s%s' % (spacing, a_value)
      else:
        print_json(object_name=None, object_value=a_value, spacing=u' %s' % spacing)
  elif isinstance(object_value, dict):
    for another_object in object_value:
      print_json(object_name=another_object, object_value=object_value[another_object], spacing=spacing)
  else:
    sys.stdout.write(u'%s\n' % (object_value))

def doUpdateNotification():
  cd = buildGAPIObject(u'directory')
  ids = list()
  get_all = False
  isUnread = None
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'unread':
      isUnread = True
      mark_as = u'unread'
      i += 1
    elif my_arg == u'read':
      isUnread = False
      mark_as = u'read'
      i += 1
    elif my_arg == u'id':
      notificationId = getString(i+1, OBJECT_NOTIFICATION_ID)
      if notificationId.lower() == u'all':
        get_all = True
      else:
        ids.append(notificationId)
      i += 2
    else:
      unknownArgumentExit(i)
  if isUnread == None:
    missingChoiceExit(i, [u'unread', u'read'])
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
    my_arg = getArgument(i)
    if my_arg == u'id':
      notificationId = getString(i+1, OBJECT_NOTIFICATION_ID)
      if notificationId.lower() == u'all':
        get_all = True
      else:
        ids.append(notificationId)
      i += 2
    else:
      unknownArgumentExit(i)
  if get_all:
    notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId),nextPageToken')
    for noti in notifications:
      ids.append(noti[u'notificationId'])
  print u'Deleting %s notification(s)...' % len(ids)
  for notificationId in ids:
    callGAPI(service=cd.notifications(), function=u'delete', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId)
    print u'deleted %s' % id

SITEVERIFICATION_SITE_TYPE_INET_DOMAIN = u'INET_DOMAIN'
SITEVERIFICATION_SITE_TYPE_SITE = u'SITE'

SITEVERIFICATION_VERIFICATION_METHOD_DNS_CNAME = u'DNS_CNAME'
SITEVERIFICATION_VERIFICATION_METHOD_DNS_TXT = u'DNS_TXT'
SITEVERIFICATION_VERIFICATION_METHOD_FILE = u'FILE'
SITEVERIFICATION_VERIFICATION_METHOD_META = u'META'

SITEVERIFICATION_METHOD_CHOICES_MAP = {
  u'cname': SITEVERIFICATION_VERIFICATION_METHOD_DNS_CNAME,
  u'txt': SITEVERIFICATION_VERIFICATION_METHOD_DNS_TXT,
  u'text': SITEVERIFICATION_VERIFICATION_METHOD_DNS_TXT,
  u'file': SITEVERIFICATION_VERIFICATION_METHOD_FILE,
  u'site': SITEVERIFICATION_VERIFICATION_METHOD_FILE,
  }

def doSiteVerifyShow():
  verif = buildGAPIObject(u'siteVerification')
  a_domain = getString(3, OBJECT_DOMAIN_NAME)
  txt_record = callGAPI(service=verif.webResource(), function=u'getToken',
                        body={u'site': {u'type': SITEVERIFICATION_SITE_TYPE_INET_DOMAIN, u'identifier': a_domain},
                              u'verificationMethod': SITEVERIFICATION_VERIFICATION_METHOD_DNS_TXT})
  print u'TXT Record Name:   %s' % a_domain
  print u'TXT Record Value:  %s' % txt_record[u'token']
  print
  cname_record = callGAPI(service=verif.webResource(), function=u'getToken',
                          body={u'site': {u'type': SITEVERIFICATION_SITE_TYPE_INET_DOMAIN, u'identifier': a_domain},
                                u'verificationMethod': SITEVERIFICATION_VERIFICATION_METHOD_DNS_CNAME})
  cname_token = cname_record[u'token']
  cname_list = cname_token.split(u' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  print u'CNAME Record Name:   %s.%s' % (cname_subdomain, a_domain)
  print u'CNAME Record Value:  %s' % cname_value
  print u''
  webserver_file_record = callGAPI(service=verif.webResource(), function=u'getToken',
                                   body={u'site': {u'type': SITEVERIFICATION_SITE_TYPE_SITE, u'identifier':u'http://%s/' % a_domain},
                                         u'verificationMethod': SITEVERIFICATION_VERIFICATION_METHOD_FILE})
  webserver_file_token = webserver_file_record[u'token']
  print u'Saving web server verification file to: %s' % webserver_file_token
  writeFile(webserver_file_token, u'google-site-verification: {0}'.format(webserver_file_token), continueOnError=True)
  print u'Verification File URL: http://%s/%s' % (a_domain, webserver_file_token)
  print
  webserver_meta_record = callGAPI(service=verif.webResource(), function=u'getToken',
                                   body={u'site': {u'type': SITEVERIFICATION_SITE_TYPE_SITE, u'identifier':u'http://%s/' % a_domain},
                                         u'verificationMethod': SITEVERIFICATION_VERIFICATION_METHOD_META})
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
  a_domain = getString(3, OBJECT_DOMAIN_NAME)
  verificationMethod = getChoice(4, SITEVERIFICATION_METHOD_CHOICES_MAP, mapChoice=True)
  if verificationMethod in [SITEVERIFICATION_VERIFICATION_METHOD_DNS_TXT, SITEVERIFICATION_VERIFICATION_METHOD_DNS_CNAME]:
    verify_type = SITEVERIFICATION_SITE_TYPE_INET_DOMAIN
    identifier = a_domain
  else:
    verify_type = SITEVERIFICATION_SITE_TYPE_SITE
    identifier = u'http://{0}/'.format(a_domain)
  body = {u'site': {u'type': verify_type, u'identifier': identifier},
          u'verificationMethod':verificationMethod}
  try:
    verify_result = callGAPI(service=verif.webResource(), function=u'insert', throw_reasons=[u'badRequest'], verificationMethod=verificationMethod, body=body)
  except googleapiclient.errors.HttpError, e:
    error = json.loads(e.content)
    message = error[u'error'][u'errors'][0][u'message']
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, message))
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
          print u'{0}No such domain found in DNS!'.format(ERROR_PREFIX)
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
          print u'{0}No such domain found in DNS!'.format(ERROR_PREFIX)
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
  unread_only = False
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'unreadonly':
      unread_only = True
      i += 1
    else:
      unknownArgumentExit(i)
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

ORGANIZATION_QUERY_TYPE_ALL = u'all'
ORGANIZATION_QUERY_TYPE_CHILDREN = u'children'

def doGetOrgInfo():
  cd = buildGAPIObject(u'directory')
  orgUnitPath = getOrgUnitPath(3)
  get_users = True
  show_children = False
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'nousers':
      get_users = False
      i += 1
    elif my_arg in [u'children', u'child']:
      show_children = True
      i += 1
    else:
      unknownArgumentExit(i)
  if orgUnitPath == u'/':
    orgs = callGAPI(service=cd.orgunits(), function=u'list',
                    customerId=GC_Values[GC_CUSTOMER_ID], type=ORGANIZATION_QUERY_TYPE_CHILDREN,
                    fields=u'organizationUnits/parentOrgUnitId')
    orgUnitPath = orgs[u'organizationUnits'][0][u'parentOrgUnitId']
  else:
    orgUnitPath = makeOrgUnitPathRelative(orgUnitPath)
  result = callGAPI(service=cd.orgunits(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath)
  print_json(None, result)
  if get_users:
    orgUnitPath = result[u'orgUnitPath']
    print u'Users: '
    page_message = getPageMessage(u'users', showFirstLastItems=True)
    users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                          message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=orgUnitPathQuery(orgUnitPath),
                          maxResults=500, fields=u'users(primaryEmail,orgUnitPath),nextPageToken')
    for user in users:
      if show_children or (orgUnitPath == user[u'orgUnitPath'].lower()):
        sys.stdout.write(u' %s' % user[u'primaryEmail'])
        if orgUnitPath.lower() != user[u'orgUnitPath'].lower():
          print u' (child)'
        else:
          print u''

def doGetASPs(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    asps = callGAPI(service=cd.asps(), function=u'list', userKey=user)
    print u'Application-Specific Passwords for %s' % user
    try:
      for asp in asps[u'items']:
        if asp[u'creationTime'] == u'0':
          created_date = u'Unknown'
        else:
          created_date = datetime.datetime.fromtimestamp(int(asp[u'creationTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        if asp[u'lastTimeUsed'] == u'0':
          used_date = NEVER
        else:
          used_date = datetime.datetime.fromtimestamp(int(asp[u'lastTimeUsed'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        print u' ID: %s\n  Name: %s\n  Created: %s\n  Last Used: %s\n' % (asp[u'codeId'], asp[u'name'], created_date, used_date)
    except KeyError:
      print u' no ASPs for %s\n' % user

def doDelASP(users):
  cd = buildGAPIObject(u'directory')
  codeId = getString(5, OBJECT_ASP_ID)
  for user in users:
    user = normalizeEmailAddressOrUID(user)
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
    user = normalizeEmailAddressOrUID(user)
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
    user = normalizeEmailAddressOrUID(user)
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
    my_arg = getArgument(i)
    if my_arg == u'clientid':
      clientId = getString(i+1, OBJECT_CLIENT_ID)
      i += 2
    else:
      unknownArgumentExit(i)
  if clientId:
    clientId = commonClientIds(clientId)
    for user in users:
      user = normalizeEmailAddressOrUID(user)
      try:
        token = callGAPI(service=cd.tokens(), function=u'get', throw_reasons=[u'notFound',], userKey=user, clientId=clientId, fields=u'clientId')
      except googleapiclient.errors.HttpError:
        continue
      print u'%s has allowed this token' % user
    return
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    tokens = callGAPI(service=cd.tokens(), function=u'list', userKey=user)
    print u'Tokens for %s:' % user
    try:
      for token in tokens[u'items']:
        print u' Client ID: %s' % token[u'clientId']
        for item in token:
          if item in [u'etag', u'kind', u'clientId']:
            continue
          if isinstance(token[item], list):
            print u' %s:' % item
            for it in token[item]:
              print u'  %s' % it
          elif isinstance(token[item], (unicode, bool)):
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
  clientId = getString(6, OBJECT_CLIENT_ID)
  clientId = commonClientIds(clientId)
  for user in users:
    user = normalizeEmailAddressOrUID(user)
    callGAPI(service=cd.tokens(), function=u'delete', userKey=user, clientId=clientId)
    print u'Deleted token for %s' % user

def doDeprovUser(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user = normalizeEmailAddressOrUID(user)
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

ADMINSETTINGS_EMAIL_ACCOUNT_HANDLING_CHOICES_MAP = {
  u'allaccounts': u'allAccounts',
  u'provisionedaccounts': u'provisionedAccounts',
  u'unknownaccounts': u'unknownAccounts',
  }
OUTBOUND_GATEWAY_MODE_CHOICES_MAP = {
  u'smtp': u'SMTP',
  u'smtp_tls': u'SMTP_TLS',
}

def doUpdateDomain():
  adminObj = getAdminSettingsObject()
  command = getArgument(3)
  if command == u'language':
    language = getChoice(4, LANGUAGE_CODES_MAP, mapChoice=True)
    callGData(service=adminObj, function=u'UpdateDefaultLanguage', defaultLanguage=language)
  elif command == u'name':
    name = getString(4, OBJECT_NAME)
    callGData(service=adminObj, function=u'UpdateOrganizationName', organizationName=name)
  elif command == u'admin_secondary_email':
    admin_secondary_email = getEmailAddress(4, noUid=True)
    callGData(service=adminObj, function=u'UpdateAdminSecondaryEmail', adminSecondaryEmail=admin_secondary_email)
  elif command == u'logo':
    logoFile = getString(4, OBJECT_FILE_NAME)
    logoImage = readFile(logoFile)
    callGData(service=adminObj, function=u'UpdateDomainLogo', logoImage=logoImage)
  elif command == u'mx_verify':
    result = callGData(service=adminObj, function=u'UpdateMXVerificationStatus')
    print u'Verification Method: %s' % result[u'verificationMethod']
    print u'Verified: %s' % result[u'verified']
  elif command == u'sso_settings':
    enableSSO = samlSignonUri = samlLogoutUri = changePasswordUri = ssoWhitelist = useDomainSpecificIssuer = None
    i = 4
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg == u'enabled':
        enableSSO = getBoolean(i+1)
        i += 2
      elif my_arg == u'signonuri':
        samlSignonUri = getString(i+1, OBJECT_URI)
        i += 2
      elif my_arg == u'signouturi':
        samlLogoutUri = getString(i+1, OBJECT_URI)
        i += 2
      elif my_arg == u'passworduri':
        changePasswordUri = getString(i+1, OBJECT_URI)
        i += 2
      elif my_arg == u'whitelist':
        ssoWhitelist = getString(i+1, OBJECT_CIDR_NETMASK)
        i += 2
      elif my_arg == u'usedomainspecificissuer':
        useDomainSpecificIssuer = getBoolean(i+1)
        i += 2
      else:
        unknownArgumentExit(i)
    callGData(service=adminObj, function=u'UpdateSSOSettings', enableSSO=enableSSO,
              samlSignonUri=samlSignonUri, samlLogoutUri=samlLogoutUri,
              changePasswordUri=changePasswordUri, ssoWhitelist=ssoWhitelist,
              useDomainSpecificIssuer=useDomainSpecificIssuer)
  elif command == u'sso_key':
    keyFile = getString(4, OBJECT_FILE_NAME)
    keyData = readFile(keyFile)
    callGData(service=adminObj, function=u'UpdateSSOKey', signingKey=keyData)
  elif command == u'user_migrations':
    value = getBoolean(4)
    result = callGData(service=adminObj, function=u'UpdateUserMigrationStatus', enableUserMigration=value)
  elif command == u'outbound_gateway':
    gateway = getString(4, OBJECT_HOST_NAME, emptyOK=True)
    mode = getChoice(6, OUTBOUND_GATEWAY_MODE_CHOICES_MAP, mapChoice=True)
    try:
      result = callGData(service=adminObj, function=u'UpdateOutboundGatewaySettings', smartHost=gateway, smtpMode=mode)
    except TypeError:
      pass
  elif command == u'email_route':
    i = 4
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg == u'destination':
        destination = getString(i+1, OBJECT_HOST_NAME)
        i += 2
      elif my_arg == u'rewriteto':
        rewrite_to = getBoolean(i+1)
        i += 2
      elif my_arg == u'enabled':
        enabled = getBoolean(i+1)
        i += 2
      elif my_arg == u'bouncenotifications':
        bounce_notifications = getBoolean(i+1)
        i += 2
      elif my_arg == u'accounthandling':
        account_handling = getChoice(i+1, ADMINSETTINGS_EMAIL_ACCOUNT_HANDLING_CHOICES_MAP, mapChoice=True)
        i += 2
      else:
        unknownArgumentExit(i)
    callGData(service=adminObj, function=u'AddEmailRoute', routeDestination=destination, routeRewriteTo=rewrite_to, routeEnabled=enabled,
              bounceNotifications=bounce_notifications, accountHandling=account_handling)
  else:
    unknownArgumentExit(3)

def doGetDomainInfo():
  adm = buildGAPIObject(u'admin-settings')
  if getChoice(3, LOGO_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    logoFile = getString(4, OBJECT_FILE_NAME)
    adminSettingsObject = getAdminSettingsObject()
    writeFile(logoFile, adminSettingsObject.GetDomainLogo())
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
  cd = buildGAPIObject(u'directory')
  user = getEmailAddress(3)
  print u"Deleting account for %s" % (user)
  callGAPI(service=cd.users(), function=u'delete', userKey=user)

def doUndeleteUser():
  cd = buildGAPIObject(u'directory')
  user = getEmailAddress(3)
  orgUnitPath = u'/'
  i = 4
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg in [u'ou', u'org']:
      orgUnitPath = getOrgUnitPath(i+1)
      i += 2
    else:
      unknownArgumentExit(i)
  user_uid = user if user.find(u'@') == -1 else None
  if not user_uid:
    print u'Looking up UID for %s...' % user
    deleted_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', customer=GC_Values[GC_CUSTOMER_ID], showDeleted=True, maxResults=500)
    matching_users = list()
    for deleted_user in deleted_users:
      if str(deleted_user[u'primaryEmail']).lower() == user:
        matching_users.append(deleted_user)
    if len(matching_users) == 0:
      print u'{0}Could not find deleted user with that address.\n'.format(ERROR_PREFIX)
      sys.exit(3)
    if len(matching_users) > 1:
      print u'{0}More than one matching deleted {1} user. Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"\n'.format(ERROR_PREFIX, user)
      for matching_user in matching_users:
        print u' uid:%s ' % matching_user[u'id']
        for attr_name in [u'creationTime', u'lastLoginTime', u'deletionTime']:
          try:
            if matching_user[attr_name] == NEVER_TIME:
              matching_user[attr_name] = NEVER
            print u'   %s: %s ' % (attr_name, matching_user[attr_name])
          except KeyError:
            pass
        print
      sys.exit(3)
    user_uid = matching_users[0][u'id']
  print u"Undeleting account for %s" % user
  callGAPI(service=cd.users(), function=u'undelete', userKey=user_uid, body={u'orgUnitPath': orgUnitPath})

def doDeleteGroup():
  cd = buildGAPIObject(u'directory')
  group = getEmailAddress(3)
  print u"Deleting group %s" % group
  callGAPI(service=cd.groups(), function=u'delete', groupKey=group)

def doDeleteAlias(alias_email=None):
  cd = buildGAPIObject(u'directory')
  if alias_email == None:
    i = 3
    alias_type = getChoice(i, ALIAS_TARGET_TYPES, defaultChoice=None)
    if alias_type:
      i += 1
    else:
      alias_type = ALIAS_TARGET_TYPE_TARGET
    alias_email = getEmailAddress(i)
  else:
    alias_type = ALIAS_TARGET_TYPE_TARGET
  print u"Deleting alias %s" % alias_email
  if alias_type != ALIAS_TARGET_TYPE_GROUP:
    try:
      callGAPI(service=cd.users().aliases(), function=u'delete', throw_reasons=[u'invalid', u'badRequest', u'notFound'],
               userKey=alias_email, alias=alias_email)
      return
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      if reason == u'notFound':
        print u'Error: The alias %s does not exist' % alias_email
        sys.exit(7)
  if alias_type != ALIAS_TARGET_TYPE_USER:
    callGAPI(service=cd.groups().aliases(), function=u'delete', groupKey=alias_email, alias=alias_email)

def doDeleteResourceCalendar():
  rescal = getResCalObject()
  resId = getString(3, OBJECT_RESOURCE_ID)
  print u"Deleting resource calendar %s" % resId
  callGData(service=rescal, function=u'DeleteResourceCalendar', id=resId)

def doDeleteOrg():
  cd = buildGAPIObject(u'directory')
  orgUnitPath = getOrgUnitPath(3, absolutePath=False)
  print u"Deleting organization %s" % orgUnitPath
  callGAPI(service=cd.orgunits(), function=u'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath)

def flatten_json(structure, key="", path="", flattened=None):
  if flattened == None:
    flattened = {}
  if not isinstance(structure, (dict, list)):
    flattened[((path + ".") if path else "") + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      flatten_json(item, "%d" % i, ".".join([item for item in [path, key] if item]), flattened)
  else:
    for new_key, value in structure.items():
      if new_key in [u'kind', u'etag']:
        continue
      if value == NEVER_TIME:
        value = NEVER
      flatten_json(value, new_key, ".".join([item for item in [path, key] if item]), flattened)
  return flattened

PRINT_USERS_ARGUMENT_TO_PROPERTY_MAP = {
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
  u'externalId': [u'externalIds',],
  u'externalIds': [u'externalIds',],
  u'externalid': [u'externalIds',],
  u'externalids': [u'externalIds',],
  u'familyname': [u'name',],
  u'firstname': [u'name',],
  u'fullname': [u'name',],
  u'gal': [u'includeInGlobalAddressList',],
  u'givenname': [u'name',],
  u'id': [u'id',],
  u'im': [u'ims',],
  u'ims': [u'ims',],
  u'includeinglobaladdresslist': [u'includeInGlobalAddressList',],
  u'ipwhitelisted': [u'ipWhitelisted',],
  u'isadmin': [u'isAdmin', u'isDelegatedAdmin',],
  u'isdelegatedadmin': [u'isAdmin', u'isDelegatedAdmin',],
  u'ismailboxsetup': [u'isMailboxSetup',],
  u'lastlogintime': [u'lastLoginTime',],
  u'lastname': [u'name',],
  u'name': [u'name',],
  u'nicknames': [u'aliases', u'nonEditableAliases',],
  u'noneditablealiases': [u'aliases', u'nonEditableAliases',],
  u'note': [u'notes',],
  u'notes': [u'notes',],
  u'org': [u'orgUnitPath',],
  u'organization': [u'organizations',],
  u'organizations': [u'organizations',],
  u'orgunitpath': [u'orgUnitPath',],
  u'otheremail': [u'emails',],
  u'ou': [u'orgUnitPath',],
  u'phone': [u'phones',],
  u'phones': [u'phones',],
  u'photo': [u'thumbnailPhotoUrl',],
  u'photourl': [u'thumbnailPhotoUrl',],
  u'relation': [u'relations',],
  u'relations': [u'relations',],
  u'suspended': [u'suspended', u'suspensionReason',],
  u'thumbnailphotourl': [u'thumbnailPhotoUrl',],
  u'website': [u'websites',],
  u'websites': [u'websites',],
  }

USERS_ORDERBY_CHOICES_MAP = {
  u'familyname': u'familyName',
  u'lastname': u'familyName',
  u'givenname': u'givenName',
  u'firstname': u'givenName',
  u'email': u'email',
  }

def doPrintUsers():
  cd = buildGAPIObject(u'directory')
  fieldsList = [u'primaryEmail',]
  customer = GC_Values[GC_CUSTOMER_ID]
  printDomain = None
  query = None
  projection = USER_PROJECTION_BASIC
  customFieldMask = None
  getGroupFeed = getLicenseFeed = email_parts = False
  todrive = False
  viewType = deleted_only = orderBy = sortOrder = None
  groupsDelimiter = u' '
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'allfields':
      fieldsList = []
      i += 1
    elif my_arg == u'custom':
      fieldsList.append(u'customSchemas')
      customFieldMask = getString(i+1, OBJECT_SCHEMA_NAME_LIST).replace(u' ', u',')
      if customFieldMask.lower() == u'all':
        customFieldMask = None
        projection = USER_PROJECTION_FULL
      else:
        projection = USER_PROJECTION_CUSTOM
      i += 2
    elif my_arg in [u'deletedonly', u'onlydeleted']:
      deleted_only = True
      i += 1
    elif my_arg == u'delimiter':
      groupsDelimiter = getString(i+1, OBJECT_STRING)
      i += 2
    elif my_arg == u'orderby':
      orderBy = getChoice(i+1, USERS_ORDERBY_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg == u'userview':
      viewType = u'domain_public'
      i += 1
    elif my_arg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[my_arg]
      i += 1
    elif my_arg == u'domain':
      printDomain = getString(i+1, OBJECT_DOMAIN_NAME).lower()
      customer = None
      i += 2
    elif my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg in PRINT_USERS_ARGUMENT_TO_PROPERTY_MAP:
      fieldsList.extend(PRINT_USERS_ARGUMENT_TO_PROPERTY_MAP[my_arg])
      i += 1
    elif my_arg == u'groups':
      getGroupFeed = True
      i += 1
    elif my_arg in [u'license', u'licenses', u'licence', u'licences']:
      getLicenseFeed = True
      i += 1
    elif my_arg in [u'emailpart', u'emailparts', u'username']:
      email_parts = True
      i += 1
    else:
      unknownArgumentExit(i)
  if fieldsList:
    fields = u'nextPageToken,users({0})'.format(u','.join(set(fieldsList)))
  else:
    fields = None
  titles, csvRows = initializeTitlesCSVfile([u'primaryEmail'])
  printGettingMessage(u"Getting all users in Google Apps account (may take some time on a large account)...\n")
  page_message = getPageMessage(u'users', showFirstLastItems=True)
  entityList = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                             message_attribute=u'primaryEmail', customer=customer, domain=printDomain, fields=fields,
                             showDeleted=deleted_only, maxResults=500, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                             query=query, projection=projection, customFieldMask=customFieldMask)
  for userEntity in entityList:
    if email_parts and (u'primaryEmail' in userEntity):
      userEmail = userEntity[u'primaryEmail']
      if userEmail.find(u'@') != -1:
        userEntity[u'primaryEmailLocal'], userEntity[u'primaryEmailDomain'] = splitEmailAddress(userEmail)
    csvRows.append(flatten_json(userEntity))
    for item in csvRows[-1]:
      if item not in csvRows[0]:
        addTitleToCSVfile(item, titles, csvRows)
  titles.remove(u'primaryEmail')
  titles = [u'primaryEmail'] + sorted(titles)
  if getGroupFeed:
    addTitleToCSVfile(u'Groups', titles, csvRows)
    i = 0
    count = len(csvRows) - 1
    for user in csvRows[1:]:
      i += 1
      userEmail = user[u'primaryEmail']
      printGettingMessage(u"Getting Group Membership for %s (%s/%s)\r\n" % (userEmail, i, count))
      groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', userKey=userEmail)
      user[u'Groups'] = groupsDelimiter.join([groupname[u'email'] for groupname in groups])
  if getLicenseFeed:
    addTitleToCSVfile(u'Licenses', titles, csvRows)
    licenses = doPrintLicenses(return_list=True)
    if len(licenses) > 1:
      for user in csvRows[1:]:
        user_licenses = []
        for u_license in licenses:
          if u_license[u'userId'].lower() == user[u'primaryEmail'].lower():
            user_licenses.append(u_license[u'skuId'])
        user[u'Licenses'] = groupsDelimiter.join(user_licenses)
  writeCSVfile(csvRows, titles, u'Users', todrive)

GROUP_ARGUMENT_TO_FIELD_NAME_TITLE_MAP = {
  u'admincreated': [u'adminCreated', u'Admin_Created'],
  u'aliases': [u'aliases', u'Aliases', u'nonEditableAliases', u'NonEditableAliases'],
  u'description': [u'description', u'Description'],
  u'email': [u'email', u'Email'],
  u'id': [u'id', u'ID'],
  u'name': [u'name', u'Name'],
  }

def doPrintGroups():
  cd = buildGAPIObject(u'directory')
  members = owners = managers = settings = todrive = False
  customer = GC_Values[GC_CUSTOMER_ID]
  usedomain = usemember = None
  aliasDelimiter = u' '
  memberDelimiter = u'\n'
  titles, csvRows = initializeTitlesCSVfile()
  fieldsList = []
  fieldsTitles = {}
  addFieldToCSVfile(u'email', GROUP_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
  roles = []
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'domain':
      usedomain = getString(i+1, OBJECT_DOMAIN_NAME).lower()
      customer = None
      i += 2
    elif my_arg == u'delimiter':
      memberDelimiter = getString(i+1, OBJECT_STRING)
      aliasDelimiter = memberDelimiter
      i += 2
    elif my_arg == u'member':
      usemember = getEmailAddress(i+1)
      customer = None
      i += 2
    elif my_arg in GROUP_ARGUMENT_TO_FIELD_NAME_TITLE_MAP:
      addFieldToCSVfile(my_arg, GROUP_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
      i += 1
    elif my_arg == u'members':
      if my_arg not in roles:
        roles.append(ROLE_MEMBER)
        addTitleToCSVfile(u'Members', titles, csvRows)
        members = True
      i += 1
    elif my_arg == u'owners':
      if my_arg not in roles:
        roles.append(ROLE_OWNER)
        addTitleToCSVfile(u'Owners', titles, csvRows)
        owners = True
      i += 1
    elif my_arg == u'managers':
      if my_arg not in roles:
        roles.append(ROLE_MANAGER)
        addTitleToCSVfile(u'Managers', titles, csvRows)
        managers = True
      i += 1
    elif my_arg == u'settings':
      settings = True
      i += 1
    else:
      unknownArgumentExit(i)
  roles = u','.join(sorted(set(roles)))
  printGettingMessage(u"Retrieving All Groups for Google Apps account (may take some time on a large account)...\n")
  page_message = getPageMessage(u'groups', showTotal=False, showFirstLastItems=True)
  entityList = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', page_message=page_message,
                             message_attribute=u'email', customer=customer, domain=usedomain, userKey=usemember,
                             fields=u'nextPageToken,groups({0})'.format(u','.join(fieldsList)))
  total_groups = len(entityList)
  count = 0
  for groupEntity in entityList:
    count += 1
    group = {}
    for field in fieldsList:
      if field in groupEntity:
        if isinstance(groupEntity[field], list):
          group[fieldsTitles[field]] = aliasDelimiter.join(groupEntity[field])
        else:
          group[fieldsTitles[field]] = groupEntity[field]
    if roles:
      printGettingMessage(u' Getting %s for %s (%s of %s)\n' % (roles, groupEntity[u'email'], count, total_groups))
      page_message = getPageMessage(u'members', showTotal=False, showFirstLastItems=True)
      all_group_members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', page_message=page_message,
                                        message_attribute=u'email', groupKey=groupEntity[u'email'], roles=roles, fields=u'nextPageToken,members(email,role)')
      if members:
        allMembers = list()
      if managers:
        allManagers = list()
      if owners:
        allOwners = list()
      for member in all_group_members:
        member_email = member.get(u'email', None)
        if not member_email:
          sys.stderr.write(u' Not sure to do with: %s\n' % member)
          continue
        role = member.get(u'role', None)
        if role:
          if role == ROLE_MEMBER:
            if members:
              allMembers.append(member_email)
          elif role == ROLE_MANAGER:
            if managers:
              allManagers.append(member_email)
          elif role == ROLE_OWNER:
            if owners:
              allOwners.append(member_email)
          elif members:
            allMembers.append(member_email)
        elif members:
          allMembers.append(member_email)
      if members:
        group[u'Members'] = memberDelimiter.join(allMembers)
      if managers:
        group[u'Managers'] = memberDelimiter.join(allManagers)
      if owners:
        group[u'Owners'] = memberDelimiter.join(allOwners)
    if settings:
      printGettingMessage(u" Retrieving Settings for group %s (%s of %s)...\r\n" % (groupEntity[u'email'], count, total_groups))
      gs = buildGAPIObject(u'groupssettings')
      settings = callGAPI(service=gs.groups(), function=u'get', retry_reasons=[u'serviceLimit'], groupUniqueId=groupEntity[u'email'])
      for key in settings:
        if key in [u'email', u'name', u'description', u'kind', u'etag']:
          continue
        setting_value = settings[key]
        if setting_value == None:
          setting_value = u''
        if key not in csvRows[0]:
          addTitleToCSVfile(key, titles, csvRows)
        group[key] = setting_value
      csvRows.append(group)
  writeCSVfile(csvRows, titles, u'Groups', todrive)

ORG_ARGUMENT_TO_FIELD_NAME_TITLE_MAP = {
  u'description': [u'description', u'Description'],
  u'id': [u'orgUnitId', u'ID'],
  u'inherit': [u'blockInheritance', u'InheritanceBlocked'],
  u'name': [u'name', u'Name'],
  u'orgunitpath': [u'orgUnitPath', u'Path'],
  u'parent': [u'parentOrgUnitPath', u'Parent'],
  u'parentid': [u'parentOrgUnitId', u'ParentID'],
  }

def doPrintOrgs():
  cd = buildGAPIObject(u'directory')
  todrive = False
  listType = ORGANIZATION_QUERY_TYPE_ALL
  orgUnitPath = u"/"
  titles, csvRows = initializeTitlesCSVfile()
  fieldsList = []
  fieldsTitles = {}
  addFieldToCSVfile(u'orgunitpath', ORG_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'allfields':
      titles, csvRows = initializeTitlesCSVfile()
      fieldsList = []
      fieldsTitles = {}
      i += 1
    elif my_arg == u'toplevelonly':
      listType = ORGANIZATION_QUERY_TYPE_CHILDREN
      i += 1
    elif my_arg == u'fromparent':
      orgUnitPath = getOrgUnitPath(i+1)
      i += 2
    elif my_arg in ORG_ARGUMENT_TO_FIELD_NAME_TITLE_MAP:
      addFieldToCSVfile(my_arg, ORG_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
      i += 1
    else:
      unknownArgumentExit(i)
  if fieldsList:
    ## Move Path to end of list
    ftList = ORG_ARGUMENT_TO_FIELD_NAME_TITLE_MAP
    titles.remove(ftList[u'orgunitpath'][1])
    titles.append(ftList[u'orgunitpath'][1])
    fields = u'organizationUnits({0})'.format(u','.join(set(fieldsList)))
  else:
    fields = None
  printGettingMessage(u"Retrieving All Organizational Units for your account (may take some time on large domain)...")
  orgs = callGAPI(service=cd.orgunits(), function=u'list', customerId=GC_Values[GC_CUSTOMER_ID], fields=fields, type=listType, orgUnitPath=orgUnitPath)
  printGettingMessage(u"done\n")
  if not orgs or (u'organizationUnits' not in orgs):
    print u'0 org units in this Google Apps instance...'
    return
  for orgEntity in orgs[u'organizationUnits']:
    orgUnit = {}
    if not fields:
      orgUnit = flatten_json(orgEntity)
      for row in orgUnit:
        if row not in csvRows[0]:
          addTitleToCSVfile(row, titles, csvRows)
    else:
      for field in fieldsList:
        orgUnit[fieldsTitles[field]] = orgEntity.get(field, u'')
    csvRows.append(orgUnit)
  writeCSVfile(csvRows, titles, u'Orgs', todrive)

def doPrintAliases():
  cd = buildGAPIObject(u'directory')
  todrive = False
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      unknownArgumentExit(i)
  titles, csvRows = initializeTitlesCSVfile([u'Alias', u'Target', u'TargetType'])
  printGettingMessage(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
  page_message = getPageMessage(u'users', showTotal=False, showFirstLastItems=True)
  all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], fields=u'users(primaryEmail,aliases),nextPageToken', maxResults=500)
  for user in all_users:
    for alias in user.get(u'aliases', []):
      csvRows.append({u'Alias': alias, u'Target': user[u'primaryEmail'], u'TargetType': u'User'})
  printGettingMessage(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
  page_message = getPageMessage(u'groups', showTotal=False, showFirstLastItems=True)
  all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', page_message=page_message,
                             message_attribute=u'email', customer=GC_Values[GC_CUSTOMER_ID], fields=u'groups(email,aliases),nextPageToken')
  for group in all_groups:
    for alias in group.get(u'aliases', []):
      csvRows.append({u'Alias': alias, u'Target': group[u'email'], u'TargetType': u'Group'})
  writeCSVfile(csvRows, titles, u'Aliases', todrive)

def doPrintGroupMembers():
  cd = buildGAPIObject(u'directory')
  todrive = all_groups = False
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'group':
      all_groups = [{u'email': getEmailAddress(i+1)}]
      i += 2
    else:
      unknownArgumentExit(i)
  titles, csvRows = initializeTitlesCSVfile([u'id', u'role', u'group', u'email', u'type'])
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
      for title in member:
        if title in [u'kind', u'etag']:
          continue
        if title not in csvRows[0]:
          addTitleToCSVfile(title, titles, csvRows)
        member_attr[title] = member[title]
      csvRows.append(member_attr)
    i += 1
  writeCSVfile(csvRows, titles, u'Group Members', todrive)

MOBILE_ORDERBY_CHOICES_MAP = {
  u'deviceid': u'deviceId',
  u'email': u'email',
  u'lastsync': u'lastSync',
  u'model': u'model',
  u'name': u'name',
  u'os': u'os',
  u'status': u'status',
  u'type': u'type',
  }

MOBILE_PROJECTION_BASIC = u'BASIC'
MOBILE_PROJECTION_FULL = u'FULL'

MOBILE_PROJECTION_CHOICES_MAP = {
  u'basic': MOBILE_PROJECTION_BASIC,
  u'full': MOBILE_PROJECTION_FULL,
  }

def doPrintMobileDevices():
  cd = buildGAPIObject(u'directory')
  todrive = False
  query = projection = orderBy = sortOrder = None
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'orderby':
      orderBy = getChoice(i+1, MOBILE_ORDERBY_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[my_arg]
      i += 1
    elif my_arg in MOBILE_PROJECTION_CHOICES_MAP:
      projection = MOBILE_PROJECTION_CHOICES_MAP[my_arg]
      i += 1
    else:
      unknownArgumentExit(i)
  printGettingMessage(u'Retrieving All Mobile Devices for organization (may take some time for large accounts)...\n')
  page_message = getPageMessage(u'mobile devices')
  devices = callGAPIpages(service=cd.mobiledevices(), function=u'list', items=u'mobiledevices', page_message=page_message,
                          customerId=GC_Values[GC_CUSTOMER_ID], query=query, projection=projection,
                          orderBy=orderBy, sortOrder=sortOrder)
  titles, csvRows = initializeTitlesCSVfile([u'resourceId'])
  if devices:
    for mobile in devices:
      mobiledevice = {}
      for attrib in mobile:
        try:
          if attrib in [u'kind', u'etag', u'applications']:
            continue
          if attrib not in csvRows[0]:
            addTitleToCSVfile(attrib, titles, csvRows)
          if attrib in [u'name', u'email']:
            mobiledevice[attrib] = mobile[attrib][0]
          else:
            mobiledevice[attrib] = mobile[attrib]
        except KeyError:
          pass
      csvRows.append(mobiledevice)
  writeCSVfile(csvRows, titles, u'Mobile', todrive)

CROS_ORDERBY_CHOICES_MAP = {
  u'lastsync': u'lastSync',
  u'location': u'annotatedLocation',
  u'notes': u'notes',
  u'serialnumber': u'serialNumber',
  u'status': u'status',
  u'supportenddate': u'supportEndDate',
  u'user': u'annotatedUser',
  }

CHROMEOSDEVICE_PROJECTION_BASIC = u'BASIC'
CHROMEOSDEVICE_PROJECTION_FULL = u'FULL'

CROS_PROJECTION_CHOICES_MAP = {
  u'basic': CHROMEOSDEVICE_PROJECTION_BASIC,
  u'full': CHROMEOSDEVICE_PROJECTION_FULL,
  }


def doPrintCrosDevices():
  cd = buildGAPIObject(u'directory')
  todrive = False
  query = projection = orderBy = sortOrder = None
  noLists = False
  selectAttrib = None
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'query':
      query = getString(i+1, OBJECT_QUERY)
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
      orderBy = getChoice(i+1, CROS_ORDERBY_CHOICES_MAP, mapChoice=True)
      i += 2
    elif my_arg in SORTORDER_CHOICES_MAP:
      sortOrder = SORTORDER_CHOICES_MAP[my_arg]
      i += 1
    elif my_arg in CROS_PROJECTION_CHOICES_MAP:
      projection = CROS_PROJECTION_CHOICES_MAP[my_arg]
      i += 1
    else:
      unknownArgumentExit(i)
  if selectAttrib:
    projection = CHROMEOSDEVICE_PROJECTION_FULL
  printGettingMessage(u'Retrieving All Chrome OS Devices for organization (may take some time for large accounts)...\n')
  page_message = getPageMessage(u'Chrome devices')
  devices = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices', page_message=page_message,
                          query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection=projection, orderBy=orderBy, sortOrder=sortOrder)
  titles, csvRows = initializeTitlesCSVfile([u'deviceId'])
  if devices:
    if (not noLists) and (not selectAttrib):
      for cros in devices:
        csvRows.append(flatten_json(cros))
        for item in csvRows[-1]:
          if item not in csvRows[0]:
            addTitleToCSVfile(item, titles, csvRows)
    else:
      attribMap = {}
      for cros in devices:
        row = {}
        for attrib in cros:
          if attrib in [u'kind', u'etag', u'recentUsers', u'activeTimeRanges']:
            continue
          if attrib not in csvRows[0]:
            addTitleToCSVfile(attrib, titles, csvRows)
          row[attrib] = cros[attrib]
        if noLists or (selectAttrib not in cros) or (not cros[selectAttrib]):
          csvRows.append(row)
        else:
          if not attribMap:
            for attrib in cros[selectAttrib][0]:
              xattrib = u'{0}.{1}'.format(selectAttrib, attrib)
              if xattrib not in csvRows[0]:
                addTitleToCSVfile(xattrib, titles, csvRows)
              attribMap[attrib] = xattrib
          for item in cros[selectAttrib]:
            new_row = row.copy()
            for attrib in item:
              if isinstance(item[attrib], (bool, int)):
                new_row[attribMap[attrib]] = str(item[attrib])
              else:
                new_row[attribMap[attrib]] = item[attrib]
            csvRows.append(new_row)
  writeCSVfile(csvRows, titles, u'CrOS', todrive)

def doPrintLicenses(return_list=False, skus=None):
  lic = buildGAPIObject(u'licensing')
  products = GOOGLE_PRODUCTS
  licenses = []
  titles, csvRows = initializeTitlesCSVfile([u'userId', u'productId', u'skuId'])
  todrive = False
  if not return_list:
    i = 3
    while i < len(sys.argv):
      my_arg = getArgument(i)
      if my_arg == u'todrive':
        todrive = True
        i += 1
      elif my_arg in [u'products', u'product']:
        products = getGoogleProductListMap(i+1)
        i += 2
      elif my_arg in [u'sku', u'skus']:
        skus = getGoogleSKUListMap(i+1)
        i += 2
      else:
        unknownArgumentExit(i)
  if skus:
    for sku in skus:
      productId = GOOGLE_SKUS[sku]
      page_message = getPageMessage(u'Licenses', forWhom=sku)
      try:
        licenses += callGAPIpages(service=lic.licenseAssignments(), function=u'listForProductAndSku', throw_reasons=[u'invalid', u'forbidden'],
                                  page_message=page_message, customerId=GC_Values[GC_DOMAIN], productId=GOOGLE_SKUS[sku], skuId=sku, fields=u'items(productId,skuId,userId),nextPageToken')
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
    a_license = {}
    for title in u_license:
      if title in [u'kind', u'etags', u'selfLink']:
        continue
      if title not in csvRows[0]:
        addTitleToCSVfile(title, titles, csvRows)
      a_license[title] = u_license[title]
    csvRows.append(a_license)
  if return_list:
    return csvRows
  writeCSVfile(csvRows, titles, u'Licenses', todrive)

def doPrintTokens():
  cd = buildGAPIObject(u'directory')
  todrive = False
  entity_type = None
  i = 3
  while i < len(sys.argv):
    my_arg = getString(i, OBJECT_ARGUMENT).lower()
    if my_arg == u'todrive':
      todrive = True
      i += 1
    else:
      entity_type, all_users = getEntityToModify(i)
  if not entity_type:
    all_users = getUsersToModify(CL_ENTITY_ALL_USERS, None, silent=False)
  titles, csvRows = initializeTitlesCSVfile([u'user', u'displayText', u'clientId', u'nativeApp', u'anonymous', u'scopes'])
  for user in all_users:
    user = normalizeEmailAddressOrUID(user)
    printGettingMessage(u' getting tokens for %s\n' % user)
    user_tokens = callGAPI(service=cd.tokens(), function='list', userKey=user)
    if user_tokens and (u'items' in user_tokens):
      for user_token in user_tokens[u'items']:
        this_token = {u'user': user, 'scopes': u' '.join(user_token[u'scopes'])}
        for token_item in user_token:
          if token_item in [u'kind', u'etag', u'scopes']:
            continue
          this_token[token_item] = user_token[token_item]
          if token_item not in csvRows[0]:
            addTitleToCSVfile(token_item, titles, csvRows)
        csvRows.append(this_token)
  writeCSVfile(csvRows, titles, u'OAuth Tokens', todrive)

RESCAL_ALLFIELDS = [u'name', u'id', u'description', u'email', u'type',]

RESCAL_ARGUMENT_TO_FIELD_NAME_TITLE_MAP = {
  u'description': [u'resourceDescription', u'Description'],
  u'email': [u'resourceEmail', u'Email'],
  u'id': [u'resourceId', u'ID'],
  u'name': [u'resourceCommonName', u'Name'],
  u'type': [u'resourceType', u'Type'],
  }

def doPrintResources():
  resObj = getResCalObject()
  titles, csvRows = initializeTitlesCSVfile()
  fieldsList = []
  fieldsTitles = {}
  addFieldToCSVfile(u'name', RESCAL_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
  todrive = False
  i = 3
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'allfields':
      titles, csvRows = initializeTitlesCSVfile()
      fieldsList = []
      fieldsTitles = {}
      for field in RESCAL_ALLFIELDS:
        addFieldToCSVfile(field, RESCAL_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
      i += 1
    elif my_arg in RESCAL_ARGUMENT_TO_FIELD_NAME_TITLE_MAP:
      addFieldToCSVfile(my_arg, RESCAL_ARGUMENT_TO_FIELD_NAME_TITLE_MAP, fieldsList, fieldsTitles, titles, csvRows)
      i += 1
    else:
      unknownArgumentExit(i)
  printGettingMessage(u"Retrieving All Resource Calendars for your account (may take some time on a large domain)")
  resources = callGData(service=resObj, function=u'RetrieveAllResourceCalendars')
  for resource in resources:
    resUnit = {}
    for field in fieldsList:
      resUnit[fieldsTitles[field]] = resource.get(field, u'')
    csvRows.append(resUnit)
  writeCSVfile(csvRows, titles, u'Resources', todrive)
#
# Utilities for audit command
#
def getAuditParameters(i, userDomainRequired=True, requestIdRequired=True, destUserRequired=False):
  auditObject = getAuditObject()
  emailAddress = getEmailAddress(i, noUid=True, optional=not userDomainRequired)
  i += 1
  parameters = {}
  if emailAddress:
    parameters[u'auditUser'], auditObject.domain = splitEmailAddress(emailAddress)
    if requestIdRequired:
      parameters[u'requestId'] = getString(i, OBJECT_REQUEST_ID)
      i += 1
    if destUserRequired:
      destEmailAddress = getEmailAddress(i, noUid=True)
      parameters[u'auditDestUserName'], destDomain = splitEmailAddress(destEmailAddress)
      if auditObject.domain != destDomain:
        invalidArgumentExit(i, u'in domain {0}'.format(auditObject.domain))
  return (auditObject, parameters)

def doCreateMonitor():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=False, destUserRequired=True)
  #end_date defaults to 30 days in the future...
  end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(u"%Y-%m-%d %H:%M")
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  i = 6
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'begin':
      begin_date = getYYYYMMDDHHMM(i+1)
      i += 2
    elif my_arg == u'end':
      end_date = getYYYYMMDDHHMM(i+1)
      i += 2
    elif my_arg == u'incomingheaders':
      incoming_headers_only = True
      i += 1
    elif my_arg == u'outgoingheaders':
      outgoing_headers_only = True
      i += 1
    elif my_arg == u'nochats':
      chats = False
      i += 1
    elif my_arg == u'nodrafts':
      drafts = False
      i += 1
    elif my_arg == u'chatheaders':
      chats_headers_only = True
      i += 1
    elif my_arg == u'draftheaders':
      drafts_headers_only = True
      i += 1
    else:
      unknownArgumentExit(i)
  callGData(service=audit, function=u'createEmailMonitor',
            source_user=parameters[u'auditUser'], destination_user=parameters[u'auditDestUserName'], end_date=end_date, begin_date=begin_date,
            incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
            drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)

def doShowMonitors():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=False, destUserRequired=False)
  results = callGData(service=audit, function=u'getEmailMonitors',
                      user=parameters[u'auditUser'])
  print parameters[u'auditUser']+u' has the following monitors:'
  print u''
  for monitor in results:
    print u'  Destination: '+monitor['destUserName']
    print u'    Begin: '+monitor.get('beginDate', u'immediately')
    print u'    End: '+monitor['endDate']
    print u'    Monitor Incoming: '+monitor['outgoingEmailMonitorLevel']
    print u'    Monitor Outgoing: '+monitor['incomingEmailMonitorLevel']
    print u'    Monitor Chats: '+monitor['chatMonitorLevel']
    print u'    Monitor Drafts: '+monitor['draftMonitorLevel']
    print u''

def doDeleteMonitor():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=False, destUserRequired=True)
  callGData(service=audit, function=u'deleteEmailMonitor',
            source_user=parameters[u'auditUser'], destination_user=parameters[u'auditDestUserName'])

def printFileURLs(request):
  if u'numberOfFiles' in request:
    print u'  Number Of Files: '+request[u'numberOfFiles']
    for i in xrange(int(request[u'numberOfFiles'])):
      print u'    Url%s: %s' % (i, request[u'fileUrl%s' % i])

def printAcctInfoRequestStatus(request, showFiles=False):
  print u' Request ID: '+request[u'requestId']
  print u'  User: '+request[u'userEmailAddress']
  print u'  Status: '+request[u'status']
  print u'  Request Date: '+request[u'requestDate']
  print u'  Requested By: '+request[u'adminEmailAddress']
  if showFiles:
    printFileURLs(request)

def doRequestActivity():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=False, destUserRequired=False)
  results = callGData(service=audit, function=u'createAccountInformationRequest',
                      user=parameters[u'auditUser'])
  print u'Request successfully submitted:'
  print u''
  printAcctInfoRequestStatus(results, showFiles=False)

def doStatusActivityRequests():
  audit, parameters = getAuditParameters(4, userDomainRequired=False, requestIdRequired=True, destUserRequired=False)
  if parameters:
    results = callGData(service=audit, function=u'getAccountInformationRequestStatus',
                        user=parameters[u'auditUser'], request_id=parameters[u'requestId'])
    print u''
    printAcctInfoRequestStatus(results)
  else:
    results = callGData(service=audit, function=u'getAllAccountInformationRequestsStatus')
    print u'Current Activity Requests:'
    print u''
    for request in results:
      printAcctInfoRequestStatus(request, showFiles=True)
      print u''

def doDownloadActivityRequest():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=True, destUserRequired=False)
  results = callGData(service=audit, function=u'getAccountInformationRequestStatus',
                      user=parameters[u'auditUser'], request_id=parameters[u'requestId'])
  if results[u'status'] != u'COMPLETED':
    print u'Request needs to be completed before downloading, current status is: '+results[u'status']
    sys.exit(4)
  try:
    if int(results[u'numberOfFiles']) < 1:
      sys.stderr.write(u'{0}Request completed but no results were returned, try requesting again\n'.format(ERROR_PREFIX))
      sys.exit(4)
  except KeyError:
    sys.stderr.write(u'{0}Request completed but no files were returned, try requesting again\n'.format(ERROR_PREFIX))
    sys.exit(4)
  for i in range(0, int(results[u'numberOfFiles'])):
    url = results[u'fileUrl'+str(i)]
    filename = u'activity-'+parameters[u'auditUser']+'-'+parameters[u'requestId']+'-'+unicode(i)+u'.txt.gpg'
    print u'Downloading '+filename+u' ('+unicode(i+1)+u' of '+results[u'numberOfFiles']+')'
    geturl(url, filename)

def printMailboxExportRequestStatus(request, showFilter=False, showDates=False, showFiles=False):
  print u' Request ID: '+request['requestId']
  print u'  User: '+request['userEmailAddress']
  print u'  Status: '+request['status']
  print u'  Request Date: '+request['requestDate']
  print u'  Requested By: '+request['adminEmailAddress']
  print u'  Requested Parts: '+request['packageContent']
  if showFilter:
    print u'  Request Filter: '+request.get(u'searchQuery', u'None')
  print u'  Include Deleted: '+request['includeDeleted']
  if showDates:
    print u'  Begin: '+request.get('beginDate', u'Account creation date')
    print u'  End: '+request.get('endDate', u'Export request date')
  if showFiles:
    printFileURLs(request)

def doRequestExport():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=False, destUserRequired=False)
  begin_date = end_date = search_query = None
  headers_only = include_deleted = False
  i = 5
  while i < len(sys.argv):
    my_arg = getArgument(i)
    if my_arg == u'begin':
      begin_date = getYYYYMMDDHHMM(i+1)
      i += 2
    elif my_arg == u'end':
      end_date = getYYYYMMDDHHMM(i+1)
      i += 2
    elif my_arg == u'search':
      search_query = getString(i+1, OBJECT_QUERY)
      i += 2
    elif my_arg == u'headersonly':
      headers_only = True
      i += 1
    elif my_arg == u'includedeleted':
      include_deleted = True
      i += 1
    else:
      unknownArgumentExit(i)
  results = callGData(service=audit, function=u'createMailboxExportRequest',
                      user=parameters[u'auditUser'], begin_date=begin_date, end_date=end_date, include_deleted=include_deleted,
                      search_query=search_query, headers_only=headers_only)
  print u'Export request successfully submitted:'
  print u''
  printMailboxExportRequestStatus(results, showFilter=False, showDates=True, showFiles=False)

def doDeleteExport():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=True, destUserRequired=False)
  callGData(service=audit, function=u'deleteMailboxExportRequest',
            user=parameters[u'auditUser'], request_id=parameters[u'requestId'])

def doDeleteActivityRequest():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=True, destUserRequired=False)
  callGData(service=audit, function=u'deleteAccountInformationRequest',
            user=parameters[u'auditUser'], request_id=parameters[u'requestId'])

def doStatusExportRequests():
  audit, parameters = getAuditParameters(4, userDomainRequired=False, requestIdRequired=True, destUserRequired=False)
  if parameters:
    results = callGData(service=audit, function=u'getMailboxExportRequestStatus',
                        user=parameters[u'auditUser'], request_id=parameters[u'requestId'])
    print u''
    printMailboxExportRequestStatus(results, showFilter=True, showFiles=True)
  else:
    results = callGData(service=audit, function=u'getAllMailboxExportRequestsStatus')
    print u'Current Export Requests:'
    print u''
    for request in results:
      printMailboxExportRequestStatus(request, showFilter=True, showDates=False, showFiles=True)
      print u''

def doWatchExportRequest():
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=True, destUserRequired=False)
  while True:
    results = callGData(service=audit, function=u'getMailboxExportRequestStatus',
                        user=parameters[u'auditUser'], request_id=parameters[u'requestId'])
    if results[u'status'] != u'PENDING':
      print u'status is %s. Sending email.' % results[u'status']
      msg_txt = u"\n"
      msg_txt += u"  Request ID: %s\n" % results[u'requestId']
      msg_txt += u"  User: %s\n" % results[u'userEmailAddress']
      msg_txt += u"  Status: %s\n" % results[u'status']
      msg_txt += u"  Request Date: %s\n" % results[u'requestDate']
      msg_txt += u"  Requested By: %s\n" % results[u'adminEmailAddress']
      msg_txt += u"  Requested Parts: %s\n" % results[u'packageContent']
      msg_txt += u"  Request Filter: %s\n" % results.get(u'searchQuery', u"None")
      msg_txt += u"  Include Deleted: %s\n" % results[u'includeDeleted']
      if u'numberOfFiles' in results:
        msg_txt += u"  Number Of Files: %s\n" % results[u'numberOfFiles']
        for i in range(int(results['numberOfFiles'])):
          msg_txt += u"  Url%s: %s\n" % (i, results[u'fileUrl%s' % i])
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
  audit, parameters = getAuditParameters(4, userDomainRequired=True, requestIdRequired=True, destUserRequired=False)
  results = callGData(service=audit, function=u'getMailboxExportRequestStatus',
                      user=parameters[u'auditUser'], request_id=parameters[u'requestId'])
  if results[u'status'] != u'COMPLETED':
    systemErrorExit(4, MESSAGE_REQUEST_NOT_COMPLETE.format(results[u'status']))
  try:
    if int(results[u'numberOfFiles']) < 1:
      sys.stderr.write(u'{0}Request completed but no results were returned, try requesting again\n'.format(ERROR_PREFIX))
      sys.exit(4)
  except KeyError:
    systemErrorExit(4, MESSAGE_REQUEST_COMPLETED_NO_FILES)
  for i in range(0, int(results['numberOfFiles'])):
    url = results[u'fileUrl'+str(i)]
    filename = u'export-'+parameters[u'auditUser']+'-'+parameters[u'requestId']+'-'+str(i)+u'.mbox.gpg'
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

#
# Add entries in members to usersList if conditions are met
def addMembersToUsers(usersList, emailField, members, checkNotSuspended=False, checkOrgUnit=None):
  if checkNotSuspended:
    for member in members:
      email = member.get(emailField, None)
      if email and (not member[u'suspended']):
        usersList.append(email)
  elif checkOrgUnit:
    for member in members:
      email = member.get(emailField, None)
      if email and (checkOrgUnit == member[u'orgUnitPath'].lower()):
        usersList.append(email)
  else:
    for member in members:
      email = member.get(emailField, None)
      if email:
        usersList.append(email)

def getUsersToModify(entityType, entity, silent=False, memberRole=None):
  usersList = list()
  if entityType == None:
    entityType = getString(1, OBJECT_ENTITY_TYPE).lower()
  if entity == None:
    entity = getString(2, OBJECT_ENTITY)
  cd = buildGAPIObject(u'directory')
  if entityType in [CL_ENTITY_USER, CL_ENTITY_USERS]:
    if entityType == CL_ENTITY_USER:
      members = [entity,]
    else:
      members = entity.replace(u',', u' ').split()
    for user in members:
      usersList.append(user)
  elif entityType == CL_ENTITY_ALL_USERS:
    if not silent:
      printGettingMessage(u"Getting all users in Google Apps account (may take some time on a large account)...\n")
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,suspended,id)', maxResults=500)
    addMembersToUsers(usersList, u'primaryEmail', members, checkNotSuspended=True)
    if not silent:
      printGettingMessage(u"done getting %s users.\r\n" % len(members))
  elif entityType == CL_ENTITY_GROUP:
    group = entity
    if memberRole == None:
      memberRole_message = u'all members'
    else:
      memberRole_message = u'%ss' % memberRole.lower()
    group = normalizeEmailAddressOrUID(group)
    if not silent:
      printGettingMessage(u"Getting %s of %s (may take some time for large groups)..." % (memberRole_message, group))
    page_message = getPageMessage(memberRole_message, noNL=True)
    members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', page_message=page_message, groupKey=group, roles=memberRole, fields=u'nextPageToken,members(email,id)')
    addMembersToUsers(usersList, u'email', members)
  elif entityType == CL_ENTITY_OU:
    ou = makeOrgUnitPathAbsolute(entity)
    if not silent:
      printGettingMessage(u"Getting all users in the Google Apps organization (may take some time on a large domain)...\n")
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id,orgUnitPath)',
                            query=u"orgUnitPath='%s'" % ou, maxResults=500)
    addMembersToUsers(usersList, u'primaryEmail', members, checkOrgUnit=ou.lower())
    if not silent:
      printGettingMessage(u"%s users are directly in the OU.\n" % len(usersList))
  elif entityType == CL_ENTITY_OU_AND_CHILDREN:
    ou = makeOrgUnitPathAbsolute(entity)
    if not silent:
      printGettingMessage(u"Getting all users in the Google Apps organization (may take some time on a large domain)...\n")
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id)', query=u"orgUnitPath='%s'" % ou, maxResults=500)
    addMembersToUsers(usersList, u'primaryEmail', members)
    if not silent:
      printGettingMessage(u"done.\r\n")
  elif entityType == CL_ENTITY_QUERY:
    if not silent:
      printGettingMessage(u"Getting all users that match query %s (may take some time on a large domain)...\n" % entity)
    page_message = getPageMessage(u'users', noNL=True)
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id)', query=entity, maxResults=500)
    addMembersToUsers(usersList, u'primaryEmail', members)
    if not silent:
      printGettingMessage(u"done.\r\n")
  elif entityType == CL_ENTITY_LICENSES:
    licenses = doPrintLicenses(return_list=True, skus=entity.split(u','))
    addMembersToUsers(usersList, u'userId', licenses[1:])
  elif entityType in [CL_ENTITY_COURSEPARTICIPANTS, CL_ENTITY_TEACHERS, CL_ENTITY_STUDENTS]:
    croom = buildGAPIObject(u'classroom')
    users = []
    entity = normalizeCourseId(entity)
    if entityType in [CL_ENTITY_COURSEPARTICIPANTS, CL_ENTITY_TEACHERS]:
      page_message = getPageMessage(u'teachers', noNL=True)
      teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', page_message=page_message, courseId=entity)
      for teacher in teachers:
        email = teacher[u'profile'].get(u'emailAddress', None)
        if email:
          usersList.append(email)
    if entityType in [CL_ENTITY_COURSEPARTICIPANTS, CL_ENTITY_STUDENTS]:
      page_message = getPageMessage(u'students', noNL=True)
      students = callGAPIpages(service=croom.courses().students(), function=u'list',
                               page_message=page_message, items=u'students', courseId=entity)
      for student in students:
        email = student[u'profile'].get(u'emailAddress', None)
        if email:
          usersList.append(email)
  elif entityType == CL_ENTITY_CROS:
    members = entity.replace(u',', u' ').split()
    for user in members:
      usersList.append(user)
  elif entityType == CL_ENTITY_ALL_CROS:
    if not silent:
      printGettingMessage(u"Getting all CrOS devices in Google Apps account (may take some time on a large account)...\n")
    try:
      members = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices',
                              customerId=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,chromeosdevices(deviceId)')
      addMembersToUsers(usersList, u'deviceId', members)
    except:
      pass
    if not silent:
      printGettingMessage(u"done getting %s CrOS devices.\r\n" % len(users))
  return usersList
#
# Return the last column of a CSV file
#
def getEntitiesFromCSVlastColumn(filename):
  entitySet = set()
  entityList = list()
  f = openFile(filename)
  csvFile = csv.reader(f)
  for row in csvFile:
    if len(row) > 0:
      item = row[-1]
    if item not in entitySet:
      entitySet.add(item)
      entityList.append(item)
  closeFile(f)
  return entityList

#
# Typically used to map courseparticipants to students or teachers
def mapEntityType(entityType, typeMap):
  if (typeMap != None) and (entityType in typeMap):
    return typeMap[entityType]
  return entityType
#
def getEntityToModify(i, defaultEntityType=None, returnOnError=False, crosAllowed=False, typeMap=None):
  entitySelector = getChoice(i, CL_ENTITY_SELECTORS, defaultChoice=None)
  if entitySelector:
    i += 1
    if entitySelector == CL_ENTITY_SELECTOR_ALL:
      choices = CL_USER_ENTITY_SELECTOR_ALL_SUBTYPES
      if crosAllowed:
        choices += CL_CROS_ENTITY_SELECTOR_ALL_SUBTYPES
      entityType = CL_ENTITY_SELECTOR_ALL_SUBTYPES_MAP[getChoice(i, choices)]
      i += 1
      return (entityType, getUsersToModify(entityType, None))
    if entitySelector == CL_ENTITY_SELECTOR_FILE:
      filename = getString(i, OBJECT_FILE_NAME)
      i += 1
      return (entityType, getUsersToModify(CL_ENTITY_USERS, getEntitiesFromCSVlastColumn(filename)))
  choices = CL_USER_ENTITIES
  if crosAllowed:
    choices += CL_CROS_ENTITIES
  entityType = getChoice(i, choices, choiceAliases=CL_ENTITY_ALIAS_MAP, defaultChoice=None)
  if entityType:
    i += 1
  else:
    entityType = defaultEntityType
  entityType = mapEntityType(entityType, typeMap)
  if entityType:
    if entityType != CL_ENTITY_CROS:
      entity = getString(i, OBJECT_USER_ENTITY, emptyOK=True)
    else:
      entity = getString(i, OBJECT_CROS_ENTITY, emptyOK=True)
    return (entityType, getUsersToModify(entityType, entity))
  if returnOnError:
    return (None, None)
  choices = CL_USER_ENTITIES+CL_ENTITY_ALIAS_MAP.keys()+CL_ENTITY_SELECTORS
  if crosAllowed:
    choices += CL_CROS_ENTITIES
  invalidChoiceExit(i, choices)

def OAuthInfo():
  access_token = getString(3, OBJECT_ACCESS_TOKEN, optional=True)
  if not access_token:
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
  print u'Google Apps Admin: %s' % token_info.get(u'email', u'Unknown')

def doDeleteOAuth():
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  try:
    credentials.revoke_uri = oauth2client.GOOGLE_REVOKE_URI
  except AttributeError:
    sys.sdterr.write(u'{0}Authorization doesn\'t exist\n'.format(ERROR_PREFIX))
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
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e.message))
    os.remove(GC_Values[GC_OAUTH2_TXT])

class cmd_flags(object):
  def __init__(self, noLocalWebserver):
    self.short_url = True
    self.noauth_local_webserver = noLocalWebserver
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
  MISSING_CLIENT_SECRETS_MESSAGE = u"""Please configure OAuth 2.0

To make GAM run you will need to populate the {0} file found at:
{1}
with information from the APIs Console <https://console.developers.google.com>.

See the follow site for instructions:
{2}

""".format(FN_CLIENT_SECRETS_JSON, GC_Values[GC_CLIENT_SECRETS_JSON], GAM_WIKI_CREATE_CLIENT_SECRETS)

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
  try:
    FLOW = oauth2client.client.flow_from_clientsecrets(GC_Values[GC_CLIENT_SECRETS_JSON], scope=scopes)
  except oauth2client.client.clientsecrets.InvalidClientSecretsError:
    systemErrorExit(14, MISSING_CLIENT_SECRETS_MESSAGE)
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  flags = cmd_flags(noLocalWebserver=GC_Values[GC_NO_BROWSER])
  if credentials is None or credentials.invalid or incremental_auth:
    http = httplib2.Http(ca_certs=GC_Values[GC_CACERT_PEM],
                         disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    GC_Values[GC_EXTRA_ARGS][u'prettyPrint'] = True
    try:
      credentials = oauth2client.tools.run_flow(flow=FLOW, storage=storage, flags=flags, http=http)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()

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
# gam batch <FileName>|- [charset <Charset>]
#
def doBatch():
  import shlex
  filename = getString(2, OBJECT_FILE_NAME)
  if getChoice(3, CHARSET_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    encoding = getString(4, OBJECT_CHAR_SET)
  else:
    encoding = GC_Values[GC_CHARSET]
  f = openFile(filename)
  batchFile = UTF8Recoder(f, encoding)
  items = []
  cmdCount = 0
  for line in batchFile:
    argv = shlex.split(line)
    if len(argv) > 0:
      cmd = argv[0].strip()
      if (not cmd) or cmd.startswith(u'#') or ((len(argv) == 1) and (cmd != COMMIT_BATCH_CMD)):
        continue
      if cmd == GAM_CMD:
        items.append([arg.encode(sys.getfilesystemencoding()) for arg in argv[1:]])
        cmdCount += 1
      elif cmd == COMMIT_BATCH_CMD:
        items.append(argv)
      else:
        sys.stderr.write(u'{0}"{1}" is not a valid gam command\n'.format(ERROR_PREFIX, line.strip()))
  closeFile(f)
  run_batch(items, cmdCount)
#
# gam csv (-|<FileName>) [charset <Charset>] [matchfield <FieldName> <PythonRegularExpression>] gam <GAM argument list>
#
def doCSV():
  filename = getString(2, OBJECT_FILE_NAME)
  if getChoice(3, CHARSET_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    encoding = getString(4, OBJECT_CHAR_SET)
    i = 5
  else:
    encoding = GC_Values[GC_CHARSET]
    i = 3
  f = openFile(filename)
  csvFile = UnicodeDictReader(f, encoding=encoding)
  if getChoice(i, MATCHFIELD_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    i += 1
    matchField = getString(i, OBJECT_FIELD_NAME)
    i += 1
    matchPattern = getREPattern(i)
    i += 1
  else:
    matchField = None
  getChoice(i, GAM_ARGUMENT_PRESENT, mapChoice=True)
  i += 1
  optionalSubs = {}
  GAM_argv = []
  GAM_argvI = 0
  while i < len(sys.argv):
    arg = sys.argv[i]
    if arg[0] != '~':
      GAM_argv.append(arg.encode(sys.getfilesystemencoding()))
    else:
      fieldName = arg[1:]
      if fieldName in csvFile.fieldnames:
        optionalSubs[GAM_argvI] = fieldName
        GAM_argv.append(fieldName)
      else:
        csvFieldErrorExit(i, fieldName, csvFile.fieldnames)
    i += 1
    GAM_argvI += 1
  items = []
  for row in csvFile:
    if matchField and ((matchField not in row) or (not matchPattern.search(row[matchField]))):
      continue
    argv = GAM_argv[:]
    for GAM_argvI, fieldName in optionalSubs.iteritems():
      if row[fieldName]:
        argv[GAM_argvI] = row[fieldName].encode(sys.getfilesystemencoding())
      else:
        argv[GAM_argvI] = u''
    items.append(argv)
  closeFile(f)
  run_batch(items, len(items))
#
# Process GAM command
#
def ProcessGAMCommand(args, processGamCfg=True):
  if args != sys.argv:
    sys.argv = args[:]
  savedStdout = sys.stdout
  savedStderr = sys.stderr
  try:
    if getChoice(1, LOOP_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
      doLoop(processGamCfg=True)
      sys.exit(0)
    if processGamCfg and (not SetGlobalVariables()):
      sys.exit(0)
    if getChoice(1, LOOP_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
      doLoop(processGamCfg=False)
      sys.exit(0)
    if len(sys.argv) == 1:
      showUsage()
      sys.exit(0)
    command = getArgument(1)
    if command == u'batch':
      doBatch()
      sys.exit(0)
    elif command == 'csv':
      doCSV()
      sys.exit(0)
    elif command == u'version':
      doGAMVersion()
      sys.exit(0)
    elif command == u'create':
      argument = getArgument(2)
      if argument == u'user':
        doCreateUser()
      elif argument == u'group':
        doCreateGroup()
      elif argument in [u'nickname', u'alias']:
        doCreateAlias()
      elif argument in [u'org', 'ou']:
        doCreateOrg()
      elif argument == u'resource':
        doCreateResource()
      elif argument in [u'verify', u'verification']:
        doSiteVerifyShow()
      elif argument in [u'schema']:
        doCreateOrUpdateUserSchema(u'insert')
      elif argument in [u'course', u'class']:
        doCreateCourse()
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'update':
      argument = getArgument(2)
      if argument == u'user':
        doUpdateSingleUser()
      elif argument == u'group':
        doUpdateGroup()
      elif argument in [u'nickname', u'alias']:
        doUpdateAlias()
      elif argument in [u'ou', u'org']:
        doUpdateOrg()
      elif argument == u'resource':
        doUpdateResourceCalendar()
      elif argument == u'domain':
        doUpdateDomain()
      elif argument == u'cros':
        doUpdateSingleCros()
      elif argument == u'mobile':
        doUpdateMobile()
      elif argument in [u'notification', u'notifications']:
        doUpdateNotification()
      elif argument in [u'verify', u'verification']:
        doSiteVerifyAttempt()
      elif argument in [u'schema', u'schemas']:
        doCreateOrUpdateUserSchema(u'update')
      elif argument in [u'course', u'class']:
        doUpdateCourse()
      elif argument in [u'printer', u'print']:
        doUpdatePrinter()
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'info':
      argument = getArgument(2)
      if argument == u'user':
        doGetUserInfo()
      elif argument == u'group':
        doGetGroupInfo()
      elif argument in [u'nickname', u'alias']:
        doGetAliasInfo()
      elif argument == u'domain':
        doGetDomainInfo()
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
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'delete':
      argument = getArgument(2)
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
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'undelete':
      argument = getArgument(2)
      if argument == u'user':
        doUndeleteUser()
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'audit':
      argument = getArgument(2)
      if argument == u'monitor':
        argument = getArgument(3)
        if argument == u'create':
          doCreateMonitor()
        elif argument == u'list':
          doShowMonitors()
        elif argument == u'delete':
          doDeleteMonitor()
        else:
          unknownArgumentExit(3)
      elif argument == u'activity':
        argument = getArgument(3)
        if argument == u'request':
          doRequestActivity()
        elif argument == u'status':
          doStatusActivityRequests()
        elif argument == u'download':
          doDownloadActivityRequest()
        elif argument == u'delete':
          doDeleteActivityRequest()
        else:
          unknownArgumentExit(3)
      elif argument == u'export':
        argument = getArgument(3)
        if argument == u'status':
          doStatusExportRequests()
        elif argument == u'watch':
          doWatchExportRequest()
        elif argument == u'download':
          doDownloadExportRequest()
        elif argument == u'request':
          doRequestExport()
        elif argument == u'delete':
          doDeleteExport()
        else:
          unknownArgumentExit(3)
      elif argument == u'uploadkey':
        doUploadAuditKey()
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'print':
      argument = getArgument(2)
      if argument == u'users':
        doPrintUsers()
      elif argument == u'nicknames' or argument == u'aliases':
        doPrintAliases()
      elif argument == u'groups':
        doPrintGroups()
      elif argument in [u'group-members', u'groups-members']:
        doPrintGroupMembers()
      elif argument in [u'orgs', u'ous']:
        doPrintOrgs()
      elif argument == u'resources':
        doPrintResources()
      elif argument == u'cros':
        doPrintCrosDevices()
      elif argument == u'mobile':
        doPrintMobileDevices()
      elif argument in [u'license', u'licenses', u'licence', u'licences']:
        doPrintLicenses()
      elif argument in [u'token', u'tokens']:
        doPrintTokens()
      elif argument in [u'schema', u'schemas']:
        doPrintUserSchemas()
      elif argument in [u'courses', u'classes']:
        doPrintCourses()
      elif argument in [u'course-participants', u'class-participants']:
        doPrintCourseParticipants()
      elif argument in [u'printers']:
        doPrintPrinters()
      elif argument in [u'printjobs']:
        doPrintPrintJobs()
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command in [u'oauth', u'oauth2']:
      argument = getArgument(2)
      if argument in [u'request', u'create']:
        doRequestOAuth()
      elif argument == u'info':
        OAuthInfo()
      elif argument in [u'delete', u'revoke']:
        doDeleteOAuth()
      else:
        unknownArgumentExit(2)
      sys.exit(0)
    elif command == u'calendar':
      argument = getArgument(3)
      if argument == u'showacl':
        doCalendarShowACL()
      elif argument == u'add':
        doCalendarAddACL()
      elif argument in [u'del', u'delete']:
        doCalendarDeleteACL()
      elif argument == u'update':
        doCalendarUpdateACL()
      elif argument == u'wipe':
        doCalendarWipeEvents()
      elif argument == u'addevent':
        doCalendarAddEvent()
      else:
        unknownArgumentExit(3)
      sys.exit(0)
    elif command == u'printer':
      argument = getArgument(3)
      if argument == u'showacl':
        doPrinterShowACL()
      elif argument == u'add':
        doPrinterAddACL()
      elif argument in [u'del', u'delete', u'remove']:
        doPrinterDelACL()
      elif argument == u'register':
        doPrinterRegister()
      else:
        unknownArgumentExit(3)
      sys.exit(0)
    elif command == u'printjob':
      argument = getArgument(3)
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
        unknownArgumentExit(3)
      sys.exit(0)
    elif command == u'report':
      showReport()
      sys.exit(0)
    elif command == u'whatis':
      doWhatIs()
      sys.exit(0)
    elif command in [u'course', u'class']:
      argument = getArgument(3)
      if argument in [u'add', u'create']:
        doAddCourseParticipants()
      elif argument in [u'del', u'delete', u'remove']:
        doDeleteCourseParticipants()
      elif argument == u'sync':
        doSyncCourseParticipants()
      else:
        unknownArgumentExit(3)
      sys.exit(0)
    entityType, entityList = getEntityToModify(1, returnOnError=True, crosAllowed=True)
    if not entityType:
      unknownArgumentExit(1)
    command = getArgument(3)
    if command == u'print':
      for user in entityList:
        print user
        sys.exit(0)
    if (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(entityList) > GC_Values[GC_AUTO_BATCH_MIN]):
      items = []
      entityName = u'user' if entityType not in [CL_ENTITY_CROS, CL_ENTITY_ALL_CROS] else u'cros'
      for user in entityList:
        items.append([entityName, user] + sys.argv[3:])
      run_batch(items, len(items))
      sys.exit(0)
    if entityType in [CL_ENTITY_CROS, CL_ENTITY_ALL_CROS]:
      if command == u'update':
        doUpdateCros(entityList)
      else:
        unknownArgumentExit(3)
      sys.exit(0)
    if command == u'transfer':
      transferWhat = getArgument(4)
      if transferWhat == u'drive':
        transferDriveFiles(entityList)
      elif transferWhat == u'seccals':
        transferSecCals(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'show':
      readWhat = getArgument(4)
      if readWhat in [u'labels', u'label']:
        showLabels(entityList)
      elif readWhat == u'profile':
        showProfile(entityList)
      elif readWhat == u'calendars':
        showCalendars(entityList)
      elif readWhat == u'calsettings':
        showCalSettings(entityList)
      elif readWhat == u'drivesettings':
        showDriveSettings(entityList)
      elif readWhat == u'drivefileacl':
        showDriveFileACL(entityList)
      elif readWhat == u'filelist':
        showDriveFiles(entityList)
      elif readWhat == u'filetree':
        showDriveFileTree(entityList)
      elif readWhat == u'fileinfo':
        showDriveFileInfo(entityList)
      elif readWhat == u'sendas':
        showSendAs(entityList)
      elif readWhat == u'gmailprofile':
        showGmailProfile(entityList)
      elif readWhat in [u'sig', u'signature']:
        getSignature(entityList)
      elif readWhat == u'forward':
        getForward(entityList)
      elif readWhat in [u'pop', u'pop3']:
        getPop(entityList)
      elif readWhat in [u'imap', u'imap4']:
        getImap(entityList)
      elif readWhat == u'vacation':
        getVacation(entityList)
      elif readWhat in [u'delegate', u'delegates']:
        getDelegates(entityList)
      elif readWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doGetBackupCodes(entityList)
      elif readWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
        doGetASPs(entityList)
      elif readWhat in [u'token', u'tokens', u'oauth', u'3lo']:
        doGetTokens(entityList)
      elif readWhat in [u'driveactivity']:
        doDriveActivity(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'trash':
      trashWhat = getArgument(4)
      if trashWhat in [u'message', u'messages']:
        doDeleteMessages(entityList, u'trash')
      else:
        unknownArgumentExit(4)
    elif command == u'spam':
      spamWhat = getArgument(4)
      if spamWhat in [u'message', u'messages']:
        doSpamMessages(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'delete' or command == u'del':
      delWhat = getArgument(4)
      if delWhat == u'delegate':
        deleteDelegate(entityList)
      elif delWhat == u'calendar':
        deleteCalendar(entityList)
      elif delWhat == u'label':
        doDeleteLabel(entityList)
      elif delWhat in [u'message', u'messages']:
        doDeleteMessages(entityList, u'delete')
      elif delWhat == u'photo':
        deletePhoto(entityList)
      elif delWhat in [u'license', u'licence']:
        doLicense(entityList, u'delete')
      elif delWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doDelBackupCodes(entityList)
      elif delWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
        doDelASP(entityList)
      elif delWhat in [u'token', u'tokens', u'oauth', u'3lo']:
        doDelTokens(entityList)
      elif delWhat in [u'group', u'groups']:
        doRemoveUsersGroups(entityList)
      elif delWhat in [u'alias', u'aliases']:
        doRemoveUsersAliases(entityList)
      elif delWhat in [u'emptydrivefolders']:
        deleteEmptyDriveFolders(entityList)
      elif delWhat in [u'drivefile']:
        deleteDriveFile(entityList)
      elif delWhat in [u'drivefileacl', u'drivefileacls']:
        delDriveFileACL(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'undelete':
      undelWhat = getArgument(4)
      if undelWhat == u'drivefile':
        deleteDriveFile(entityList, function=u'untrash')
      else:
        unknownArgumentExit(4)
    elif command == u'add':
      addWhat = getArgument(4)
      if addWhat == u'calendar':
        addCalendar(entityList)
      elif addWhat == u'drivefile':
        createDriveFile(entityList)
      elif addWhat in [u'license', u'licence']:
        doLicense(entityList, u'insert')
      elif addWhat in [u'drivefileacl', u'drivefileacls']:
        addDriveFileACL(entityList)
      elif addWhat in [u'label', u'labels']:
        doLabel(entityList, 5)
      else:
        unknownArgumentExit(4)
    elif command == u'update':
      updateWhat = getArgument(4)
      if updateWhat == u'calendar':
        updateCalendar(entityList)
      elif updateWhat == u'calattendees':
        changeCalendarAttendees(entityList)
      elif updateWhat == u'photo':
        doPhoto(entityList)
      elif updateWhat in [u'license', u'licence']:
        doLicense(entityList, u'patch')
      elif updateWhat == u'user':
        doUpdateUser(entityList)
      elif updateWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
        doGenBackupCodes(entityList)
      elif updateWhat in [u'drivefile']:
        doUpdateDriveFile(entityList)
      elif updateWhat in [u'drivefileacls', u'drivefileacl']:
        updateDriveFileACL(entityList)
      elif updateWhat in [u'label', u'labels']:
        renameLabels(entityList)
      elif updateWhat in [u'labelsettings']:
        updateLabels(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'create':
      createWhat = getArgument(4)
      if createWhat == u'calendar':
        createCalendar(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'modify':
      modifyWhat = getArgument(4)
      if modifyWhat == u'calendar':
        modifyCalendar(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'info':
      infoWhat = getArgument(4)
      if infoWhat == u'calendar':
        infoCalendar(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'remove':
      removeWhat = getArgument(4)
      if removeWhat == u'calendar':
        removeCalendar(entityList)
      else:
        unknownArgumentExit(4)
    elif command in [u'deprov', u'deprovision']:
      doDeprovUser(entityList)
    elif command == u'get':
      getWhat = getArgument(4)
      if getWhat == u'photo':
        getPhoto(entityList)
      elif getWhat == u'drivefile':
        downloadDriveFile(entityList)
      else:
        unknownArgumentExit(4)
    elif command == u'profile':
      doProfile(entityList)
    elif command == u'imap':
      doImap(entityList)
    elif command in [u'pop', u'pop3']:
      doPop(entityList)
    elif command == u'sendas':
      doSendAs(entityList)
    elif command == u'language':
      doLanguage(entityList)
    elif command in [u'utf', u'utf8', u'utf-8', u'unicode']:
      doUTF(entityList)
    elif command == u'pagesize':
      doPageSize(entityList)
    elif command == u'shortcuts':
      doShortCuts(entityList)
    elif command == u'arrows':
      doArrows(entityList)
    elif command == u'snippets':
      doSnippets(entityList)
    elif command == u'label':
      doLabel(entityList, 4)
    elif command == u'filter':
      doFilter(entityList)
    elif command == u'forward':
      doForward(entityList)
    elif command in [u'sig', u'signature']:
      doSignature(entityList)
    elif command == u'vacation':
      doVacation(entityList)
    elif command == u'webclips':
      doWebClips(entityList)
    elif command in [u'delegate', u'delegates']:
      doDelegates(entityList)
    else:
      unknownArgumentExit(3)
    sys.exit(0)
  except IndexError:
    missingArgumentExit(u'additional arguments')
  except KeyboardInterrupt:
    sysExitRC = 50
  except socket.error, e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sysExitRC = 3
  except MemoryError:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, MESSAGE_GAM_OUT_OF_MEMORY))
    sysExitRC = 99
  except IOError as e:
    sys.stderr.write(u'{0}{1}\n'.format(ERROR_PREFIX, e))
    sysExitRC = 3
  except SystemExit as sysExitRC:
    pass
  except Exception as e:
    import traceback
    traceback.print_exc(file=savedStderr)
    sysExitRC = 1
  if sys.stdout != savedStdout:
    sys.stdout.close()
    sys.stdout = savedStdout
  if sys.stderr != savedStderr:
    sys.stderr.close()
    sys.stderr = savedStderr
  return sysExitRC
#
# gam loop (-|<FileName>) [charset <String>] [matchfield <FieldName> <PythonRegularExpression>] gam <GAM argument list>
#
def doLoop(processGamCfg=True):
  filename = getString(2, OBJECT_FILE_NAME)
  if getChoice(3, CHARSET_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    encoding = getString(4, OBJECT_CHAR_SET)
    i = 5
  else:
    encoding = GC_Values.get(GC_CHARSET, u'ascii')
    i = 3
  f = openFile(filename)
  csvFile = UnicodeDictReader(f, encoding=encoding)
  if getChoice(i, MATCHFIELD_ARGUMENT_PRESENT, defaultChoice=False, mapChoice=True):
    i += 1
    matchField = getString(i, OBJECT_FIELD_NAME)
    i += 1
    matchPattern = getREPattern(i)
    i += 1
  else:
    matchField = None
  getChoice(i, GAM_ARGUMENT_PRESENT, mapChoice=True)
  i += 1
  choice = getArgument(i)
  if choice == LOOP_CMD:
    usageErrorExit(i, u'Command can not be nested.')
  if processGamCfg:
    if choice in [REDIRECT_CMD, SELECT_CMD, CONFIG_CMD]:
# gam loop ... gam redirect|select|config ... process gam.cfg on each iteration
      nextProcessGamCfg = True
    else:
# gam loop ... gam !redirect|select|config ... process gam.cfg on first iteration only
      nextProcessGamCfg = False
  else:
    if choice in [REDIRECT_CMD, SELECT_CMD, CONFIG_CMD]:
# gam redirect|select|config ... loop ... gam redirect|select|config ... process gam.cfg on each iteration
      nextProcessGamCfg = processGamCfg = True
    else:
# gam redirect|select|config ... loop ... gam !redirect|select|config ... no further processing of gam.cfg
      nextProcessGamCfg = False
  optionalSubs = {}
  GAM_argv = [sys.argv[0]]
  GAM_argvI = len(GAM_argv)
  while i < len(sys.argv):
    arg = sys.argv[i]
    if arg[0] != u'~':
      GAM_argv.append(arg.encode(sys.getfilesystemencoding()))
    else:
      fieldName = arg[1:]
      if fieldName in csvFile.fieldnames:
        optionalSubs[GAM_argvI] = fieldName
        GAM_argv.append(fieldName)
      else:
        csvFieldErrorExit(i, fieldName, csvFile.fieldnames)
    i += 1
    GAM_argvI += 1
  for row in csvFile:
    if matchField and ((matchField not in row) or (not matchPattern.search(row[matchField]))):
      continue
    argv = GAM_argv[:]
    for GAM_argvI, fieldName in optionalSubs.iteritems():
      if row[fieldName]:
        argv[GAM_argvI] = row[fieldName].encode(sys.getfilesystemencoding())
      else:
        argv[GAM_argvI] = u''
    ProcessGAMCommand(argv, processGamCfg=processGamCfg)
    processGamCfg = nextProcessGamCfg
  closeFile(f)
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
