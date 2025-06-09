# -*- coding: utf-8 -*-

# Copyright (C) 2025 Ross Scroggs All Rights Reserved.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""GAM gam.cfg variables

"""

import os

TRUE = 'true'
FALSE = 'false'
DEFAULT_CHARSET = 'utf-8'
MY_CUSTOMER = 'my_customer'
NEVER = 'Never'
TLS_CHOICE_MAP = {
  '': '',
  'tlsv1_2': 'TLSv1_2', 'tlsv1.2': 'TLSv1_2',
  'tlsv1_3': 'TLSv1_3', 'tlsv1.3': 'TLSv1_3',
  }

FN_CACERTS_PEM = 'cacerts.pem'
FN_CLIENT_SECRETS_JSON = 'client_secrets.json'
FN_EXTRA_ARGS_TXT = 'extra-args.txt'
FN_OAUTH2_TXT = 'oauth2.txt'
FN_OAUTH2SERVICE_JSON = 'oauth2service.json'

# Global variables defined in gam.cfg

# The following XXX constants are the names of the items in gam.cfg
# When retrieving lists of Google Drive activities from API, how many should be retrieved in each chunk
ACTIVITY_MAX_RESULTS = 'activity_max_results'
# Admin email address, required when enable_dasa is true, overrides oauth2.txt value otherwise
ADMIN_EMAIL = 'admin_email'
# Check if API calls rate exceeds limit
API_CALLS_RATE_CHECK = 'api_calls_rate_check'
# API calls per 100 seconds limit
API_CALLS_RATE_LIMIT = 'api_calls_rate_limit'
# API calls tries limit
API_CALLS_TRIES_LIMIT = 'api_calls_tries_limit'
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, do not automatically generate gam batch commands
AUTO_BATCH_MIN = 'auto_batch_min'
# When bailing on internal errors, how many total tries should be performed
BAIL_ON_INTERNAL_ERROR_TRIES = 'bail_on_internal_error_tries'
# When processing items in batches, how many should be processed in each batch
BATCH_SIZE = 'batch_size'
# Location of cacerts.pem for API calls
CACERTS_PEM = 'cacerts_pem'
# GAM cache directory
CACHE_DIR = 'cache_dir'
# GAM cache discovery only. If no_cache is False, only API discovery calls will be cached
CACHE_DISCOVERY_ONLY = 'cache_discovery_only'
# Channel custmerId from gam.cfg
CHANNEL_CUSTOMER_ID = 'channel_customer_id'
# Character set of batch, csv, data files
CHARSET = 'charset'
# When retrieving lists of Google Classroom items from API, how many should be retrieved in each chunk
CLASSROOM_MAX_RESULTS = 'classroom_max_results'
# Path to client_secrets.json
CLIENT_SECRETS_JSON = 'client_secrets_json'
# Allowed clock skew in seconds
CLOCK_SKEW_IN_SECONDS = 'clock_skew_in_seconds'
# Command logging filename
CMDLOG = 'cmdlog'
# Bogus Command logging maximum number of backup log files
CMDLOG_MAX__BACKUPS = 'cmdlog_max__backups'
# Command logging maximum number of backup log files
CMDLOG_MAX_BACKUPS = 'cmdlog_max_backups'
# Command logging max kilo bytes per log file
CMDLOG_MAX_KILO_BYTES = 'cmdlog_max_kilo_bytes'
# GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
CONFIG_DIR = 'config_dir'
# When retrieving lists of Google Contacts from API, how many should be retrieved in each chunk
CONTACT_MAX_RESULTS = 'contact_max_results'
# Column delimiter in CSV input file
CSV_INPUT_COLUMN_DELIMITER = 'csv_input_column_delimiter'
# No escape character in CSV input file
CSV_INPUT_NO_ESCAPE_CHAR = 'csv_input_no_escape_char'
# Quote character in CSV input file
CSV_INPUT_QUOTE_CHAR = 'csv_input_quote_char'
# Filter for input column values
CSV_INPUT_ROW_FILTER = 'csv_input_row_filter'
# Mode (and|or) for input column values
CSV_INPUT_ROW_FILTER_MODE = 'csv_input_row_filter_mode'
# Filter for input column drop values
CSV_INPUT_ROW_DROP_FILTER = 'csv_input_row_drop_filter'
# Mode (and|or) for input column drop values
CSV_INPUT_ROW_DROP_FILTER_MODE = 'csv_input_row_drop_filter_mode'
# Limit number of input rows
CSV_INPUT_ROW_LIMIT = 'csv_input_row_limit'
# Convert newlines in text fields to "\n" in CSV output file
CSV_OUTPUT_CONVERT_CR_NL = 'csv_output_convert_cr_nl'
# Column delimiter in CSV output file
CSV_OUTPUT_COLUMN_DELIMITER = 'csv_output_column_delimiter'
# No escape character in CSV output file
CSV_OUTPUT_NO_ESCAPE_CHAR = 'csv_output_no_escape_char'
# Field list delimiter in CSV output file
CSV_OUTPUT_FIELD_DELIMITER = 'csv_output_field_delimiter'
# Filter for output column headers
CSV_OUTPUT_HEADER_FILTER = 'csv_output_header_filter'
# Filter for output column headers to drop
CSV_OUTPUT_HEADER_DROP_FILTER = 'csv_output_header_drop_filter'
# Force output column headers
CSV_OUTPUT_HEADER_FORCE = 'csv_output_header_force'
# Orde output column headers
CSV_OUTPUT_HEADER_ORDER = 'csv_output_header_order'
# Line terminator in CSV output file
CSV_OUTPUT_LINE_TERMINATOR = 'csv_output_line_terminator'
# Quote character in CSV output file
CSV_OUTPUT_QUOTE_CHAR = 'csv_output_quote_char'
# Filter for output column values
CSV_OUTPUT_ROW_FILTER = 'csv_output_row_filter'
# Mode (and|or) for output column values
CSV_OUTPUT_ROW_FILTER_MODE = 'csv_output_row_filter_mode'
# Filter for output column drop values
CSV_OUTPUT_ROW_DROP_FILTER = 'csv_output_row_drop_filter'
# Mode (and|or) for output column drop values
CSV_OUTPUT_ROW_DROP_FILTER_MODE = 'csv_output_row_drop_filter_mode'
# Limit number of output rows
CSV_OUTPUT_ROW_LIMIT = 'csv_output_row_limit'
# Output sort headers
CSV_OUTPUT_SORT_HEADERS = 'csv_output_sort_headers'
# Column header subfield name delimiter in CSV output file
CSV_OUTPUT_SUBFIELD_DELIMITER = 'csv_output_subfield_delimiter'
# Add timestamp column to CSV output file
CSV_OUTPUT_TIMESTAMP_COLUMN = 'csv_output_timestamp_column'
# Output rows for users even if they do not have the print object (delegate, filters, ...)
CSV_OUTPUT_USERS_AUDIT = 'csv_output_users_audit'
# custmerId from gam.cfg or retrieved from Google
CUSTOMER_ID = 'customer_id'
# If debug_level > 0: extra_args['prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
DEBUG_LEVEL = 'debug_level'
# When retrieving lists of ChromeOS devices from API, how many should be retrieved in each chunk
DEVICE_MAX_RESULTS = 'device_max_results'
# Domain obtained from gam.cfg or oauth2.txt
DOMAIN = 'domain'
# Google Drive download directory
DRIVE_DIR = 'drive_dir'
# When retrieving lists of Drive files/folders from API, how many should be retrieved in each chunk
DRIVE_MAX_RESULTS = 'drive_max_results'
# Use Drive V3 beta
DRIVE_V3_BETA = 'drive_v3_beta'
# Use Drive V3 ntive names
DRIVE_V3_NATIVE_NAMES = 'drive_v3_native_names'
# When processing email messages in batches, how many should be processed in each batch
EMAIL_BATCH_SIZE = 'email_batch_size'
# Enable Delegated Admin Service Account
ENABLE_DASA = 'enable_dasa'
# Enable Cloud Session Reauthentication by borrowing a RAPT token from gcloud command
ENABLE_GCLOUD_REAUTH = 'enable_gcloud_reauth'
# Value for enforceExpansiveAccess for commands that delete or update drive file ACLs/permissions.
ENFORCE_EXPANSIVE_ACCESS = 'enforce_expansive_access'
# When retrieving lists of calendar events from API, how many should be retrieved in each chunk
EVENT_MAX_RESULTS = 'event_max_results'
# Path to extra_args.txt
EXTRA_ARGS = 'extra_args'
# Gmail CSE certificates directory
GMAIL_CSE_INCERT_DIR = 'gmail_cse_incert_dir'
# Gmail CSE KACL wrapped key files
GMAIL_CSE_INKEY_DIR = 'gmail_cse_inkey_dir'
# When processing items in batches, how many seconds should GAM wait between batches
INTER_BATCH_WAIT = 'inter_batch_wait'
# When retrieving lists of licenses from API, how many should be retrieved in each chunk
LICENSE_MAX_RESULTS = 'license_max_results'
# License SKUs to process
LICENSE_SKUS = 'license_skus'
# Use Meet V2 beta
MEET_V2_BETA = 'meet_v2_beta'
# When retrieving lists of Google Group members from API, how many should be retrieved in each chunk
MEMBER_MAX_RESULTS = 'member_max_results'
# CI API Group members max page size when view=BASIC
MEMBER_MAX_RESULTS_CI_BASIC = 'member_max_results_ci_basic'
# CI API Group members max page size when view=FULL
MEMBER_MAX_RESULTS_CI_FULL = 'member_max_results_ci_full'
# When deleting or modifying Gmail messages, how many should be processed in each batch
MESSAGE_BATCH_SIZE = 'message_batch_size'
# When retrieving lists of Gmail messages from API, how many should be retrieved in each chunk
MESSAGE_MAX_RESULTS = 'message_max_results'
# When retrieving lists of Mobile devices from API, how many should be retrieved in each chunk
MOBILE_MAX_RESULTS = 'mobile_max_results'
# Number of parallel multiprocess pool.apply_async calls; -1: no limit, 0: NUM_THREADS, >0: specific limit
MULTIPROCESS_POOL_LIMIT = 'multiprocess_pool_limit'
# Value to substitute for NEVER_TIME
NEVER_TIME = 'never_time'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doOAuthRequest prints a link and waits for the verification code when oauth2.txt is being created
NO_BROWSER = 'no_browser'
# Disable GAM API caching
NO_CACHE = 'no_cache'
# Do noit use URL shortner for authentication URLs
NO_SHORT_URLS = 'no_short_urls'
# Disable GAM update check
NO_UPDATE_CHECK = 'no_update_check'
# Disable SSL certificate validation
NO_VERIFY_SSL = 'no_verify_ssl'
# Number of threads for gam tbatch
NUM_TBATCH_THREADS = 'num_tbatch_threads'
# Number of threads for gam batch/csv
NUM_THREADS = 'num_threads'
# Path to oauth2.txt
OAUTH2_TXT = 'oauth2_txt'
# Path to oauth2service.json
OAUTH2SERVICE_JSON = 'oauth2service_json'
# Output date format, empty defalts to ISOFormat
OUTPUT_DATEFORMAT = 'output_dateformat'
# Output time format, empty defalts to ISOFormat
OUTPUT_TIMEFORMAT = 'output_timeformat'
# When retrieving lists of people from API, how many should be retrieved in each chunk
PEOPLE_MAX_RESULTS = 'people_max_results'
# Domains for print alises|groups|users
PRINT_AGU_DOMAINS = 'print_agu_domains'
# OrgUnits for print cros
PRINT_CROS_OUS = 'print_cros_ous'
# OrgUnits and children for print cros
PRINT_CROS_OUS_AND_CHILDREN = 'print_cros_ous_and_children'
# Number of seconds to wait for batch/csv processes to complete
PROCESS_WAIT_LIMIT = 'process_wait_limit'
# Use quick method to move Chromebooks to OU
QUICK_CROS_MOVE = 'quick_cros_move'
# Quick info user: nogroups nolicenses noschemas
QUICK_INFO_USER = 'quick_info_user'
# resellerId from gam.cfg or retrieved from Google
RESELLER_ID = 'reseller_id'
# Retry service not available errors on API calls
RETRY_API_SERVICE_NOT_AVAILABLE = 'retry_api_service_not_available'
# Default section to use for processing
SECTION = 'section'
# Show API calls retry data
SHOW_API_CALLS_RETRY_DATA = 'show_api_calls_retry_data'
# Show commands when processing batch/csv/loop
SHOW_COMMANDS = 'show_commands'
# Convert newlines in text fields to "\n" in show commands
SHOW_CONVERT_CR_NL = 'show_convert_cr_nl'
# Add (n/m) to end of messages if number of items to be processed exceeds this number
SHOW_COUNTS_MIN = 'show_counts_min'
# Enable/disable "Getting ... " messages
SHOW_GETTINGS = 'show_gettings'
# Enable/disable NL at end of "Got ..." messages
SHOW_GETTINGS_GOT_NL = 'show_gettings_got_nl'
# Enable/disable showing multiprocess info in redirected stdout/stderr
SHOW_MULTIPROCESS_INFO = 'show_multiprocess_info'
# SMTP fqdn
SMTP_FQDN = 'smtp_fqdn'
# SMTP host
SMTP_HOST = 'smtp_host'
# SMTP username
SMTP_USERNAME = 'smtp_username'
# SMTP password
SMTP_PASSWORD = 'smtp_password'
# Time Zone
TIMEZONE = 'timezone'
## Minimum TLS Version required for HTTPS connections
TLS_MIN_VERSION = 'tls_min_version'
## Maximum TLS Version used for HTTPS connections
TLS_MAX_VERSION = 'tls_max_version'
# Clear basic filter when updating an existing sheet
TODRIVE_CLEARFILTER = 'todrive_clearfilter'
# Use client access for todrive
TODRIVE_CLIENTACCESS = 'todrive_clientaccess'
# Enable conversion to Google Sheets when uploading todrive files
TODRIVE_CONVERSION = 'todrive_conversion'
# Save local copy of CSV file
TODRIVE_LOCALCOPY = 'todrive_localcopy'
# Specify locale for Google Sheets
TODRIVE_LOCALE = 'todrive_locale'
# Suppress opening browser on todrive upload
TODRIVE_NOBROWSER = 'todrive_nobrowser'
# Suppress sending email on todrive upload
TODRIVE_NOEMAIL = 'todrive_noemail'
# No escape character in CSV output file
TODRIVE_NO_ESCAPE_CHAR = 'todrive_no_escape_char'
# ID/Name of parent folder for todrive files
TODRIVE_PARENT = 'todrive_parent'
# Append timestamp to todrive sheet name
TODRIVE_SHEET_TIMESTAMP = 'todrive_sheet_timestamp'
# Sheet timestamp format, empty defalts to ISOFormat
TODRIVE_SHEET_TIMEFORMAT = 'todrive_sheet_timeformat'
# Append timestamp to todrive file name
TODRIVE_TIMESTAMP = 'todrive_timestamp'
# Timestamp format, empty defalts to ISOFormat
TODRIVE_TIMEFORMAT = 'todrive_timeformat'
# Specify timezone for Google Sheets
TODRIVE_TIMEZONE = 'todrive_timezone'
# Upload data files with no data
TODRIVE_UPLOAD_NODATA = 'todrive_upload_nodata'
# User for todrive files
TODRIVE_USER = 'todrive_user'
# Truncate Client ID
TRUNCATE_CLIENT_ID  = 'truncate_client_id'
# Update CrOS org unit with orgUnitId
UPDATE_CROS_OU_WITH_ID = 'update_cros_ou_with_id'
# Use admin access for chat where possible
USE_CHAT_ADMIN_ACCESS = 'use_chat_admin_access'
# Use course owner for course access
USE_COURSE_OWNER_ACCESS = 'use_course_owner_access'
# Use Project ID as Project Name and App Name
USE_PROJECTID_AS_NAME = 'use_projectid_as_name'
# When retrieving lists of Users from API, how many should be retrieved in each chunk
USER_MAX_RESULTS = 'user_max_results'
# User service account access only, no client access
USER_SERVICE_ACCOUNT_ACCESS_ONLY = 'user_service_account_access_only'

CSV_INPUT_ROW_FILTER_ITEMS = {CSV_INPUT_ROW_FILTER, CSV_INPUT_ROW_FILTER_MODE,
                              CSV_INPUT_ROW_DROP_FILTER, CSV_INPUT_ROW_DROP_FILTER_MODE,
                              CSV_INPUT_ROW_LIMIT}

CSV_OUTPUT_ROW_FILTER_ITEMS = {CSV_OUTPUT_HEADER_FILTER, CSV_OUTPUT_HEADER_DROP_FILTER,
                               CSV_OUTPUT_HEADER_FORCE, CSV_OUTPUT_HEADER_ORDER,
                               CSV_OUTPUT_ROW_FILTER, CSV_OUTPUT_ROW_FILTER_MODE,
                               CSV_OUTPUT_ROW_DROP_FILTER, CSV_OUTPUT_ROW_DROP_FILTER_MODE,
                               CSV_OUTPUT_ROW_LIMIT}

Defaults = {
  ACTIVITY_MAX_RESULTS: '100',
  ADMIN_EMAIL: '',
  API_CALLS_RATE_CHECK: FALSE,
  API_CALLS_RATE_LIMIT: '100',
  API_CALLS_TRIES_LIMIT: '10',
  AUTO_BATCH_MIN: '0',
  BAIL_ON_INTERNAL_ERROR_TRIES: '2',
  BATCH_SIZE: '50',
  CACERTS_PEM: '',
  CACHE_DIR: '',
  CACHE_DISCOVERY_ONLY: TRUE,
  CHARSET: DEFAULT_CHARSET,
  CHANNEL_CUSTOMER_ID: '',
  CLASSROOM_MAX_RESULTS: '0',
  CLIENT_SECRETS_JSON: FN_CLIENT_SECRETS_JSON,
  CLOCK_SKEW_IN_SECONDS: '10',
  CMDLOG: '',
  CMDLOG_MAX_BACKUPS: 5,
  CMDLOG_MAX_KILO_BYTES: 1000,
  CONFIG_DIR: '',
  CONTACT_MAX_RESULTS: '100',
  CSV_INPUT_COLUMN_DELIMITER: ',',
  CSV_INPUT_NO_ESCAPE_CHAR: TRUE,
  CSV_INPUT_QUOTE_CHAR: '\'"\'',
  CSV_INPUT_ROW_FILTER: '',
  CSV_INPUT_ROW_FILTER_MODE: 'allmatch',
  CSV_INPUT_ROW_DROP_FILTER: '',
  CSV_INPUT_ROW_DROP_FILTER_MODE: 'anymatch',
  CSV_INPUT_ROW_LIMIT: '0',
  CSV_OUTPUT_COLUMN_DELIMITER: ',',
  CSV_OUTPUT_CONVERT_CR_NL: FALSE,
  CSV_OUTPUT_NO_ESCAPE_CHAR: FALSE,
  CSV_OUTPUT_FIELD_DELIMITER: "' '",
  CSV_OUTPUT_HEADER_FILTER: '',
  CSV_OUTPUT_HEADER_DROP_FILTER: '',
  CSV_OUTPUT_HEADER_FORCE: '',
  CSV_OUTPUT_HEADER_ORDER: '',
  CSV_OUTPUT_LINE_TERMINATOR: 'lf',
  CSV_OUTPUT_QUOTE_CHAR: '\'"\'',
  CSV_OUTPUT_ROW_FILTER: '',
  CSV_OUTPUT_ROW_FILTER_MODE: 'allmatch',
  CSV_OUTPUT_ROW_DROP_FILTER: '',
  CSV_OUTPUT_ROW_DROP_FILTER_MODE: 'anymatch',
  CSV_OUTPUT_ROW_LIMIT: '0',
  CSV_OUTPUT_SORT_HEADERS: '',
  CSV_OUTPUT_SUBFIELD_DELIMITER: '.',
  CSV_OUTPUT_TIMESTAMP_COLUMN: '',
  CSV_OUTPUT_USERS_AUDIT: FALSE,
  CUSTOMER_ID: MY_CUSTOMER,
  DEBUG_LEVEL: '0',
  DEVICE_MAX_RESULTS: '200',
  DOMAIN: '',
  DRIVE_DIR: '',
  ENFORCE_EXPANSIVE_ACCESS: TRUE,
  DRIVE_MAX_RESULTS: '1000',
  DRIVE_V3_BETA: FALSE,
  DRIVE_V3_NATIVE_NAMES: TRUE,
  EMAIL_BATCH_SIZE: '50',
  ENABLE_DASA: FALSE,
  ENABLE_GCLOUD_REAUTH: FALSE,
  EVENT_MAX_RESULTS: '250',
  EXTRA_ARGS: '',
  GMAIL_CSE_INCERT_DIR: '',
  GMAIL_CSE_INKEY_DIR: '',
  INTER_BATCH_WAIT: '0',
  LICENSE_MAX_RESULTS: '100',
  LICENSE_SKUS: '',
  MEET_V2_BETA: FALSE,
  MEMBER_MAX_RESULTS: '200',
  MEMBER_MAX_RESULTS_CI_BASIC: '1000',
  MEMBER_MAX_RESULTS_CI_FULL: '500',
  MESSAGE_BATCH_SIZE: '50',
  MESSAGE_MAX_RESULTS: '500',
  MOBILE_MAX_RESULTS: '100',
  MULTIPROCESS_POOL_LIMIT: '0',
  NEVER_TIME: NEVER,
  NO_BROWSER: FALSE,
  NO_CACHE: FALSE,
  NO_SHORT_URLS: TRUE,
  NO_UPDATE_CHECK: TRUE,
  NO_VERIFY_SSL: FALSE,
  NUM_TBATCH_THREADS: '2',
  NUM_THREADS: '5',
  OAUTH2_TXT: FN_OAUTH2_TXT,
  OAUTH2SERVICE_JSON: FN_OAUTH2SERVICE_JSON,
  OUTPUT_DATEFORMAT: '',
  OUTPUT_TIMEFORMAT: '',
  PEOPLE_MAX_RESULTS: '100',
  PRINT_AGU_DOMAINS: '',
  PRINT_CROS_OUS: '',
  PRINT_CROS_OUS_AND_CHILDREN: '',
  PROCESS_WAIT_LIMIT: '0',
  QUICK_CROS_MOVE: FALSE,
  QUICK_INFO_USER: FALSE,
  RESELLER_ID: '',
  RETRY_API_SERVICE_NOT_AVAILABLE: FALSE,
  SECTION: '',
  SHOW_API_CALLS_RETRY_DATA: FALSE,
  SHOW_COMMANDS: FALSE,
  SHOW_CONVERT_CR_NL: FALSE,
  SHOW_COUNTS_MIN: '1',
  SHOW_GETTINGS: TRUE,
  SHOW_GETTINGS_GOT_NL: FALSE,
  SHOW_MULTIPROCESS_INFO: FALSE,
  SMTP_FQDN: '',
  SMTP_HOST: '',
  SMTP_USERNAME: '',
  SMTP_PASSWORD: '',
  TIMEZONE: 'utc',
  TLS_MIN_VERSION: 'TLSv1_3',
  TLS_MAX_VERSION: '',
  TODRIVE_CLEARFILTER: FALSE,
  TODRIVE_CLIENTACCESS: FALSE,
  TODRIVE_CONVERSION: TRUE,
  TODRIVE_LOCALCOPY: FALSE,
  TODRIVE_LOCALE: '',
  TODRIVE_NOBROWSER: '',
  TODRIVE_NOEMAIL: '',
  TODRIVE_NO_ESCAPE_CHAR: TRUE,
  TODRIVE_PARENT: 'root',
  TODRIVE_SHEET_TIMESTAMP: 'copy', # copy from TODRIVE_TIMESTAMP
  TODRIVE_SHEET_TIMEFORMAT: 'copy', # copy from TODRIVE_TIMEFORMAT
  TODRIVE_TIMESTAMP: FALSE,
  TODRIVE_TIMEFORMAT: '',
  TODRIVE_TIMEZONE: '',
  TODRIVE_UPLOAD_NODATA: TRUE,
  TODRIVE_USER: '',
  TRUNCATE_CLIENT_ID: FALSE,
  UPDATE_CROS_OU_WITH_ID: FALSE,
  USE_CHAT_ADMIN_ACCESS: FALSE,
  USE_COURSE_OWNER_ACCESS: FALSE,
  USE_PROJECTID_AS_NAME: FALSE,
  USER_MAX_RESULTS: '500',
  USER_SERVICE_ACCOUNT_ACCESS_ONLY: FALSE,
  }

Values = {DEBUG_LEVEL: 0}

TYPE_BOOLEAN = 'bool'
TYPE_CHARACTER = 'char'
TYPE_CHOICE = 'choi'
TYPE_CHOICE_LIST = 'chol'
TYPE_DATETIME = 'datm'
TYPE_DIRECTORY = 'dire'
TYPE_EMAIL = 'emai'
TYPE_EMAIL_OPTIONAL = 'emao'
TYPE_FILE = 'file'
TYPE_FLOAT = 'floa'
TYPE_HEADERFILTER = 'heaf'
TYPE_HEADERFORCE = 'hefo'
TYPE_HEADERORDER = 'heor'
TYPE_INTEGER = 'inte'
TYPE_LANGUAGE = 'lang'
TYPE_LOCALE = 'locl'
TYPE_PASSWORD = 'pass'
TYPE_ROWFILTER = 'rowf'
TYPE_STRING = 'stri'
TYPE_STRINGLIST = 'strl'
TYPE_TIMEZONE = 'tmzn'

VAR_TYPE = 'type'
VAR_ENVVAR = 'enva'
VAR_CHOICES = 'chod'
VAR_LIMITS = 'lmit'
VAR_SFFT = 'sfft'
VAR_SIGFILE = 'sigf'
VAR_ACCESS = 'aces'

VAR_INFO = {
  ACTIVITY_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 500)},
  ADMIN_EMAIL: {VAR_TYPE: TYPE_STRING, VAR_ENVVAR: 'GA_ADMIN_EMAIL', VAR_LIMITS: (0, None)},
  API_CALLS_RATE_CHECK: {VAR_TYPE: TYPE_BOOLEAN},
  API_CALLS_RATE_LIMIT: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (50, None)},
  API_CALLS_TRIES_LIMIT: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (3, 30)},
  AUTO_BATCH_MIN: {VAR_TYPE: TYPE_INTEGER, VAR_ENVVAR: 'GAM_AUTOBATCH', VAR_LIMITS: (0, 100)},
  BAIL_ON_INTERNAL_ERROR_TRIES: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 10)},
  BATCH_SIZE: {VAR_TYPE: TYPE_INTEGER, VAR_ENVVAR: 'GAM_BATCH_SIZE', VAR_LIMITS: (1, 1000)},
  CACERTS_PEM: {VAR_TYPE: TYPE_FILE, VAR_ENVVAR: 'GAM_CA_FILE', VAR_ACCESS: os.R_OK},
  CACHE_DIR: {VAR_TYPE: TYPE_DIRECTORY, VAR_ENVVAR: 'GAMCACHEDIR'},
  CACHE_DISCOVERY_ONLY: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'allcache.txt', VAR_SFFT: (TRUE, FALSE)},
  CHARSET: {VAR_TYPE: TYPE_STRING, VAR_ENVVAR: 'GAM_CHARSET', VAR_LIMITS: (1, None)},
  CHANNEL_CUSTOMER_ID: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  CLASSROOM_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (0, 1000)},
  CLIENT_SECRETS_JSON: {VAR_TYPE: TYPE_FILE, VAR_ENVVAR: 'CLIENTSECRETS', VAR_ACCESS: os.R_OK},
  CLOCK_SKEW_IN_SECONDS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (10, 3600)},
  CMDLOG: {VAR_TYPE: TYPE_FILE, VAR_ACCESS: os.W_OK},
  CMDLOG_MAX_BACKUPS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 10)},
  CMDLOG_MAX_KILO_BYTES: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (100, 10000)},
  CONFIG_DIR: {VAR_TYPE: TYPE_DIRECTORY, VAR_ENVVAR: 'GAMUSERCONFIGDIR'},
  CONTACT_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 10000)},
  CSV_INPUT_COLUMN_DELIMITER: {VAR_TYPE: TYPE_CHARACTER},
  CSV_INPUT_NO_ESCAPE_CHAR: {VAR_TYPE: TYPE_BOOLEAN},
  CSV_INPUT_QUOTE_CHAR: {VAR_TYPE: TYPE_CHARACTER},
  CSV_INPUT_ROW_FILTER: {VAR_TYPE: TYPE_ROWFILTER},
  CSV_INPUT_ROW_FILTER_MODE: {VAR_TYPE: TYPE_CHOICE, VAR_CHOICES: {'allmatch': True, 'anymatch': False}},
  CSV_INPUT_ROW_DROP_FILTER: {VAR_TYPE: TYPE_ROWFILTER},
  CSV_INPUT_ROW_DROP_FILTER_MODE: {VAR_TYPE: TYPE_CHOICE, VAR_CHOICES: {'allmatch': True, 'anymatch': False}},
  CSV_INPUT_ROW_LIMIT: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (0, None)},
  CSV_OUTPUT_COLUMN_DELIMITER: {VAR_TYPE: TYPE_CHARACTER},
  CSV_OUTPUT_CONVERT_CR_NL: {VAR_TYPE: TYPE_BOOLEAN},
  CSV_OUTPUT_NO_ESCAPE_CHAR: {VAR_TYPE: TYPE_BOOLEAN},
  CSV_OUTPUT_FIELD_DELIMITER: {VAR_TYPE: TYPE_CHARACTER},
  CSV_OUTPUT_HEADER_FILTER: {VAR_TYPE: TYPE_HEADERFILTER},
  CSV_OUTPUT_HEADER_DROP_FILTER: {VAR_TYPE: TYPE_HEADERFILTER},
  CSV_OUTPUT_HEADER_FORCE: {VAR_TYPE: TYPE_HEADERFORCE},
  CSV_OUTPUT_HEADER_ORDER: {VAR_TYPE: TYPE_HEADERORDER},
  CSV_OUTPUT_LINE_TERMINATOR: {VAR_TYPE: TYPE_CHOICE, VAR_CHOICES: {'cr': '\r', 'lf': '\n', 'crlf': '\r\n'}},
  CSV_OUTPUT_QUOTE_CHAR: {VAR_TYPE: TYPE_CHARACTER},
  CSV_OUTPUT_ROW_FILTER: {VAR_TYPE: TYPE_ROWFILTER},
  CSV_OUTPUT_ROW_FILTER_MODE: {VAR_TYPE: TYPE_CHOICE, VAR_CHOICES: {'allmatch': True, 'anymatch': False}},
  CSV_OUTPUT_ROW_DROP_FILTER: {VAR_TYPE: TYPE_ROWFILTER},
  CSV_OUTPUT_ROW_DROP_FILTER_MODE: {VAR_TYPE: TYPE_CHOICE, VAR_CHOICES: {'allmatch': True, 'anymatch': False}},
  CSV_OUTPUT_ROW_LIMIT: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (0, None)},
  CSV_OUTPUT_SORT_HEADERS: {VAR_TYPE: TYPE_STRINGLIST},
  CSV_OUTPUT_SUBFIELD_DELIMITER: {VAR_TYPE: TYPE_CHARACTER},
  CSV_OUTPUT_TIMESTAMP_COLUMN: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  CSV_OUTPUT_USERS_AUDIT: {VAR_TYPE: TYPE_BOOLEAN},
  CUSTOMER_ID: {VAR_TYPE: TYPE_STRING, VAR_ENVVAR: 'CUSTOMER_ID', VAR_LIMITS: (0, None)},
  DEBUG_LEVEL: {VAR_TYPE: TYPE_INTEGER, VAR_SIGFILE: 'debug.gam', VAR_LIMITS: (0, None), VAR_SFFT: ('0', '4')},
  DEVICE_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 200)},
  DOMAIN: {VAR_TYPE: TYPE_STRING, VAR_ENVVAR: 'GA_DOMAIN', VAR_LIMITS: (0, None)},
  DRIVE_DIR: {VAR_TYPE: TYPE_DIRECTORY, VAR_ENVVAR: 'GAMDRIVEDIR'},
  ENFORCE_EXPANSIVE_ACCESS: {VAR_TYPE: TYPE_BOOLEAN},
  DRIVE_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 1000)},
  DRIVE_V3_BETA: {VAR_TYPE: TYPE_BOOLEAN},
  DRIVE_V3_NATIVE_NAMES: {VAR_TYPE: TYPE_BOOLEAN},
  EMAIL_BATCH_SIZE: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 100)},
  ENABLE_DASA: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'enabledasa.txt', VAR_SFFT: (FALSE, TRUE)},
  ENABLE_GCLOUD_REAUTH: {VAR_TYPE: TYPE_BOOLEAN},
  EVENT_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 2500)},
  EXTRA_ARGS: {VAR_TYPE: TYPE_FILE, VAR_SIGFILE: FN_EXTRA_ARGS_TXT, VAR_SFFT: ('', FN_EXTRA_ARGS_TXT), VAR_ACCESS: os.R_OK},
  GMAIL_CSE_INCERT_DIR: {VAR_TYPE: TYPE_DIRECTORY},
  GMAIL_CSE_INKEY_DIR: {VAR_TYPE: TYPE_DIRECTORY},
  INTER_BATCH_WAIT: {VAR_TYPE: TYPE_FLOAT, VAR_LIMITS: (0.0, 60.0)},
  LICENSE_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (10, 1000)},
  LICENSE_SKUS: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  MEET_V2_BETA: {VAR_TYPE: TYPE_BOOLEAN},
  MEMBER_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 200)},
  MEMBER_MAX_RESULTS_CI_BASIC: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 1000)},
  MEMBER_MAX_RESULTS_CI_FULL: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 500)},
  MESSAGE_BATCH_SIZE: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 1000)},
  MESSAGE_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 10000)},
  MOBILE_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 100)},
  MULTIPROCESS_POOL_LIMIT: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (-1, None)},
  NEVER_TIME: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  NO_BROWSER: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'nobrowser.txt', VAR_SFFT: (FALSE, TRUE)},
  NO_CACHE: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'nocache.txt', VAR_SFFT: (FALSE, TRUE)},
  NO_SHORT_URLS: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'noshorturls.txt', VAR_SFFT: (FALSE, TRUE)},
  NO_UPDATE_CHECK: {VAR_TYPE: TYPE_BOOLEAN},
  NO_VERIFY_SSL: {VAR_TYPE: TYPE_BOOLEAN},
  NUM_TBATCH_THREADS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 1000)},
  NUM_THREADS: {VAR_TYPE: TYPE_INTEGER, VAR_ENVVAR: 'GAM_THREADS', VAR_LIMITS: (1, 1000)},
  OAUTH2_TXT: {VAR_TYPE: TYPE_FILE, VAR_ENVVAR: 'OAUTHFILE', VAR_ACCESS: os.R_OK | os.W_OK},
  OAUTH2SERVICE_JSON: {VAR_TYPE: TYPE_FILE, VAR_ENVVAR: 'OAUTHSERVICEFILE', VAR_ACCESS: os.R_OK | os.W_OK},
  OUTPUT_DATEFORMAT: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  OUTPUT_TIMEFORMAT: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  PEOPLE_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (0, 1000)},
  PRINT_AGU_DOMAINS: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  PRINT_CROS_OUS: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  PRINT_CROS_OUS_AND_CHILDREN: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  PROCESS_WAIT_LIMIT: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (0, None)},
  QUICK_CROS_MOVE: {VAR_TYPE: TYPE_BOOLEAN},
  QUICK_INFO_USER: {VAR_TYPE: TYPE_BOOLEAN},
  RESELLER_ID: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  RETRY_API_SERVICE_NOT_AVAILABLE: {VAR_TYPE: TYPE_BOOLEAN},
  SECTION: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  SHOW_API_CALLS_RETRY_DATA: {VAR_TYPE: TYPE_BOOLEAN},
  SHOW_COMMANDS: {VAR_TYPE: TYPE_BOOLEAN},
  SHOW_CONVERT_CR_NL: {VAR_TYPE: TYPE_BOOLEAN},
  SHOW_COUNTS_MIN: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (0, 100)},
  SHOW_GETTINGS: {VAR_TYPE: TYPE_BOOLEAN},
  SHOW_GETTINGS_GOT_NL: {VAR_TYPE: TYPE_BOOLEAN},
  SHOW_MULTIPROCESS_INFO: {VAR_TYPE: TYPE_BOOLEAN},
  SMTP_FQDN: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  SMTP_HOST: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  SMTP_USERNAME: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  SMTP_PASSWORD: {VAR_TYPE: TYPE_PASSWORD, VAR_LIMITS: (0, None)},
  TIMEZONE: {VAR_TYPE: TYPE_TIMEZONE},
  TLS_MIN_VERSION: {VAR_TYPE: TYPE_CHOICE, VAR_ENVVAR: 'GAM_TLS_MIN_VERSION', VAR_CHOICES: TLS_CHOICE_MAP},
  TLS_MAX_VERSION: {VAR_TYPE: TYPE_CHOICE, VAR_ENVVAR: 'GAM_TLS_MAX_VERSION', VAR_CHOICES: TLS_CHOICE_MAP},
  TODRIVE_CLEARFILTER: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_CLIENTACCESS: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_CONVERSION: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_LOCALCOPY: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_LOCALE: {VAR_TYPE: TYPE_LOCALE},
  TODRIVE_NOBROWSER: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'nobrowser.txt', VAR_SFFT: (FALSE, TRUE)},
  TODRIVE_NOEMAIL: {VAR_TYPE: TYPE_BOOLEAN, VAR_SIGFILE: 'notdemail.txt', VAR_SFFT: (FALSE, TRUE)},
  TODRIVE_NO_ESCAPE_CHAR: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_PARENT: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  TODRIVE_SHEET_TIMESTAMP: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_SHEET_TIMEFORMAT: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  TODRIVE_TIMESTAMP: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_TIMEFORMAT: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  TODRIVE_TIMEZONE: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  TODRIVE_UPLOAD_NODATA: {VAR_TYPE: TYPE_BOOLEAN},
  TODRIVE_USER: {VAR_TYPE: TYPE_STRING, VAR_LIMITS: (0, None)},
  TRUNCATE_CLIENT_ID: {VAR_TYPE: TYPE_BOOLEAN},
  UPDATE_CROS_OU_WITH_ID: {VAR_TYPE: TYPE_BOOLEAN},
  USE_CHAT_ADMIN_ACCESS: {VAR_TYPE: TYPE_BOOLEAN},
  USE_COURSE_OWNER_ACCESS: {VAR_TYPE: TYPE_BOOLEAN},
  USE_PROJECTID_AS_NAME: {VAR_TYPE: TYPE_BOOLEAN},
  USER_MAX_RESULTS: {VAR_TYPE: TYPE_INTEGER, VAR_LIMITS: (1, 500)},
  USER_SERVICE_ACCOUNT_ACCESS_ONLY: {VAR_TYPE: TYPE_BOOLEAN},
  }
