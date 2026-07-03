"""GAM shared constants.

This module provides constants that are shared across cmd/ modules. These
constants are defined here (rather than in gam/__init__.py) to avoid circular
import issues—gam/__init__.py imports from cmd/ modules, so cmd/ modules
cannot safely import from gam at module level.
"""

import re
import string

# Time formats
IS08601_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%:z'
RFC2822_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S %z'

# Application name
GIT_USER = 'GAM-team'
GAM = 'GAM'
GAM_PROJECT_CREATION = 'GAM Project Creation'
GAM_PROJECT_CREATION_CLIENT_ID = '297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com'

# Byte sizes
ONE_KILO_BYTES = 1024
ONE_MEGA_BYTES = ONE_KILO_BYTES * ONE_KILO_BYTES
ONE_GIGA_BYTES = ONE_KILO_BYTES * ONE_MEGA_BYTES
ONE_TERA_BYTES = ONE_KILO_BYTES * ONE_GIGA_BYTES

# Day names
DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Time constants
MAX_LOCAL_GOOGLE_TIME_OFFSET = 30

# Character sets
LOWERNUMERIC_CHARS = string.ascii_lowercase + string.digits
ALPHANUMERIC_CHARS = LOWERNUMERIC_CHARS + string.ascii_uppercase
PASSWORD_SAFE_CHARS = ALPHANUMERIC_CHARS + '!#$%&()*-./:;<=>?@[\\\\]^_{|}~'

# Google Meet
GOOGLE_MEETID_PATTERN = re.compile(r'^[a-z]{3}-[a-z]{4}-[a-z]{3}$')
GOOGLE_MEETID_FORMAT_REQUIRED = 'abc-defg-hij'
GOOGLE_TIMECHECK_LOCATION = 'admin.googleapis.com'

# Drive constants
MY_DRIVE = 'My Drive'
TEAM_DRIVE = 'Drive'
ROOT = 'root'

# Access options
ADMIN_ACCESS_OPTIONS = {'adminaccess', 'asadmin'}
OWNER_ACCESS_OPTIONS = {'owneraccess', 'asowner'}

# Choice maps
PROJECTION_CHOICE_MAP = {'basic': 'BASIC', 'full': 'FULL'}

# Google API MIME types
APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'

# Queries
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
AND_ME_IN_OWNERS = " and " + ME_IN_OWNERS
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "
AND_NOT_ME_IN_OWNERS = " and " + NOT_ME_IN_OWNERS
ANY_FOLDERS = "mimeType = '" + MIMETYPE_GA_FOLDER + "'"
NON_TRASHED = "trashed = false"
WITH_PARENTS = "'{0}' in parents"
ANY_NON_TRASHED_WITH_PARENTS = "trashed = false and '{0}' in parents"
ANY_NON_TRASHED_FOLDER_NAME = "mimeType = '" + MIMETYPE_GA_FOLDER + "' and name = '{0}' and trashed = false"
MY_NON_TRASHED_FOLDER_NAME = ME_IN_OWNERS_AND + ANY_NON_TRASHED_FOLDER_NAME
MY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS = ME_IN_OWNERS_AND + "mimeType = '" + MIMETYPE_GA_FOLDER + "' and name = '{0}' and trashed = false and '{1}' in parents"
ANY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS = "mimeType = '" + MIMETYPE_GA_FOLDER + "' and name = '{0}' and trashed = false and '{1}' in parents"
AND_NOT_SHORTCUT = " and mimeType != '" + MIMETYPE_GA_SHORTCUT + "'"

