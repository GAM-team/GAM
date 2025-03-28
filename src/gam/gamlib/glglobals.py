# -*- coding: utf-8 -*-

# Copyright (C) 2023 Ross Scroggs All Rights Reserved.
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

"""GAM global variables

"""

# The following GM_XXX constants are arbitrary but must be unique
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
# GAM admin user from oauth2.txt or oauth2service.json
ADMIN = 'admn'
# Drive service for admin; used to look up Shared Drive Names
ADMIN_DRIVE = 'addr'
# Number/length of API call retries
API_CALLS_RETRY_DATA = 'rtry'
# GAM cache directory. If no_cache is True, this variable will be set to None
CACHE_DIR = 'gacd'
# Reset GAM cache directory after discovery
CACHE_DISCOVERY_ONLY = 'gcdo'
# Classroom service not available
CLASSROOM_SERVICE_NOT_AVAILABLE = 'csna'
# Command logging
CMDLOG_HANDLER = 'clha'
CMDLOG_LOGGER = 'cllo'
# Convert to local time
CONVERT_TO_LOCAL_TIME = 'ctlt'
# Credentials scopes
CREDENTIALS_SCOPES = 'crsc'
# csvfile keyfield <FieldName> [delimiter <Character>] (matchfield <FieldName> <MatchPattern>)* [datafield <FieldName>(:<FieldName>*) [delimiter <String>]]
CSVFILE = 'csvf'
# { key: [datafieldvalues]}
CSV_DATA_DICT = 'csdd'
CSV_KEY_FIELD = 'cskf'
CSV_SUBKEY_FIELD = 'cssk'
CSV_DATA_FIELD = 'csdf'
# Filter for input column drop values
CSV_INPUT_ROW_DROP_FILTER = 'cird'
# Mode (and|or) for input column drop values
CSV_INPUT_ROW_DROP_FILTER_MODE = 'cidm'
# Filter for input column values
CSV_INPUT_ROW_FILTER = 'cirf'
# Mode (and|or) for input column values
CSV_INPUT_ROW_FILTER_MODE = 'cirm'
# Limit number of input rows
CSV_INPUT_ROW_LIMIT = 'cirl'
# Column delimiter in CSV output file
CSV_OUTPUT_COLUMN_DELIMITER = 'codl'
# Filter for output column headers to drop
CSV_OUTPUT_HEADER_DROP_FILTER = 'cohd'
# Filter for output column headers
CSV_OUTPUT_HEADER_FILTER = 'cohf'
# Force output column headers
CSV_OUTPUT_HEADER_FORCE = 'cofh'
# Order output column headers
CSV_OUTPUT_HEADER_ORDER = 'coho'
# No escape character in CSV output file
CSV_OUTPUT_NO_ESCAPE_CHAR = 'cone'
# Quote character in CSV output file
CSV_OUTPUT_QUOTE_CHAR = 'coqc'
# Filter for output column drop values
CSV_OUTPUT_ROW_DROP_FILTER = 'cord'
# Mode (and|or) for output column drop values
CSV_OUTPUT_ROW_DROP_FILTER_MODE = 'codm'
# Filter for output column values
CSV_OUTPUT_ROW_FILTER = 'corf'
# Mode (and|or) for output column values
CSV_OUTPUT_ROW_FILTER_MODE = 'corm'
# Limit number of output rows
CSV_OUTPUT_ROW_LIMIT = 'corl'
# Add timestamp column to CSV output file
CSV_OUTPUT_TIMESTAMP_COLUMN = 'cotc'
# Transpose output rows/columns
CSV_OUTPUT_TRANSPOSE = 'cotr'
# Output sort headers
CSV_OUTPUT_SORT_HEADERS = 'cosh'
# CSV todrive options
CSV_TODRIVE = 'todr'
# Current API services
CURRENT_API_SERVICES = 'caps'
# Current Client API
CURRENT_CLIENT_API = 'ccap'
# Current Client API scopes
CURRENT_CLIENT_API_SCOPES = 'ccas'
# Current Service Account API
CURRENT_SVCACCT_API = 'csap'
# Current Service Account API scopes
CURRENT_SVCACCT_API_SCOPES = 'csas'
# Current Service Account user
CURRENT_SVCACCT_USER = 'csa'
# datetime.datetime.now
DATETIME_NOW = 'dtno'
# If debug_level > 0: extra_args['prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
DEBUG_LEVEL = 'dbgl'
# Decoded ID token
DECODED_ID_TOKEN = 'didt'
# Index of start of <UserTypeEntity> in command line
ENTITY_CL_DELAY_START = 'ecld'
ENTITY_CL_START = 'ecls'
# Extra arguments to pass to GAPI functions
EXTRA_ARGS_LIST = 'exad'
# gam.cfg file
GAM_CFG_FILE = 'gcfi'
GAM_CFG_PATH = 'gcpa'
GAM_CFG_SECTION = 'gcse'
GAM_CFG_SECTION_NAME = 'gcsn'
# Path to gam
GAM_PATH = 'gpth'
# Python source, PyInstaller or StaticX?
GAM_TYPE = 'gtyp'
# Length of last Got message
LAST_GOT_MSG_LEN = 'lgml'
# License SKUs
LICENSE_SKUS = 'lsku'
# Make Building ID/Name map
MAKE_BUILDING_ID_NAME_MAP = 'mkbm'
# Dictionary mapping Building ID to Name
MAP_BUILDING_ID_TO_NAME = 'bi2n'
# Dictionary mapping Building Name to ID
MAP_BUILDING_NAME_TO_ID = 'bn2i'
# Dictionary mapping OrgUnit ID to Name
MAP_ORGUNIT_ID_TO_NAME = 'oi2n'
# Dictionary mapping Shared Drive ID to Name
MAP_SHAREDDRIVE_ID_TO_NAME = 'si2n'
# Make Role ID/Name map
MAKE_ROLE_ID_NAME_MAP = 'mkrm'
# Dictionary mapping Role ID to Name
MAP_ROLE_ID_TO_NAME = 'ri2n'
# Dictionary mapping Role Name to ID
MAP_ROLE_NAME_TO_ID = 'rn2i'
# Dictionary mapping User ID to Name
MAP_USER_ID_TO_NAME = 'ui2n'
# Multiprocess exit condition
MULTIPROCESS_EXIT_CONDITION = 'mpec'
# Multiprocess exit processing
MULTIPROCESS_EXIT_PROCESSING = 'mpep'
# Number of batch items
NUM_BATCH_ITEMS = 'nbat'
# Values retrieved from oauth2service.json
OAUTH2SERVICE_CLIENT_ID = 'osci'
OAUTH2SERVICE_JSON_DATA = 'osjd'
# Values retrieved from oauth2.txt
OAUTH2_CLIENT_ID = 'oaci'
# oauth2.txt lock file
OAUTH2_TXT_LOCK = 'oatl'
# Output date format, empty defalts to ISOFormat
OUTPUT_DATEFORMAT = 'oudf'
# Output time format, empty defalts to ISOFormat
OUTPUT_TIMEFORMAT = 'outf'
# gam.cfg parser
PARSER = 'pars'
# Process ID
PID = 'pid '
# Domains for print alises|groups|users
PRINT_AGU_DOMAINS = 'pagu'
# OrgUnits for print cros
PRINT_CROS_OUS = 'pcou'
# OrgUnits and children for print cros
PRINT_CROS_OUS_AND_CHILDREN = 'pcoc'
# Check API calls rate
RATE_CHECK_COUNT = 'rccn'
RATE_CHECK_START = 'rcst'
# Section name from outer gam, passed to inner gams
SECTION = 'sect'
# Enable/disable "Getting ... " messages
SHOW_GETTINGS = 'shog'
# Enable/disable NL at end of "Got ..." messages
SHOW_GETTINGS_GOT_NL = 'shgn'
# redirected files
SAVED_STDOUT = 'svso'
STDERR = 'stde'
STDOUT = 'stdo'
# Scopes values retrieved from oauth2service.json
SVCACCT_SCOPES = 'sasc'
# Were scopes values retrieved from oauth2service.json
SVCACCT_SCOPES_DEFINED = 'sasd'
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
SYSEXITRC = 'sxrc'
# Encodings
SYS_ENCODING = 'syen'
# Shared by threadBatchWorker and threadBatchGAMCommands
TBATCH_QUEUE = 'batq'
# redirected file fields: name, mode, encoding, write header, multiproces, queue
REDIRECT_NAME = 'rdfn'
REDIRECT_MODE = 'rdmo'
REDIRECT_FD = 'rdfd'
REDIRECT_MULTI_FD = 'rdmf'
REDIRECT_STD = 'rdst'
REDIRECT_ENCODING = 'rden'
REDIRECT_WRITE_HEADER = 'rdwh'
REDIRECT_MULTIPROCESS = 'rdmp'
REDIRECT_QUEUE = 'rdq'
REDIRECT_QUEUE_NAME = 'name'
REDIRECT_QUEUE_TODRIVE = 'todrive'
REDIRECT_QUEUE_CSVPF = 'csvpf'
REDIRECT_QUEUE_DATA = 'rows'
REDIRECT_QUEUE_ARGS = 'args'
REDIRECT_QUEUE_GLOBALS = 'globals'
REDIRECT_QUEUE_VALUES = 'values'
REDIRECT_QUEUE_START = 'start'
REDIRECT_QUEUE_END = 'end'
REDIRECT_QUEUE_EOF = 'eof'
#
Globals = {
  ADMIN: None,
  ADMIN_DRIVE: None,
  API_CALLS_RETRY_DATA: {},
  CACHE_DIR: None,
  CACHE_DISCOVERY_ONLY: True,
  CLASSROOM_SERVICE_NOT_AVAILABLE: False,
  CMDLOG_HANDLER: None,
  CMDLOG_LOGGER: None,
  CONVERT_TO_LOCAL_TIME: False,
  CREDENTIALS_SCOPES: set(),
  CSVFILE: {},
  CSV_DATA_DICT: {},
  CSV_KEY_FIELD: None,
  CSV_SUBKEY_FIELD: None,
  CSV_DATA_FIELD: None,
  CSV_INPUT_ROW_DROP_FILTER: [],
  CSV_INPUT_ROW_DROP_FILTER_MODE: False,
  CSV_INPUT_ROW_FILTER: [],
  CSV_INPUT_ROW_FILTER_MODE: True,
  CSV_INPUT_ROW_LIMIT: 0,
  CSV_OUTPUT_COLUMN_DELIMITER: None,
  CSV_OUTPUT_HEADER_DROP_FILTER: [],
  CSV_OUTPUT_HEADER_FILTER: [],
  CSV_OUTPUT_HEADER_FORCE: [],
  CSV_OUTPUT_HEADER_ORDER: [],
  CSV_OUTPUT_NO_ESCAPE_CHAR: None,
  CSV_OUTPUT_QUOTE_CHAR: None,
  CSV_OUTPUT_ROW_DROP_FILTER: [],
  CSV_OUTPUT_ROW_DROP_FILTER_MODE: False,
  CSV_OUTPUT_ROW_FILTER: [],
  CSV_OUTPUT_ROW_FILTER_MODE: True,
  CSV_OUTPUT_ROW_LIMIT: 0,
  CSV_OUTPUT_SORT_HEADERS: [],
  CSV_OUTPUT_TIMESTAMP_COLUMN: None,
  CSV_OUTPUT_TRANSPOSE: False,
  CSV_TODRIVE: {},
  CURRENT_API_SERVICES: {},
  CURRENT_CLIENT_API: None,
  CURRENT_CLIENT_API_SCOPES: set(),
  CURRENT_SVCACCT_API: None,
  CURRENT_SVCACCT_API_SCOPES: set(),
  CURRENT_SVCACCT_USER: None,
  DATETIME_NOW: None,
  DEBUG_LEVEL: 0,
  DECODED_ID_TOKEN: None,
  ENTITY_CL_DELAY_START: 1,
  ENTITY_CL_START: 1,
  EXTRA_ARGS_LIST: [],
  GAM_CFG_FILE: '',
  GAM_CFG_PATH: '',
  GAM_CFG_SECTION: '',
  GAM_CFG_SECTION_NAME: '',
  GAM_PATH: '.',
  GAM_TYPE: '',
  LAST_GOT_MSG_LEN: 0,
  LICENSE_SKUS: [],
  MAKE_BUILDING_ID_NAME_MAP: True,
  MAKE_ROLE_ID_NAME_MAP: True,
  MAP_BUILDING_ID_TO_NAME: {},
  MAP_BUILDING_NAME_TO_ID: {},
  MAP_ORGUNIT_ID_TO_NAME: {},
  MAP_SHAREDDRIVE_ID_TO_NAME: {},
  MAP_ROLE_ID_TO_NAME: {},
  MAP_ROLE_NAME_TO_ID: {},
  MAP_USER_ID_TO_NAME: {},
  MULTIPROCESS_EXIT_CONDITION: None,
  MULTIPROCESS_EXIT_PROCESSING: False,
  NUM_BATCH_ITEMS: 0,
  OAUTH2SERVICE_CLIENT_ID: None,
  OAUTH2SERVICE_JSON_DATA: {},
  OAUTH2_CLIENT_ID: None,
  OAUTH2_TXT_LOCK: None,
  OUTPUT_DATEFORMAT: '',
  OUTPUT_TIMEFORMAT: '',
  PARSER: None,
  PID: 0,
  PRINT_AGU_DOMAINS: '',
  PRINT_CROS_OUS: '',
  PRINT_CROS_OUS_AND_CHILDREN: '',
  RATE_CHECK_COUNT: 0,
  RATE_CHECK_START: 0,
  SECTION: None,
  SHOW_GETTINGS: True,
  SHOW_GETTINGS_GOT_NL: False,
  SAVED_STDOUT: None,
  STDERR: {},
  STDOUT: {},
  SVCACCT_SCOPES: {},
  SVCACCT_SCOPES_DEFINED: False,
  SYSEXITRC: 0,
  SYS_ENCODING: 'utf-8',
  TBATCH_QUEUE: None
  }
