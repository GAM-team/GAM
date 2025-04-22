# -*- coding: utf-8 -*-

# Copyright (C) 2024 Ross Scroggs All Rights Reserved.
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

"""GAM messages

"""

# These values can be translated into other languages
# Project creation messages in order of appearance
CREATING_PROJECT = 'Creating project "{0}"...\n'
CHECK_INTERRUPTED = 'Check interrupted'
CHECKING_PROJECT_CREATION_STATUS = 'Checking project creation status...\n'
NO_RIGHTS_GOOGLE_CLOUD_ORGANIZATION = 'Looks like you have no rights to your Google Cloud Organization.\nAttempting to fix that...\n'
YOUR_ORGANIZATION_NAME_IS = 'Your organization name is {0}\n'
YOU_HAVE_NO_RIGHTS_TO_CREATE_PROJECTS_AND_YOU_ARE_NOT_A_SUPER_ADMIN = 'You have no rights to create projects for your organization and you don\'t seem to be a super admin! Sorry, there\'s nothing more I can do.'
LOOKS_LIKE_NO_ONE_HAS_RIGHTS_TO_YOUR_GOOGLE_CLOUD_ORGANIZATION_ATTEMPTING_TO_GIVE_YOU_CREATE_RIGHTS = 'Looks like no one has rights to your Google Cloud Organization. Attempting to give you create rights...\n'
THE_FOLLOWING_RIGHTS_SEEM_TO_EXIST = 'The following rights seem to exist:\n'
GIVING_LOGIN_HINT_THE_CREATOR_ROLE = 'Giving {0} the role of {1}...\n'
ACCEPT_CLOUD_TOS = '''
Please go to:

https://console.cloud.google.com/projectselector2/home/dashboard?supportedpurview=project

sign in as {0} and accept the Terms of Service (ToS). As soon as you've accepted the ToS popup, you can return here and press enter.\n'''

PROJECT_STILL_BEING_CREATED_SLEEPING = 'Project still being created. Sleeping {0} seconds\n'
FAILED_TO_CREATE_PROJECT = 'Failed to create project: {0}\n'
SETTING_GAM_PROJECT_CONSENT_SCREEN_CREATING_CLIENT = 'Setting GAM project consent screen, creating client...\n'
CREATE_CLIENT_INSTRUCTIONS = '''
Please go to:

  {0}

 1. If "+ CREATE CLIENT" is on the screen, skip to step 14
 2. Click "GET STARTED"
 3. Under "App Information", enter {1} or another value in "App name *"
 4. Under "App Information", enter {2} in "User support email *"
 5. Click "NEXT"
 6. Under "Audience", choose INTERNAL
 7. Click "NEXT"
 8. Under, "Contact Information", enter an email address in "Email addresses *"
 9. Click "NEXT"
10. Under "Finish", click "I agree to the Google API Services: User Data Policy."
11. Click "CONTINUE"
12. Click "CREATE"
13. Click "Clients" in the left-hand column
14. Click "+ CREATE CLIENT"
15. Choose "Desktop App" for "Application type"
16. Enter {1} or another value in "Name *"
17. Click "Create"
18. Under "Name", click your client name
19. Copy the "Client ID" value under "Additional information"
20. Paste it at the "Enter your Client ID: " prompt in your terminal
21. Press return/enter in your terminal
22. Switch back to the browser
23. Copy the "Client secret" value under "Client Secrets"
24. Paste it at the "Enter your Client Secret: " prompt in your terminal
25. Press return/enter in your terminal
26. Switch back to the browser
27. Click "OK"
28. These steps are complete
'''
ENTER_YOUR_CLIENT_ID = '\nEnter your Client ID: '
ENTER_YOUR_CLIENT_SECRET = '\nEnter your Client Secret: '
IS_NOT_A_VALID_CLIENT_ID = '''

{0}

Is not a valid Client ID.

Please make sure you are following the directions exactly and that there are no extra spaces in your Client ID.
'''
IS_NOT_A_VALID_CLIENT_SECRET = '''

{0}

Is not a valid Client Secret.

Please make sure you are following the directions exactly and that there are no extra spaces in your Client Secret.
'''
TRUST_GAM_CLIENT_ID = '''
It's important to mark the {0} Client ID as trusted by your Workspace instance.

Please go to:

  https://admin.google.com/ac/owl/list?tab=configuredApps

1. Click on: Configure new app
2. Enter the following Client ID value in Search for app:

  {1}

3. Press Search, select the {0} app, click
4. Keep the default scope or select a preferred scope that includes your GAM admin.
5. Press Continue
6. Select Trusted radio button, press Continue and Finish.
7. Press Confirm if Confirm parental consent pops up
8. Press enter here on the terminal once trust is complete.
'''

ENABLE_SERVICE_ACCOUNT_PRIVATE_KEY_UPLOAD = '''
Your workspace is configured to disable service account private key uploads.

Please go to:

  https://github.com/GAM-team/GAM/wiki/Authorization#authorize-service-account-key-uploads

Follow the steps to allow a service account private key upload for the project ({0}) just created.
Once those steps are completed, you can continue with your project authentication.
'''

YOUR_GAM_PROJECT_IS_CREATED_AND_READY_TO_USE = '''
That\'s it! Your GAM Project is created and ready to use.
Proceed to the authentication steps.
'''