# Program return codes
UNKNOWN_ERROR_RC = 1
USAGE_ERROR_RC = 2
SOCKET_ERROR_RC = 3
GOOGLE_API_ERROR_RC = 4
NETWORK_ERROR_RC = 5
FILE_ERROR_RC = 6
MEMORY_ERROR_RC = 7
KEYBOARD_INTERRUPT_RC = 8
HTTP_ERROR_RC = 9
SCOPES_NOT_AUTHORIZED_RC = 10
DATA_ERROR_RC = 11
API_ACCESS_DENIED_RC = 12
CONFIG_ERROR_RC = 13
SYSTEM_ERROR_RC = 14
NO_SCOPES_FOR_API_RC = 15
CLIENT_SECRETS_JSON_REQUIRED_RC = 16
OAUTH2SERVICE_JSON_REQUIRED_RC = 16
OAUTH2_TXT_REQUIRED_RC = 16
INVALID_JSON_RC = 17
JSON_ALREADY_EXISTS_RC = 17
AUTHENTICATION_TOKEN_REFRESH_ERROR_RC = 18
HARD_ERROR_RC = 19
# Information
ENTITY_IS_A_USER_RC = 20
ENTITY_IS_A_USER_ALIAS_RC = 21
ENTITY_IS_A_GROUP_RC = 22
ENTITY_IS_A_GROUP_ALIAS_RC = 23
ENTITY_IS_AN_UNMANAGED_ACCOUNT_RC = 24
ORGUNIT_NOT_EMPTY_RC = 25
USER_SUSPENDED_RC = 26
CHECK_USER_GROUPS_ERROR_RC = 29
ORPHANS_COLLECTED_RC = 30
# Warnings/Errors
ACTION_FAILED_RC = 50
ACTION_NOT_PERFORMED_RC = 51
INVALID_ENTITY_RC = 52
BAD_REQUEST_RC = 53
ENTITY_IS_NOT_UNIQUE_RC = 54
DATA_NOT_AVALIABLE_RC = 55
ENTITY_DOES_NOT_EXIST_RC = 56
ENTITY_DUPLICATE_RC = 57
ENTITY_IS_NOT_AN_ALIAS_RC = 58
ENTITY_IS_UKNOWN_RC = 59
NO_ENTITIES_FOUND_RC = 60
INVALID_DOMAIN_RC = 61
INVALID_DOMAIN_VALUE_RC = 62
INVALID_TOKEN_RC = 63
JSON_LOADS_ERROR_RC = 64
MULTIPLE_DELETED_USERS_FOUND_RC = 65
MULTIPLE_PROJECT_FOLDERS_FOUND_RC = 65
STDOUT_STDERR_ERROR_RC = 66
INSUFFICIENT_PERMISSIONS_RC = 67
REQUEST_COMPLETED_NO_RESULTS_RC = 71
REQUEST_NOT_COMPLETED_RC = 72
SERVICE_NOT_APPLICABLE_RC = 73
TARGET_DRIVE_SPACE_ERROR_RC = 74
USER_REQUIRED_TO_CHANGE_PASSWORD_ERROR_RC = 75
USER_SUSPENDED_ERROR_RC = 76
NO_CSV_DATA_TO_UPLOAD_RC = 77
NO_SA_ACCESS_CONTEXT_MANAGER_EDITOR_ROLE_RC = 78
ACCESS_POLICY_ERROR_RC = 79
YUBIKEY_CONNECTION_ERROR_RC = 80
YUBIKEY_INVALID_KEY_TYPE_RC = 81
YUBIKEY_INVALID_SLOT_RC = 82
YUBIKEY_INVALID_PIN_RC = 83
YUBIKEY_APDU_ERROR_RC = 84
YUBIKEY_VALUE_ERROR_RC = 85
YUBIKEY_MULTIPLE_CONNECTED_RC = 86
YUBIKEY_NOT_FOUND_RC = 87

# Building address field map
BUILDING_ADDRESS_FIELD_MAP = {
  'address': 'addressLines',
  'addresslines': 'addressLines',
  'administrativearea': 'administrativeArea',
  'city': 'locality',
  'country': 'regionCode',
  'language': 'languageCode',
  'languagecode': 'languageCode',
  'locality': 'locality',
  'postalcode': 'postalCode',
  'regioncode': 'regionCode',
  'state': 'administrativeArea',
  'sublocality': 'sublocality',
  'zipcode': 'postalCode',
}