# check|update service messages in order of appearance
SYSTEM_TIME_STATUS = 'System time status'
YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE = 'Your system time differs from {0} by {1}'
PRESS_ENTER_ONCE_AUTHORIZATION_IS_COMPLETE = 'Press enter once authorization is complete.'
SERVICE_ACCOUNT_API_DISABLED = '{0} not enabled. Please run "gam update project" and "gam user user@domain.com update serviceaccount"'
SERVICE_ACCOUNT_PRIVATE_KEY_AUTHENTICATION = 'Service Account Private Key Authentication'
SERVICE_ACCOUNT_CHECK_PRIVATE_KEY_AGE = 'Service Account Private Key age; Google recommends rotating keys on a routine basis'
SERVICE_ACCOUNT_PRIVATE_KEY_AGE = 'Service Account Private Key age: {0} days'
SERVICE_ACCOUNT_SKIPPING_KEY_AGE_CHECK = 'Skipping Private Key age check: {0} rotation not necessary'
UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS = 'Please run "gam update project" to view/manage service account keys'
DOMAIN_WIDE_DELEGATION_AUTHENTICATION = 'Domain-wide Delegation authentication'
SCOPE_AUTHORIZATION_PASSED = '''All scopes PASSED!

Service Account Client name: {0} is fully authorized.
'''
SCOPE_AUTHORIZATION_UPDATE_PASSED = '''All scopes PASSED!
To authorize them (in case some scopes were unselected), please go to the following link in your browser:
{0}
    {1}

You will be directed to the Google Workspace admin console Security > API Controls > Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.
'''
SCOPE_AUTHORIZATION_FAILED = '''Some scopes FAILED!
To authorize them, please go to the following link in your browser:
{0}
    {1}

You will be directed to the Google Workspace admin console Security > API Controls > Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.
'''
# General messages
ACCESS_FORBIDDEN = 'Access Forbidden'
ACTION_APPLIED = 'Action Applied'
ACTION_IN_PROGRESS = 'Action {0} in progress'
ACTION_MAY_BE_DELAYED = 'Action may be delayed'
ADMIN_STATUS_CHANGED_TO = 'Admin Status Changed to'
ALL = 'All'
ALL_FOLDER_NAMES_MUST_BE_NON_BLANK = 'All folder names must be non-blank: {0}'
ALL_SKU_PRODUCTIDS_MUST_MATCH = 'All SKU productIds must match, {0} != {1}'
ALREADY_WAS_OWNER = 'Already was owner'
ALREADY_EXISTS = 'Already exists'
ALREADY_EXISTS_IN_TARGET_FOLDER = 'Already exists in {0}: {1}'
ALREADY_EXISTS_USE_MERGE_ARGUMENT = 'Already exists; use the "merge" argument to merge the labels'
API_ACCESS_DENIED = 'API access Denied'
API_CALLS_RETRY_DATA = 'API calls retry data\n'
API_CHECK_CLIENT_AUTHORIZATION = 'Please make sure the Client ID: {0} is authorized for the appropriate API or scopes:\n{1}\n\nRun: gam oauth create\n'
API_CHECK_SVCACCT_AUTHORIZATION = 'Please make sure the Service Account Client ID: {0} is authorized for the appropriate API or scopes:\n{1}\n\nRun: gam user {2} update serviceaccount\n'
API_ERROR_SETTINGS = 'API error, some settings not set'
ARE_BOTH_REQUIRED = 'Arguments {0} and {1} are both required'
ARE_MUTUALLY_EXCLUSIVE = 'Arguments {0} and {1} are mutually exclusive'
AS = 'as'
ATTENDEES_ADD = 'Add Attendees'
ATTENDEES_ADD_REMOVE = 'Add/Remove Attendees'
ATTENDEES_REMOVE = 'Remove Attendees'
AUTHORIZATION_FILE_ALREADY_EXISTS = '{0} already exists. Please delete or rename it before attempting to {1} project.'
AUTHENTICATION_FLOW_COMPLETE = '\nThe authentication flow has completed.'
AUTHENTICATION_FLOW_COMPLETE_CLOSE_BROWSER = 'The authentication flow has completed. You may close this browser window and return to {0}.'
AUTHENTICATION_FLOW_FAILED = 'The authentication flow failed, reissue command'
BAD_ENTITIES_IN_SOURCE = '{0} {1} {2} in source marked >>> <<< above'
BAD_REQUEST = 'Bad Request'
BATCH = 'Batch'
BATCH_CSV_LOOP_DASH_DEBUG_INCOMPATIBLE = '"gam {0} - ..." is not compatible with debugging. Disable debugging by setting debug_level = 0 in gam.cfg'
BATCH_CSV_PROCESSING_COMPLETE = '{0},0/{1},Processing complete\n'
BATCH_CSV_TERMINATE_N_PROCESSES = '{0},0/{1},Terminating {2} running {3}\n'
BATCH_CSV_WAIT_LIMIT = ', wait limit {0} seconds'
BATCH_CSV_WAIT_N_PROCESSES = '{0},0/{1},Waiting for {2} running {3} to finish before terminating{4}\n'
BATCH_NOT_PROCESSED_ERRORS = '{0}batch file: {1}, not processed, {2} {3}\n'
CALLING_GCLOUD_FOR_REAUTH = 'Calling gcloud for reauth credentials..."\n'
CAN_NOT_DELETE_USER_WITH_VAULT_HOLD = '{0}: The user may be (or have recently been) on Google Vault Hold and thus not eligible for deletion. You can check holds with "gam user {1} show vaultholds".'
CAN_NOT_BE_SPECIFIED_MORE_THAN_ONCE = 'Argument {0} can not be specified more than once'
CHAT_ADMIN_ACCESS_LIMITED_TO_ONE_USER = 'Chat adminaccess|asadmin limited to one user, {0} specified'
CHROME_TARGET_VERSION_FORMAT = r'^([a-z]+)-(\d+)$ or ^(\d{1,4}\.){1,4}$'
COLUMN_DOES_NOT_MATCH_ANY_INPUT_COLUMNS = '{0} column "{1}" does not match any input columns'
COLUMN_DOES_NOT_MATCH_ANY_OUTPUT_COLUMNS = '{0} column "{1}" does not match any output columns'
COMMAND_NOT_COMPATIBLE_WITH_ENABLE_DASA = 'gam {0} {1} is not compatible with enable_dasa = true in gam.cfg'
COMMIT_BATCH_COMPLETE = '{0},0/{1},commit-batch - running {2} finished, proceeding\n'
COMMIT_BATCH_WAIT_N_PROCESSES = '{0},0/{1},commit-batch - waiting for {2} running {3} to finish before proceeding\n'
CONFIRM_WIPE_YUBIKEY_PIV = 'This will wipe all YubiKey PIV keys and configuration from your YubiKey. Are you sure? (y/N) '
CONTACT_ADMINISTRATOR_FOR_PASSWORD = 'Contact administrator for password'
CONTACT_PHOTO_NOT_FOUND = 'Contact photo not found'
CONTAINS_AT_LEAST_1_ITEM = 'Contains at least 1 item'
COUNT_N_EXCEEDS_MAX_TO_PROCESS_M = 'Count {0} exceeds maximum to {1} {2}'
CORRUPT_FILE = 'Corrupt file'
COULD_NOT_FIND_ANY_YUBIKEY = 'Could not find any YubiKey\n'
COULD_NOT_FIND_YUBIKEY_WITH_SERIAL = 'Could not find YubiKey with serial number {0}\n'
CREATE_USER_NOTIFY_MESSAGE = 'Hello #givenname# #familyname#,\n\nYou have a new account at #domain#\nAccount details:\nUsername: #user#\nPassword: #password#\nStart using your new account by signing in at\nhttps://www.google.com/accounts/AccountChooser?Email=#user#&continue=https://workspace.google.com/dashboard\n'
CREATE_USER_NOTIFY_SUBJECT = 'Welcome to #domain#'
CSV_DATA_ALREADY_SAVED = 'CSV data already saved'
CSV_FILE_HEADERS = 'The CSV file ({0}) has the following headers:\n'
CSV_SAMPLE_COMMANDS = 'Here are the first {0} commands {1} will run\n'
DATA_FIELD_MISMATCH = 'datafield {0} does not match saved datafield {1}'
DATA_TRANSFER_COMPLETED = 'Data Transfer completed: {0}\n'
DATA_UPLOADED_TO_DRIVE_FILE = 'Data uploaded to Drive File'
DEFAULT_SMIME = 'Default S/MIME'
DELETED = 'Deleted'
DEVICE_LIST_BUG = 'GAM hit Google internal bug 237397223. Please file a Google Support ticket stating that you are encountering this bug.'
DEVICE_LIST_BUG_WORKAROUND_NOT_POSSIBLE = 'GAM workaround for this issue only works if orderby argument is not used and query does not contain \'register\'.'
DEVICE_LIST_BUG_ATTEMPTING_WORKAROUND = 'GAM is attempting to work around the bug by filtering for devices created on or after the newest we\'ve seen ({0})...\n'
DIRECTLY_IN_THE = ' directly in the {0}'
DISABLE_TLS_MIN_MAX = 'Execute: gam select default config tls_max_version "" tls_min_version "" save\n'
DISPLAYNAME_NOT_ALLOWED_WHEN_UPDATING_MULTIPLE_SCHEMAS = 'displayname not allowed when updating multiple schemas'
DOES_NOT_EXIST = 'Does not exist'
DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT = '{0}: {1}, Does not exist or has invalid format, {2}'
DOES_NOT_MATCH = 'Does not match {0}'
DOMAIN_NOT_FOUND_IN_DNS = 'Domain not found in DNS!'
DOMAIN_NOT_VERIFIED_SECONDARY = 'Domain is not a verified secondary domain'
DONE_GENERATING_PRIVATE_KEY_AND_PUBLIC_CERTIFICATE = 'Done generating private key and public certificate'
DO_NOT_EXIST = 'Do not exist'
DOWNLOADING_AGAIN_AND_OVER_WRITING = 'Downloading again and over-writing...'
DUPLICATE = 'Duplicate'
DUPLICATE_ALREADY_A_ROLE = 'Duplicate, already a {0}'
DYNAMIC_GROUP_MEMBERSHIP_CANNOT_BE_MODIFIED = 'Dynamic group membership cannot be modified'
EITHER = 'Either'
EMAIL_ADDRESS_IS_UNMANAGED_ACCOUNT = 'The email address is an unmanaged account'
ENABLE_PROJECT_APIS_AUTOMATICALLY_OR_MANUALLY = 'Do you want to enable project APIs [a]utomatically or [m]anually? (a/m): '
ENTER_GSUITE_ADMIN_EMAIL_ADDRESS = '\nEnter your Google Workspace admin email address? '
ENTER_MANAGE_GCP_PROJECT_EMAIL_ADDRESS = '\nEnter your Google Workspace admin or GCP project manager email address authorized to manage project(s): {0}? '
ENTER_VERIFICATION_CODE_OR_URL = 'Enter verification code or paste "Unable to connect" URL from other computer (only URL data up to &scope required): '
ENTITY_DOES_NOT_EXIST = '{0} does not exist'
ENTITY_NAME_NOT_VALID = 'Entity Name Not Valid'
ERROR = 'error'
ERRORS = 'errors'
EVENT_IS_CANCELED = 'Event is canceled'
EXECUTE_GAM_OAUTH_CREATE = '\nPlease run\n\ngam oauth delete\ngam oauth create\n\n'
EXISTS = 'Exists'
EXPECTED = 'Expected'
EXPORT_NOT_COMPLETE = 'Export needs to be complete before downloading, current status is: {0}'
EXTRACTING_PUBLIC_CERTIFICATE = 'Extracting public certificate'
FAILED_PRECONDITION = 'Failed precondition'
FAILED_TO_PARSE_AS_JSON = 'Failed to parse as JSON'
FAILED_TO_PARSE_AS_LIST = 'Failed to parse as list'
FIELD_NOT_FOUND_IN_SCHEMA = 'Field {0} not found in schema {1}'
FILE_NOT_FOUND = 'File {0} not found'
FINISHED = 'Finished'
FILTER_CAN_ONLY_CONTAIN_ONE_CATEGORY_LABEL = 'Filter can only contain one CATEGORY label'
FILTER_CAN_ONLY_CONTAIN_ONE_USER_LABEL = 'Filter can only contain one USER label'
FOR = 'for'
FORBIDDEN = 'Forbidden'
FORMAT_NOT_AVAILABLE = 'Format ({0}) not available'
FORMAT_NOT_DOWNLOADABLE = 'Format not downloadable'
FROM = 'From'
FROM_LC = 'from'
FULL_PATH_MUST_START_WITH_DRIVE = 'fullpath must start with {0} or {1}'
GAM_BATCH_FILE_WRITTEN = 'GAM batch file {0} written\n'
GAM_LATEST_VERSION_NOT_AVAILABLE = 'GAM Latest Version information not available'
GAM_OUT_OF_MEMORY = 'GAM has run out of memory. If this is a large Google Workspace instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
GENERATING_NEW_PRIVATE_KEY = 'Generating new private key'
GETTING = 'Getting'
GETTING_ALL = 'Getting all'
GRANTING_RIGHTS_TO_ROTATE_ITS_OWN_PRIVATE_KEY = '{0} rights to rotate its own private key'
GOOGLE_DELEGATION_ERROR = 'Google delegation error, delegator and delegate both exist and are valid for delegation'
GOT = 'Got'
GROUP_MAPS_TO_MULTIPLE_OUS = 'File: {0}, Group: {1} references multiple OUs: {2}'
GROUP_MAPS_TO_OU_INVALID_ROW = 'File: {0}, Invalid row, must contain non-blank <EmailAddress> and <OrgUnitPath>: <{1}> <{2}>'
GUARDIAN_INVITATION_STATUS_NOT_PENDING = 'Guardian invitation status is not PENDING'
HAS_CHILD_ORGS = 'Has child {0}'
HAS_INVALID_FORMAT = '{0}: {1}, Has invalid format'
HEADER_NOT_FOUND_IN_CSV_HEADERS = 'Header "{0}" not found in CSV headers of "{1}".'
HELP_SYNTAX = 'Help: Syntax in file {0}\n'
HELP_WIKI = 'Help: Documentation is at {0}\n'
IGNORED = 'Ignored'
INSTRUCTIONS_CLIENT_SECRETS_JSON = 'Please run\n\ngam create|use project\ngam oauth create\n\nto create and authorize a Client account.\n'
INSTRUCTIONS_OAUTH2SERVICE_JSON = 'Please run\n\ngam create|use project\ngam user <user> update serviceaccount\n\nto create and authorize a Service account.\n'
INSUFFICIENT_PERMISSIONS_TO_PERFORM_TASK = 'Insufficient permissions to perform this task'
INTER_BATCH_WAIT_INCREASED = 'inter_batch_wait increased to {0:.2f}'
INVALID = 'Invalid'
INVALID_ALIAS = 'Invalid Alias'
INVALID_ATTENDEE_CHANGE = 'Invalid attendee change "{0}"'
INVALID_CHARSET = 'Invalid charset "{0}"'
INVALID_DATE_TIME_RANGE = '{0} {1} must be greater than/equal to {2} {3}'
INVALID_ENTITY = 'Invalid {0}, {1}'
INVALID_FILE_SELECTION_WITH_ADMIN_ACCESS = 'Invalid file selection with adminaccess|asadmin'
INVALID_GROUP = 'Invalid Group'
INVALID_HTTP_HEADER = 'Invalid http header data: {0}'
INVALID_JSON_INFORMATION = 'Google API reported Invalid JSON Information'
INVALID_JSON_SETTING = 'Invalid JSON setting'
INVALID_LIST = 'Invalid list'
INVALID_MEMBER = 'Invalid Member address'
INVALID_MESSAGE_ID = 'Invalid message id(s)'
INVALID_MIMETYPE = 'Invalid mimeType {0}, must be {1}'
INVALID_NUMBER_OF_CHAT_SPACE_MEMBERS = '{0} type {1} number of members, {2}, must be in range {3} to {4}'
INVALID_ORGUNIT = 'Invalid Organizational Unit'
INVALID_PATH = 'Invalid Path'
INVALID_PERMISSION_ATTRIBUTE_TYPE = 'permission attribute {0} not allowed with type {1}'
INVALID_REGION = 'See: https://github.com/GAM-team/GAM/wiki/Context-Aware-Access-Levels#caa-region-codes'
INVALID_QUERY = 'Invalid Query'
INVALID_RE = 'Invalid RE'
INVALID_REQUEST = 'Invalid Request'
INVALID_RESELLER_CUSTOMER_NAME = 'name must be: accounts/<ResellerID>/customers/<ChannelCustomerID>'
INVALID_ROLE = 'Invalid subkeyfield Role, must be one of: {0}'
INVALID_SCHEMA_VALUE = 'Invalid Schema Value'
INVALID_SCOPE = 'Invalid Scope'
INVALID_SITE = 'Invalid Site ({0}), must match pattern ({1})'
INVALID_TAG_SPECIFICATION = 'Invalid tag, expected field.subfield or field.subfield.subfield.string'
INVALID_TIMEOFDAY_RANGE = '{0} must be less than/equal to {1}'
IN_SKIPIDS = 'In skipids'
IN_THE = ' in the {0}'
IN_TRASH_AND_EXCLUDE_TRASHED = 'In Trash and excludeTrashed'
IS_EXPIRED_OR_REVOKED = '{0}: {1}, Is expired or has been revoked'
IS_NOT_DONE_CHECKING_IN_SECONDS = 'Is not done, checking again in {0} seconds'
IS_NOT_UNIQUE = 'Is not unique, {0}: {1}'
IS_REQD_TO_CHG_PWD_NO_DELEGATION = 'Is required to change password at next login. You must change password or clear changepassword flag for delegation.'
IS_SUSPENDED_NO_BACKUPCODES = 'User is suspended. You must unsuspend to process backupcodes'
IS_SUSPENDED_NO_DELEGATION = 'Is suspended. You must unsuspend for delegation.'
IS_YUBIKEY_INSERTED = 'Is YubiKey inserted?'
JSON_ERROR = 'JSON error "{0}" in file {1}'
JSON_KEY_NOT_FOUND = 'JSON key "{0}" not found in file {1}'
KIOSK_MODE_REQUIRED = ' This command ({0}) requires that the ChromeOS device be in Kiosk mode.'
LESS_THAN_1_SECOND = 'less than 1 second'
LIST_CHROMEOS_INVALID_INPUT_PAGE_TOKEN_RETRY = 'List ChromeOSdevices Invalid Input: pageToken retry'
LOGGING_INITIALIZATION_ERROR = 'Logging initialization error: {0}'
LOOKING_UP_GOOGLE_UNIQUE_ID = 'Looking up Google Unique ID'
MARKED_AS = 'Marked as'
MATCHED_THE_FOLLOWING = 'Matched the following'
MATTER_NOT_OPEN = 'Matter needs to be open, current state is: {0}'
MAXIMUM_OF = 'maximum of'
MEMBERSHIP_IS_PENDING_WILL_DELETE_ADD_TO_ACCEPT = 'Membership is pending, will delete and add to accept'
MIMETYPE_MISMATCH = 'Shortcut target mimeType {0} does not match actual target mimeType {1}'
MIMETYPE_NOT_PRESENT_IN_ATTACHMENT = 'MIME type not present in attachment'
MISMATCH_RE_SEARCH_REPLACE_SUBFIELDS = 'The subfield ({2}) in replace "{3}" exceeds the number of subfields ({0}) in search "{1}"'
MISMATCH_SEARCH_REPLACE_SUBFIELDS = 'The number of subfields ({0}) in search "{1}" does not match the number of subfields ({2}) in replace "{3}"'
MISSING_FIELDS = 'Missing fields: {0}\n'
MULTIPLE_BUILDINGS_SAME_NAME = '{0} {1} with the same (case-insensitive) name exist'
MULTIPLE_ENTITIES_FOUND = 'Multiple {0} ({1}) found, {2}'
MULTIPLE_ITEMS_SPECIFIED = 'Multiple {0} are specfied, only one is allowed'
MULTIPLE_ITEMS_MARKED_PRIMARY = 'Multiple {0} are marked primary, only one can be primary'
MULTIPLE_PARENTS_SPECIFIED = 'Multiple parents ({0}) specified, only one is allowed'
MULTIPLE_SEARCH_METHODS_SPECIFIED = 'Multiple search methods ({0}) specified, only one is allowed'
MULTIPLE_SSO_PROFILES_MATCH = 'Multiple SSO profiles match display name {0}:\n'
MULTIPLE_YUBIKEYS_CONNECTED = 'Multiple YubiKeys connected. Specify yubikey_serial_number and one of {0}\n'
MUST_BE_NUMERIC = 'Must be numeric'
NEED_READ_ACCESS = 'Need Read access'
NEED_READ_WRITE_ACCESS = 'Need Read/Write access'
NEED_WRITE_ACCESS = 'Need Write access'
NESTED_LOOP_CMD_NOT_ALLOWED = 'Command can not be nested.'
NEWUSER_REQUIREMENTS = 'newuser option requires: at least 1 recipient and givenname, familyname and password options'
NEW_OWNER_MUST_DIFFER_FROM_OLD_OWNER = 'New owner must differ from old owner'
NO_DATA = 'No data'
NON_BLANK = 'Non-blank'
NON_EMPTY = 'Non-empty'
NOT_A = 'Not a'
NOT_A_PRIMARY_EMAIL_ADDRESS = 'Not a primary email address'
NOT_A_MEMBER = 'Not a member'
NOT_ACTIVE = 'Not Active'
NOT_ALLOWED = 'Not Allowed'
NOT_AN_ENTITY = 'Not a {0}'
NOT_APPROPRIATE = 'Not Appropriate'
NOT_COMPATIBLE = 'Not Compatible'
NOT_COPYABLE = 'Not Copyable'
NOT_COPYABLE_INTO_ITSELF = 'Not copyable into itself'
NOT_COPYABLE_SAME_NAME_CURRENT_FOLDER_MERGE = 'Not copyable with same name into current folder with duplicatefolders merge'
NOT_COPYABLE_SAME_NAME_CURRENT_FOLDER_OVERWRITE = 'Not copyable with same name into current folder with duplicatefiles overwriteall|overwriteolder'
NOT_DELETABLE = 'Not Deletable'
NOT_FOUND = 'Not Found'
NOT_MOVABLE = 'Not Movable'
NOT_MOVABLE_IN_TRASH = 'Not Movable, in Trash'
NOT_MOVABLE_INTO_ITSELF = 'Not movable into itself'
NOT_MOVABLE_SAME_NAME_CURRENT_FOLDER_MERGE = 'Not movable with same name into current folder with duplicatefolders merge'
NOT_MOVABLE_SAME_NAME_CURRENT_FOLDER_OVERWRITE = 'Not movable with same name into current folder with duplicatefiles overwriteall|overwriteolder'
NOT_OWNED_BY = 'Not owned by {0}'
NOT_SELECTED = 'Not Selected'
NOT_WRITABLE = 'Not Writable'
NOW_THE_PRIMARY_DOMAIN = 'Now the primary domain'
NO_ACTION_SPECIFIED = 'No action specified'
NO_AVAILABLE_LICENSES = "There aren't enough available licenses for the specified product-SKU pair(s)"
NO_CHANGES = 'No changes'
NO_CLIENT_ACCESS_ALLOWED = 'No Client Access allowed'
NO_CLIENT_ACCESS_CREATE_UPDATE_ALLOWED = 'No Client Access create/update allowed'
NO_COLUMNS_SELECTED_WITH_CSV_OUTPUT_HEADER_FILTER = 'No columns selected with {0} and {1}'
NO_CREDENTIALS_REPLACEMENT = '{0}: {1} has {2} {3}. We only replace if there are 2.\n'
NO_CSV_DATA_TO_UPLOAD = 'No CSV data to upload'
NO_CSV_FILE_DATA_FOUND = 'No CSV file data found'
NO_CSV_FILE_DATA_SAVED = 'No CSV file data saved'
NO_CSV_FILE_SUBKEYS_SAVED = 'No CSV file subkeys saved'
NO_DATA_TRANSFER_APP_FOR_PARAMETER = 'No data transfer application for key {0}'
NO_ENTITIES_FOUND = 'No {0} found'
NO_ENTITIES_MATCHED = 'No {0} matched'
NO_FILTER_ACTIONS = 'No {0} actions specified'
NO_FILTER_CRITERIA = 'No {0} criteria specified'
NO_LABELS_MATCH = 'No Labels match'
NO_LABELS_TO_PROCESS = 'No Labels to process'
NO_MESSAGES_WITH_LABEL = 'No Messages with Label'
NO_PARENTS_TO_CONVERT_TO_SHORTCUTS = 'No parents to convert to shortcuts'
NO_REPORT_AVAILABLE = 'No {0} report available.'
NO_SCOPES_FOR_API = 'There are no scopes authorized for the {0}'
NO_SERIAL_NUMBERS_SPECIFIED = 'No serial numbers specified'
NO_SSO_PROFILE_MATCHES = 'No SSO profile matches display name {0}'
NO_SSO_PROFILE_ASSIGNED = 'No SSO profile assigned to {0} {1}'
NO_SVCACCT_ACCESS_ALLOWED = 'No Service Account Access allowed'
NO_TRANSFER_LACK_OF_DISK_SPACE = 'Transfer not performed due to lack of target drive space.'
NO_USAGE_PARAMETERS_DATA_AVAILABLE = 'No usage parameters data available.'
NO_USER_COUNTS_DATA_AVAILABLE = 'No User counts data available.'
OAUTH2_GO_TO_LINK_MESSAGE = """
Go to the following link in a browser on this computer or on another computer:

    {url}

If you use a browser on another computer, you will get a browser error that the site can't be reached AFTER you
click the Allow button, paste "Unable to connect" URL from other computer (only URL data up to &scope required):
"""
ON_CURRENT_PRIVATE_KEY = ' on current key'
ON_VAULT_HOLD = 'On Google Vault Hold'
ONLY_ADMINISTRATORS_CAN_PERFORM_SHARED_DRIVE_QUERIES = 'Only administrators can perform Shared Drive queries'
ONLY_ADMINISTRATORS_CAN_SPECIFY_SHARED_DRIVE_ORGUNIT = 'Only administrators can specify Shared Drive Org Unit'
ONLY_ONE_DEVICE_SELECTION_ALLOWED = 'Only one device selection allowed, filter = "{0}"'
ONLY_ONE_JSON_RANGE_ALLOWED = 'Only one range/json allowed'
ONLY_ONE_OWNER_ALLOWED = 'Only one owner allowed'
OR = 'or'
OU_AND_MOVETOOU_CANNOT_BE_IDENTICAL = 'ou {0} can not be be identical to movetoou {1}'
OU_SUBOUS_CANNOT_BE_MOVED_TO_MOVETOOU = 'ou {0} sub OUs can not be be moved to movetoou {1}'
PERMISSION_DENIED = 'The caller does not have permission'
PLEASE_CORRECT_YOUR_SYSTEM_TIME = 'Please correct your system time.'
PLEASE_ENTER_A_OR_M = 'Please enter a or m ...\n'
PLEASE_SELECT_ENTITY_TO_PROCESS = '{0} {1} found, please select the correct one to {2} and specify with {3}'
PLEASE_SPECIFY_BUILDING_EXACT_CASE_NAME_OR_ID = 'Please specify building by exact case name or ID.'
PREVIEW_ONLY = 'Preview Only'
PRIMARY_EMAIL_DID_NOT_MATCH_PATTERN = 'primaryEmail address did not match pattern: {0}'
PROCESS = 'process'
PROCESSES = 'processes'
PROCESSING_ITEM_N = '{0},0,Processing item {1}\n'
PROCESSING_ITEM_N_OF_M = '{0},0,Processing item {1}/{2}\n'
PROFILE_PHOTO_NOT_FOUND = 'Profile photo not found'
PROFILE_PHOTO_IS_DEFAULT = 'Profile photo is default'
REASON_ONLY_VALID_WITH_CONTENTRESTRICTIONS_READONLY_TRUE = 'reason only valid with contentrestrictions readonly true'
REAUTHENTICATION_IS_NEEDED = 'Reauthentication is needed, please run\n\ngam oauth create'
RECOMMEND_RUNNING_GAM_ROTATE_SAKEY = 'Recommend running "gam rotate sakey" to get a new key\n'
REFUSING_TO_DEPROVISION_DEVICES = 'Refusing to deprovision {0} devices because acknowledge_device_touch_requirement not specified.\nDeprovisioning a device means the device will have to be physically wiped and re-enrolled to be managed by your domain again.\nThis requires physical access to the device and is very time consuming to perform for each device.\nPlease add "acknowledge_device_touch_requirement" to the GAM command if you understand this and wish to proceed with the deprovision.\nPlease also be aware that deprovisioning can have an effect on your device license count.\nSee https://support.google.com/chrome/a/answer/3523633 for full details.'
REPLY_TO_CUSTOM_REQUIRES_EMAIL_ADDRESS = 'replyto REPLY_TO_CUSTOM requires customReplyTo <EmailAddress>'
REQUEST_COMPLETED_NO_FILES = 'Request completed but no results/files were returned, try requesting again'
REQUEST_NOT_COMPLETE = 'Request needs to be completed before downloading, current status is: {0}'
RERUN_THE_COMMAND_AND_SPECIFY_A_NEW_SANAME = """
Re-run the command specify a new service account name with: saname <ServiceAccountName>
See: https://github.com/GAM-team/GAM/wiki/Authorization#advanced-use
"""
RESOURCE_CAPACITY_FLOOR_REQUIRED = 'Options "capacity <Number>" (<Number> > 0) and "floor <String>" required'
RESOURCE_FLOOR_REQUIRED = 'Option "floor <String>" required'
RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = 'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
RETRIES_EXHAUSTED = 'Retries {0} exhausted'
RETRYING_GOOGLE_SHEET_EXPORT_SLEEPING = 'Retrying Google Sheet export {0}/{1}. Sleeping {2} seconds\n'
ROLE_MUST_BE_ORGANIZER = 'Role must be organizer'
ROLE_NOT_IN_SET = 'Role not in set: {0})'
SCHEMA_WOULD_HAVE_NO_FIELDS = '{0} would have no {1}'
SELECTED = 'Selected'
SERVICE_NOT_APPLICABLE = 'Service not applicable/Does not exist'
SERVICE_NOT_APPLICABLE_THIS_ADDRESS = 'Service not applicable for this address: {0}'
SERVICE_NOT_ENABLED = '{0} Service/App not enabled'
SHORTCUT_TARGET_CAPABILITY_IS_FALSE = '{0} capability {1} is False'
SITES_COMMAND_DEPRECATED = 'The Classic Sites API is deprecated, this command will not work:\n{0}'
SKU_HAS_NO_MATCHING_ARCHIVED_USER_SKU = 'SKU {0} has no matching Archived User SKU'
STARTING_THREAD = 'Starting thread'
STATISTICS_COPY_FILE = 'Total: {0}, Copied: {1}, Shortcut created {2}, Shortcut exists {3}, Duplicate: {4}, Copy Failed: {5}, Not copyable: {6}, In skipids: {7}, Permissions Failed: {8}, Protected Ranges Failed: {9}'
STATISTICS_COPY_FOLDER = 'Total: {0}, Copied: {1}, Shortcut created {2}, Shortcut exists {3}, Duplicate: {4}, Merged: {5}, Copy Failed: {6}, Not writable: {7}, Permissions Failed: {8}'
STATISTICS_MOVE_FILE = 'Total: {0}, Moved: {1}, Shortcut created {2}, Shortcut exists {3}, Duplicate: {4}, Move Failed: {5}, Not movable: {6}'
STATISTICS_MOVE_FOLDER = 'Total: {0}, Moved: {1}, Shortcut created {2}, Shortcut exists {3}, Duplicate: {4}, Merged: {5}, Move Failed: {6}, Not writable: {7}'
STATISTICS_USER_NOT_ORGANIZER = 'User not organizer: {0}'
STRING_LENGTH = 'string length'
SUBKEY_FIELD_MISMATCH = 'subkeyfield {0} does not match saved subkeyfield {1}'
SUBSCRIPTION_NOT_FOUND = 'Could not find subscription'
SUFFIX_NOT_ALLOWED_WITH_CUSTOMLANGUAGE = 'Suffix {0} not allowed with customLanguage {1}'
TASKLIST_TITLE_NOT_FOUND = 'Task list title not found'
THREAD = 'thread'
THREADS = 'threads'
TO = 'To'
TO_LC = 'to'
TO_MAXIMUM_OF = 'to maximum of'
TO_SET_UP_GOOGLE_CHAT = """
To set up Google Chat for your API project, please go to:

    {0}

and follow the instructions at:

    https://github.com/GAM-team/GAM/wiki/Chat-Bot#set-up-a-chat-bot
"""
TOTAL_ITEMS_IN_ENTITY = 'Total {0} in {1}'
TRIMMED_MESSAGE_FROM_LENGTH_TO_MAXIMUM = 'Trimmed message of length {0} to maximum length {1}'
UNABLE_TO_GET_PERMISSION_ID = 'Unable to get Permission ID for <{0}>'
UNABLE_TO_CREATE_NOT_FOUND_USER = 'Unable to create not found user, some required field (givenName, familyName, password/notfoundpassword) not present'
UNAVAILABLE = 'Unavailable'
UNKNOWN = 'Unknown'
UNKNOWN_API_OR_VERSION = 'Unknown Google API or version: ({0}), contact {1}'
UNRECOVERABLE_ERROR = 'Unrecoverable error'
UPDATE_ATTENDEE_CHANGES = 'Update attendee changes'
UPDATE_GAM_TO_64BIT = "You're running a 32-bit version of GAM on a 64-bit version of Windows, upgrade to a windows-x86_64 version of GAM"
UPDATE_USER_PASSWORD_CHANGE_NOTIFY_MESSAGE = 'The account password for #givenname# #familyname#, #user# has been changed to: #password#\n'
UPDATE_USER_PASSWORD_CHANGE_NOTIFY_SUBJECT = 'Account #user# password has been changed'
UPLOAD_CSV_FILE_INTERNAL_ERROR = 'Google reported "{0}" but the file was probably uploaded, check that it has {1} rows'
UPLOADING_NEW_PUBLIC_CERTIFICATE_TO_GOOGLE = 'Uploading new public certificate to Google...\n'
URL_ERROR = 'URL error: {0}'
USE_MIMETYPE_TO_SPECIFY_GOOGLE_FORMAT = 'Use "mimetype <MimeType>" to specify Google file format\n'
USED = 'Used'
USER_BELONGS_TO_N_GROUPS_THAT_MAP_TO_ORGUNITS = 'User belongs to {0} groups ({1}) that map to OUs'
USER_CANCELLED = 'User cancelled'
USER_HAS_MULTIPLE_DIRECT_OR_INHERITED_MEMBERSHIPS_IN_GROUP = 'User has multiple direct or inherited memberships in group'
USER_IN_OTHER_DOMAIN = '{0}: {1} in other domain.'
USER_IS_NOT_ORGANIZER = 'User is not organizer, use anyorganizer option to override'
USER_NOT_IN_MATCHUSERS = 'User not in matchusers'
USER_SUBS_NOT_ALLOWED_TAG_REPLACEMENT = 'user substitutions not allowed in replace <Tag> <String>'
USE_DOIT_ARGUMENT_TO_PERFORM_ACTION = 'Use the "doit" argument to perform action'
USING_N_PROCESSES = '{0},0/{1},Using {2} {3}...\n'
VALUES_ARE_NOT_CONSISTENT = 'Values are not consistent'
VERSION_UPDATE_AVAILABLE = 'Version update available'
WAITING_FOR_DATA_TRANSFER_TO_COMPLETE_SLEEPING = 'Waiting for Data Transfer to complete. Sleeping {0} seconds\n'
WAITING_FOR_ITEM_CREATION_TO_COMPLETE_SLEEPING = 'Waiting for {0} creation to complete. Sleeping {1} seconds\n'
WHAT_IS_YOUR_PROJECT_ID = '\nWhat is your project ID? '
WILL_RERUN_WITH_NO_BROWSER_TRUE = 'Will re-run command with no_browser true\n'
WITH = 'with'
WOULD_MAKE_MEMBERSHIP_CYCLE = 'Would make membership cycle'
WRITER_ACCESS_REQUIRED_TO_BOTH_CALENDARS = 'Writer access required to both calendars'
WROTE_PRIVATE_KEY_DATA = 'Wrote private key data to {0}\n'
WROTE_PUBLIC_CERTIFICATE = 'Wrote public certificate to {0}\n'
YOU_CAN_ADD_DOMAIN_TO_ACCOUNT = 'You can now add: {0} or its subdomains as secondary or domain aliases of the Google Workspace Account: {1}'
YUBIKEY_GENERATING_NONEXPORTABLE_PRIVATE_KEY = 'YubiKey is generating a non-exportable private key...\n'
YUBIKEY_PIN_SET_TO = 'YubiKey PIN set to: {0}\n'
