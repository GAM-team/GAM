# GAM Configuration
- [Introduction](#introduction)
- [Variables](#variables)
- [Multiple Computers](#multiple-computers)
- [Multiple Customers and Domains](#multiple-customers-and-domains)
- [Multiple Users-Projects on One Computer](#multiple-users-projects-on-one-computer)

## Introduction
GAM uses a configuration file, gam.cfg, to store the values of the various environment variables
and signal files used by Legacy GAM. Configuration files client_secrets.json, oauth2.txt, oauth2service.json and extra_args.txt
are moved to a version independent location. This should simplify upgrading GAM versions in the future.
Additionally, if you support multiple clients/domains or have multiple users running GAM,
gam.cfg lets you easily manage your configuration.

In the following discussion, these names will be used to refer to directories:
* OldGamPath: Location of previous version of gam.py or gam.exe
* GamPath: Location of new version of gam.py or gam.exe
* GamCfgDir: Location of gam.cfg
* GamConfigDir: Location of client_secrets.json, oauth2.txt, oauth2service.json and extra_args.txt
* GamCacheDir: Google API cache files
* GamDriveDir: Files downloaded with gam user <User> get drivefile <DriveFileID> when targetfolder <FilePath> is not specified

These are the default values that GAM uses.
* GamCfgDir: ~/.gam
* GamConfigDir: ~/.gam
* GamCacheDir: ~/.gam/gamcache
* GamDriveDir: ~/Downloads

If you are an existing GAM user and don't like the suggested locations or you already have some other scheme in use,
set the GAMCFGDIR environment variable to the desired path for gam.cfg. In gam.cfg, specify the desired values for the other locations.

How will gam.cfg be used? At its simplest, it is created once and you can ignore it.
Every once in a while, you edit gam.cfg to set some desired values and then you ignore it.
gam.cfg must be a plain text file, you can edit it with your favorite text editor (emacs, vi, TextWrangler,
TextEdit, Notepad, Wordpad) as long as you wind up with a plain text file.

If you are upgrading from Legacy GAM, set the environment variable OLDGAMPATH to OldGamPath. This is a one-time setting
to allow GAM to find your old signal files and to copy client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
from OldGamPath to GamConfigDir. To generate the initial gam.cfg, execute the command: gam select default verify.
Once gam.cfg is created, no signal files are read and the only environment variable used is GAMCFGDIR.
GAMFIGDIR does not have to be set unless you want a value other than ~/.gam for the location of gam.cfg.

## Variables
These are the gam.cfg variables; if GAM does not find a value for an environment variable, the default value is used.
If a signal file is located, the associated variable is set True, otherwise False.
(For debug.gam, debug_level is set to 1 if the file is located, otherwise 0.)
```
activity_max_results
        When retrieving lists of Google Drive activities from API,
        how many should be retrieved in each API call
        Default: 100
        Range: 1 - 500
admin_email
        Google Admin email address
        Default: Blank, address from OAUTH2.TXT will be used
        Environment variable: GA_ADMIN_EMAIL
api_calls_rate_check
        Should rate of Google API calls per 60 seconds be checked
        Default: False
api_calls_rate_limit
        Limit on number of Google API calls per 60 seconds
        Default: 1000
        Range: 100 - Unlimited
api_calls_tries_limit
        Limit the number of tries for Google API calls that return an error
        that indicates a retry should be performed
        Default: 10
        Range: 3-30
auto_batch_min
        Automatically generate gam batch command if number of users
        specified in gam users xxx command exceeds this number
        Default: 0, don't automatically generate gam batch commands
        Range: 0 - 100
        Environment variable: GAM_AUTOBATCH
bail_on_internal_error_tries
        When Google returns 'Internal error' error on an API call and
        experience has shown that retrying the call is unlikely to succeed,
        how many total tries should GAM perform before bailing out and reporting the error.
        Default: 2
        Range: 1 - 10
batch_size
        When processing items in batches, how many should be processed in each batch
        Default: 50
        Range: 1 - 1000
        Environment variable: GAM_BATCH_SIZE
cacerts_pem
        SSL Root CA certificates file
        Default: Blank, internal cacerts.pem will be used
        Environment variable: GAM_CA_FILE
cache_dir
        GAM cache directory.
        Default: ~/.gam/gamcache
        Environment variable: GAMCACHEDIR
cache_discovery_only
        If no_cache = True,
            no GAM API calls are cached.
        If no_cache = False and cache_discovery_only = False,
            all GAM API calls are cached.
        If no_cache = False and cache_discovery_only = True,
            only GAM discovery API calls are cached.
        The last combination caches GAM discovery API calls that usually return
        the same value without consuming large amounts of disc space as when
        all GAM API calls are cached.
        Signal file: OldGamPath/allcache.txt
channel_customer_id
        Cloud Channel Customer ID
        Default: Blank
charset
        Character set of gam batch, gam csv, gam loop files.
        Default: utf-8
        Environment variable: GAM_CHARSET
classroom_max_results
        When retrieving lists of Google Classroom items from API,
        how many should be retrieved in each API call
        Default: 0 (Google defined limit)
        Range: 0 - 1000
client_secrets_json
        Path to client_secrets.json
        Default: GamConfigDir/client_secrets.json
        Environment variable: CLIENTSECRETS
clock_skew_in_seconds
        Number of seconds of clock skew allowed between local time and Google time
        Default: 10
        Range: 10 - 3600
cmdlog
        Path to GAM Log file; there is no logging if cmdlog is empty.
        If cmdlog specifies a relative path, e.g., just a filename, it is appended to GamConfigDir.
        If cmdlog specifies a full path, it is used as is.
        Default: ''
cmdlog_max_backups
        Maximum number of backup log files
        Default: 5
        Range: 1 - 10
cmdlog_max_kilo_bytes
        Maximum kilobytes per log file
        Default: 1000
        Range: 100 - 10000
config_dir
        GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json
        and extra_args.txt
        Default: ~/.gam
        Environment variable: GAMUSERCONFIGDIR
contact_max_results
        When retrieving lists of Google Contacts from API,
        how many should be retrieved in each API call
        Default: 100
        Range: 1 - 10000
csv_input_column_delimiter
        Column delimiter used when reading CSV files; this must be a single character
        All places where an input CSV file can be specified have an
        argument columndelimiter <String> that can override this value.
        Default: ','
csv_input_no_escape_char
        When reading a CSV file, should `\` be ignored as an escape character.
        Set this to False if the input file data was written using `\` as an escape character.
        Default: True
csv_input_quote_char
        A one-character string used to quote fields containing special characters,
        such as the csv_input_column_delimiter or csv_input_quote_char, or newline characters.
        This is typically used when reading CSV files produced by gam print formatjson
        where csv_output_quote_char was set to a value other than double quote.
        Defaults: '"'
csv_input_row_drop_filter
        A list of expressions used to select specific rows based on column values
        for exclusion from the CSV file read by a gam csv command
        Default: ''
csv_input_row_drop_filter_mode
        Allowed values: allmatch|anymatch
        allmatch - all filters must match for exclusion from the CSV file read by a gam csv command
        anymatch - any filter must match for exclusion from the CSV file read by a gam csv command
        Default: 'anymatch'
csv_input_row_filter
        A list of expressions used to select specific rows based on column values
        for inclusion in the CSV file read by a gam csv command
        Default: ''
csv_input_row_filter_mode
        Allowed values: allmatch|anymatch
        allmatch - all filters must match for inclusion in the CSV file read by a gam csv command
        anymatch - any filter must match for inclusion in the CSV file read by a gam csv command
        Default: 'allmatch'
csv_input_row_limit
        A limit on the number of rows to read from a CSV file; a value of 0 sets no limit.
        The gam csv|loop commands have an option maxrows <Integer> that can override this value.
        Default: 0
csv_output_convert_cr_nl
        Convert carriage returns (CR) to '\r' and newlines (NL) to '\n' embedded
        in data fields when writing CSV files; embedded CR and LF characters can
        make processing CSV files difficult
        The commands gam print groups|messages|orgs|resources|sites|threads have
        an argument, convertcrnl, that can set this value to true to
        override csv_output_convert_cr_nl = False
        Default: False
csv_output_column_delimiter
        Column delimiter used when writing CSV files;
        this must be a single character
        The redirect csv <FileName> columndelimiter <Character> argument can
        override this value.
        Default: ','
csv_output_field_delimiter
        Field list delimiter used when writing CSV output files;
        this must be a single character
        Each of the gam print courses|groups|users  commands has a
        delimiter <String> argument that can override this value.
        Default: ' '
csv_output_header_drop_filter
        A list of <REMatchPatterns> used to select specific column headers
        for exclusion from the CSV file written by a gam print command
        Default: ''
csv_output_header_filter
        A list of <REMatchPatterns> used to select specific column headers
        for inclusion in the CSV file written by a gam print command
        Default: ''
csv_output_header_force
        A list of <Strings> used to specify the exact column headers
        for inclusion in the CSV file written by a gam print command
        Default: ''
csv_output_header_order
        A list of <Strings> used to specify the order of column headers
        for inclusion in the CSV file written by a gam print command
        Any headers in the file but not in the list will appear after
        the headers in the list
        Default: ''
csv_output_line_terminator
        Allowed values: cr, lf, crlf
        Designates character(s) used to terminate the lines of a CSV file.
        For Linux and Mac OS, this would typically be lf.
        For Windows, this would typically be crlf.
        Default: lf
csv_output_no_escape_char
        When writing a CSV file, should `\` be ignored as an escape character.
        Set this to True if the output file data is to be read by a non-Python program.
        Default: False
csv_output_quote_char
        A one-character string used to quote fields containing special characters,
        such as the csv_output_column_delimiter or csv_output_quote_char
        or new-line characters.
        The redirect csv <FileName> quotechar <Character> argument can
        override this value.
        This is most useful with gam print commands with formatjson where the
        JSON column contains many double quotes; by setting csv_output_quote_char
        to a single quote, the output is much cleaner. Google Sheets only recognizes
        double quote as the quote character so use this option only when writing
        to a local file.
        Default: '"'
csv_output_row_drop_filter
        A list of expressions used to select specific rows based on column values
        for exclusion from the CSV file written by a gam print command
        Default: ''
csv_output_row_drop_filter_mode
        Allowed values: allmatch|anymatch
        allmatch - all filters must match for exclusion from the CSV file written by a gam print command
        anymatch - any filter must match for exclusion from the CSV file written by a gam print command
        Default: 'anymatch'
csv_output_row_filter
        A list of expressions used to select specific rows based on column values
        for inclusion in the CSV file written by a gam print command
        Default: ''
csv_output_row_filter_mode
        Allowed values: allmatch|anymatch
        allmatch - all filters must match for inclusion in the CSV file written by a gam print command
        anymatch - any filter must match for inclusion in the CSV file written by a gam print command
        Default: 'allmatch'
csv_output_row_limit
        A limit on the number of rows to write to a CSV file; a value of 0 sets no limit.
        Default: 0
csv_output_sort_headers
        A list of column headers that causes GAM to sort CSV output rows by those headers.
        The column headers are case insensitive and if column header does not appear in the CSV output, it is ignored.
        Default: Blank
csv_output_subfield_delimiter
        Character used to delimit fields and subfields in headers when writing CSV files;
        this must be a single character
        Default: '.'
csv_output_timestamp_column
        The name of column to add to CSV output files that will contain a timestamp;
        the time will be expressed in the timezome specified in the timezone variable
        and will be formatted as specified in the todrive_timeformat variable.
        Default: ''
csv_output_users_audit
        Gam print commands that print objects belonging to users
        don't print rows for users that don't have any of the objects.
        The objects are: calendars, calendar ACLs, calendar events, delegates, filters,
        forwarding addresses, sendas addresses, S/MIME certificates and tokens.
        When csv_output_users_audit is true, a placeholder row will be output with the
        user's email address; these rows will useful for auditing purposes only,
        they can not be successfuly used in a gam csv command.
        Default: False
customer_id
        Google Customer ID
        Default: Blank
        Environment variable: CUSTOMER_ID
debug_level
        If debug_level > 0, turn on API debugging output.
        Default: 0
        Signal file: OldGamPath/debug.gam
device_max_results
        When retrieving lists of ChromeOS devices from API,
        how many should be retrieved in each API call
        Default: 200
        Range: 1 - 200
domain
        Google Domain
        Default: Blank
        Environment variable: GA_DOMAIN
drive_dir
        Directory for get drivefile and CSV files
        Default: ~/Downloads
        Environment variable: GAMDRIVEDIR
drive_max_results
        When retrieving lists of Drive files/folders from API,
        how many should be retrieved in each API call
        Default: 1000
        Range: 1 - 1000
drive_v3_beta
        Enable/disable use of Drive API v3 beta for Limited Folder Access testing
        Default: False
drive_v3_native_names
        Enable/disable use of Drive API v3 native column names
        in all gam print/show commands related to Google Drive
        Default: True
email_batch_size
        When archiving, printing, showing, trashing, untrashing, marking as spam Gmail messages.
        how many should be processed in each batch
        Default: 100
        Range: 1 - 100
enable_dasa
        Enable/disable Delegated Admin Service Account API Access
        admin_email, customer_id and domain must be set when enable_dasa is True,
        customer_id may not be set to my_customer
        Signal file: OldGamPath/enabledasa.txt
event_max_results
        When retrieving lists of Calendar events from API,
        how many should be retrieved in each API call
        Default: 250
        Range: 1 - 2500
extra_args
        Path to extra_args.txt
        Default: Blank
        Data file: extra_args.txt
gmail_cse_incert_dir
        Directory for the S/MIME certificate files used by Gmail Client Side Encryption.
        Default: Blank
gmail_cse_inkey_dir
        Directory for the Key Access Control List (KACL) wrapped private key data files used by Gmail Client Side Encryption.
        Default: Blank
inter_batch_wait
        When processing items in batches, how many seconds should GAM wait between batches
        Default: 0
        Range: 0 - 60
license_max_results
        When retrieving licenses from License API,
        how many should be retrieved in each API call
        Default: 100
        Range: 10 - 1000
license_skus
        A comma separated list of license SKUs; when getting licenses, only these SKUs will be processed.
        Each item in the list can be a <SKUID> which will be validated or <ProductID>/<SKUID> which will not
        Default: Blank
meet_v2_beta
        Enable/disable use of Meet API v2 beta for additional Chat Space parameters.
        Default: False
member_max_results
        When retrieving lists of Google Group members from API,
        how many should be retrieved in each API call
        Default: 200
        Range: 1 - 200
member_max_results_ci_basic
        When retrieving lists of Cloud Identity Group members from API
        with the minimal option,
        how many should be retrieved in each API call
        Default: 1000
        Range: 1 - 1000
member_max_results_ci_full
        When retrieving lists of Cloud Identity Group members from API
        with either the basic or full options,
	how many should be retrieved in each API call
        Default: 500
        Range: 1 - 500
message_batch_size
        When deleting or modifying Gmail messages,
        how many should be processed in each batch
        Default: 50
        Range: 1 - 1000
message_max_results
        When retrieving lists of Gmail messages from API,
        how many should be retrieved in each API call
        Default: 1000
        Range: 1 - 10000
mobile_max_results
        When retrieving lists of Mobile devices from API,
        how many should be retrieved in each API call
        Default: 100
        Range: 1 - 100
multiprocess_pool_limit
       Number of parallel multiprocess pool.apply_async calls
       Default: 0
       -1 - Pass all commands to the multiprocessing pool immediately
        0 - Pass commands to the multiprocessing pool in batches of size num_threads
       >0 - Pass commands to the multiprocessing pool in batches of the indicated size
never_time
        The value to be substituted whenever a Google datetime variable
        has the value "1970-01-01T00:00:00.000Z"
        Default: Never
no_browser
        If no_browser is True, GAM won't open a browser if todrive is set
        when creating CSV files and GAM prints a link and waits for
        the verification code when oauth2.txt is being created
        Signal file: OldGamPath/nobrowser.txt
no_cache
        Disable GAM API caching
        Signal file: OldGamPath/nocache.txt
no_short_urls
        When False, the long scopes URLs in `gam oauth create` and
        `gam <UserTypeEntity> check|update serviceaccount`
        will be shortened at the site `https://gam-shortn.appspot.com`;
        the shortened URL redirects to the long URL.
        When True, the long scopes URLs in `gam oauth create` and
        `gam <UserTypeEntity> check|update serviceaccount` will be used as is.
no_verify_ssl
        Disable SSL certificate validation
num_tbatch_threads
        Number of threads for gam tbatch
        Default: 2
        Range: 1 - 1000
num_threads
        Number of processes for gam batch/csv
        Default: 5
        Range: 1 - 1000
        Environment variable: GAM_THREADS
oauth2_txt
        Path to oauth2.txt
        Default: GamConfigDir/oauth2.txt
        Environment variable: OAUTHFILE
oauth2service_json
        Path to oauth2service.json
        Default: GamConfigDir/oauth2service.json
        Environment variable: OAUTHSERVICEFILE
output_dateformat
        Output format of dates
        See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        Default: '' which selects the format YYYY-MM-DD
        Example: %m/%d/%Y  will display as 08/07/2023
output_timeformat
        Output format of times
        See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        Default: '' which selects the format YYYY-MM-DDTHH:MM:SS[Z|(+|-)HH:MM)
        Example: %H:%M: %m/%d/%Y will display as 09:00 08/07/2023
people_max_results
        When retrieving lists of People from API,
        how many should be retrieved in each API call
        Default: 100
        Range: 1 - 1000
print_agu_domains
        A comma separated list of domain names that are used in these commands:
          gam print aliases
          gam print groups
          gam print|show group-members
          gam print users
        This allows predefining the list of domains so they don't have to be specified in each command.
        Default: Blank
print_cros_ous
        A comma separated list of org unit that are used in these commands:
          gam print cros
          gam print crosactivity
        This allows predefining the list of org units so they don't have to be specified in each command.
        Default: Blank
print_cros_ous_and_children
        A comma separated list of org unit names that are used in these commands:
          gam print cros
          gam print crosactivity
        This allows predefining the list of org units so they don't have to be specified in each command.
        Default: Blank
process_wait_limit
        When processing batch/CSV files, how long (in seconds) GAM should wait for all batch|csv processes to complete
        after all have been started. If the limit is reached, GAM terminates any remaining processes.
        Default: 0: no limit
        Range: 0 - Unlimited
quick_cros_move
        Default value for "quickcrosmove [<Boolean>]" in commands that update Chromebook OUs.
        Default: False
quick_info_user
        Enable/disable display of information requiring additional API calls with "gam info user"
        Default: False
reseller_id
        Google Cloud Reseller  ID
        Default: Blank
retry_api_service_not_available
        Enable/disable retrying "Service not available" errors on API calls
        These errors typically occur when making a service account API call with
          1) an invalid user email address
          2) a valid user email address for a user with no access to the app; e.g., Gmail/Drive
        Retrying these errors is pointless
        Occasionallly, Google returns this error when its backend servers are overloaded;
        these errors can be retried
        Default: False
section
        Default section of gam.cfg.
        Default: DEFAULT
show_api_calls_retry_data
        Enable/disable display of Google API calls retry data at end of processing
        Default: False
show_commands
        Enable/disable display of commands to stderr when executing `gam batch|tbatch|csv|loop`.
        Default: False
show_convert_cr_nl
        Convert carriage returns (CR) to '\r' and newlines (NL) to '\n' embedded
        in data fields when showing data
        The commands gam show groups|messages|orgs|resources|sites|threads have
        an argument, convertcrnl, that can set this value to true to
        override show_convert_cr_nl = False
        Default: False
show_counts_min
        Add (n/m) to end of messages if number of items to be processed exceeds this number
        Default: 1
        Range: 0 - 100
show_gettings
        Enable/disable "Getting ... " messages
        Default: True
show_gettings_got_nl
        Enable/disable NL at end of "Got ... " messages
        Default: False
show_multiprocess_info
        Enable/disable showing multiprocess info in redirected stdout/stderr with gam csv
        Default: False
smtp_fqdn
        Fully qualified domain name used in SMTP EHLO command
        Default: ''
smtp_host
        SMTP host name
        Default: ''
smtp_password
        SMTP authentication password
        Default: ''
smtp_username
        SMTP authentication username
        Default: ''
timezone
        Specify time conversion from Google's standard of UTC. If you are running GAM
        on a computer at your location, specify "local" to have time values converted
        to your local timezone. If you are running GAM on a remote computer or on a
        cloud shell, "local" will mean the time at the remote/cloud shell computer,
        not your location, Use "+|-hh:mm" to specify the timezone at your location.
        Default: utc
        Range: utc|Z|local|(+|-hh:mm)
tls_max_version
        Allowed values: '', tlsv1_2, tlsv1.2, tlsv1_3, tlsv1.3
        The maximum TLS version to use in https connections
        Default: ''
tls_min_version
        Allowed values: '', tlsv1_2, tlsv1.2, tlsv1_3, tlsv1.3
        The minimum TLS version to use in https connections
        Default: ''
todrive_clearfilter
        Enable/disable clearing the spreadsheet basic filter when uploading data to an existing sheet in an existing file.
        Default: False
todrive_clientaccess
        Enable/disable use of client access rather than service account access when uploading files with todrive
        Default: False
todrive_conversion
        Enable/disable conversion of CSV files to Google Sheets when todrive is specified
        Default: True
todrive_localcopy
        Enable/disable saving a local copy of CSV files when todrive is specified
        Default: False
todrive_locale
        The Spreadsheet settings Locale value.
        Default: ''
todrive_nobrowser
        Enable/disable opening a browser when todrive is specified
        Default: False
todrive_noemail
        Enable/disable sending an email when todrive is specified
        Default: True
todrive_no_escape_char
        When writing a CSV file to Google Drive, should `\` be ignored as an escape character.
        Default: True
todrive_parent
        Parent folder for CSV files when todrive is specified;
        can be id:<DriveFolderID> or <DriveFolderName>
        Default: root
todrive_sheet_timestamp
        Enable/disable adding a timestamp to the sheet (tab) title of CSV files when todrive is specified
        Default: False
todrive_sheet_timeformat
        Format of the timestamp added to the sheet (tab) title of CSV files
        See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        Default: '' which selects an ISO format timestamp
        Example: %Y-%m-%dT%H:%M:%S will display as 2020-07-06T17:48:54
todrive_timestamp
        Enable/disable adding a timestamp to the title of CSV files when todrive is specified
        Default: False
todrive_timeformat
        Format of the timestamp added to the title of CSV files
        See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        Default: '' which selects an ISO format timestamp
        Example: %Y-%m-%dT%H:%M:%S will display as 2020-07-06T17:48:54
todrive_timezone
        The Spreadsheet settings Timezone value.
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        Default: ''
todrive_upload_nodata
        Enable/disable uploading CSV files with no data rows
        Default: True
todrive_user
        Email address of user to receive CSV files when todrive is specified
        Default: '' which becomes admin user in admin_email or address from oauth2.txt
truncate_client_id
        Prior to version 6.74.00, GAM stripped '.apps.googleusercontent.com' from the client_id in oauth2.txt
        and passed the truncated value in API calls; this is no longer performed unless truncate_client_id is true
        Default: False
update_cros_ou_with_id
        Update the OU of a Chromebook with the OU ID rather than the OU path.
        Set to true if you are getting the following error:
        `400: invalidInput - Invalid Input: Inconsistent Orgunit id and path in request`
        Default: False
use_chat_admin_access
        When False, GAM uses user access when making Chat API calls. For calls that support admin access,
        this can be overridden with the asadmin command line option.
        When True, GAM uses admin access for Chat API calls that support admin access;
        other calls will use user access.
        Default: False
use_course_owner_access
        How is classroom member information obtained and how are classroom members deleted.
        Client access does not provide complete information about non-domain students/teachers.
        When False, GAM uses client access to get classroom member information and to delete members
        When True, GAM uses service account access as the classroom owner.
        An extra API call is required per course to authenticate the owner
        Default: False
use_projectid_as_name
        When False, new projects have a default project name of "GAM Project"
        and a default app name of "GAM".
        When True, new projects have a default project name of "<ProjectID>"
        and a default app name of "<ProjectID>".
        Default: False
user_max_results
        When retrieving lists of Users from API,
        how many should be retrieved in each API call
        Default: 500
        Range: 1 - 500
user_service_account_access_only
        Used by consultants that do not have client access to client domains,
        but only service account access to manage user content: files, messages, calendars.
        Default: False
```
This is sample output:
```
$gam select default verify.
Config File: /Users/admin/.gam/gam.cfg, Initialized
Section: DEFAULT
  activity_max_results = 100
  admin_email = ''
  api_calls_rate_check = false
  api_calls_rate_limit = 100
  api_calls_tries_limit = 10
  auto_batch_min = 0
  bail_on_internal_error_tries = 2
  batch_size = 50
  cacerts_pem = ''
  cache_dir = /Users/admin/.gam/gamcache
  cache_discovery_only = true
  channel_customer_id = ''
  charset = utf-8
  classroom_max_results = 0
  client_secrets_json = client_secrets.json ; /Users/admin/.gam/client_secrets.json
  clock_skew_in_seconds = 10
  cmdlog = ''
  cmdlog_max_backups = 5
  cmdlog_max_kilo_bytes = 1000
  config_dir = /Users/admin/.gam
  contact_max_results = 100
  csv_input_column_delimiter = ,
  csv_input_no_escape_char = true
  csv_input_quote_char = '"'
  csv_input_row_drop_filter = ''
  csv_input_row_drop_filter = ''
  csv_input_row_drop_filter_mode = anymatch
  csv_input_row_filter = ''
  csv_input_row_filter_mode = allmatch
  csv_input_row_limit = 0
  csv_output_column_delimiter = ,
  csv_output_convert_cr_nl = false
  csv_output_field_delimiter = ' '
  csv_output_header_drop_filter = ''
  csv_output_header_filter = ''
  csv_output_header_force = ''
  csv_output_line_terminator = lf
  csv_output_no_escape_char = false
  csv_output_quote_char = '"'
  csv_output_row_drop_filter = ''
  csv_output_row_drop_filter_mode = anymatch
  csv_output_row_filter = ''
  csv_output_row_filter_mode = allmatch
  csv_output_row_limit = 0
  csv_output_subfield_delimiter = '.'
  csv_output_timestamp_column = ''
  csv_output_users_audit = false
  customer_id = my_customer
  debug_level = 0
  device_max_results = 200
  domain = ''
  drive_dir = /Users/admin/Downloads
  drive_max_results = 1000
  drive_v3_native_names = true
  email_batch_size = 50
  enable_dasa = false
  event_max_results = 250
  extra_args = ''
  inter_batch_wait = 0
  license_max_results = 100
  license_skus = ''
  member_max_results = 200
  message_batch_size = 50
  message_max_results = 500
  mobile_max_results = 100
  multiprocess_pool_limit = 0
  never_time = Never
  no_browser = false
  no_cache = false
  no_update_check = true
  no_verify_ssl = false
  num_tbatch_threads = 2
  num_threads = 5
  oauth2_txt = oauth2.txt ; /Users/admin/.gam/oauth2.txt
  oauth2service_json = oauth2service.json ; /Users/admin/.gam/oauth2service.json
  output_dateformat = ''
  output_timeformat = ''
  people_max_results = 100
  print_agu_domains = ''
  print_cros_ous = ''
  print_cros_ous_and_children = ''
  process_wait_limit = 0
  quick_cros_move = false
  quick_info_user = false
  reseller_id = ''
  retry_api_service_not_available = false
  section = ''
  show_api_calls_retry_data = false
  show_commands = false
  show_convert_cr_nl = false
  show_counts_min = 1
  show_gettings = true
  show_gettings_got_nl = false
  show_multiprocess_info = false
  smtp_fqdn = ''
  smtp_host = ''
  smtp_password = ''
  smtp_username = ''
  timezone = utc
  tls_max_version = ''
  tls_min_version = 'TLSv1_2'
  todrive_clearfilter = false
  todrive_clientaccess = false
  todrive_conversion = true
  todrive_localcopy = false
  todrive_locale = ''
  todrive_nobrowser = false
  todrive_noemail = true
  todrive_no_escape_char = true
  todrive_parent = root
  todrive_sheet_timeformat = ''
  todrive_sheet_timestamp = false
  todrive_timeformat = ''
  todrive_timestamp = false
  todrive_timezone = ''
  todrive_upload_nodata = true
  todrive_user = ''
  truncate_client_id = false
  update_cros_ou_with_id = false
  use_projectid_as_name = false
  user_max_results = 500
  user_service_account_access_only = false
```

## Multiple Computers
You can install GAM on multiple computers, all using the same project. After installing GAM on your
initial computer, follow these quidelines.

Install GAM on the other computers; they can be on different OS's than your computer; if asked by the installer, indicate:
* that you do not want to set up a project
* that you are performing an update

Make the GAM configuration directory:
* Make the GAM configuration directory; this can be different than on your computer
* Set the GAMCFGDIR environment variable to point to the GAM configuration directory
* Copy the contents of your GAM configuration directory to the other computer

Edit `gam.cfg` on the other computer
* If the GAM configuration directory on the other computer is different than that on yours, update these values in the [DEFAULT] section:
    * cache_dir
    * config_dir
    * drive_dir

## Multiple Customers and Domains
There are four arguments to GAM that should simplify how you use GAM with multiple clients/domains.
Each client/domain will have a section in gam.cfg that sets the values specific to it.
The select argument specifies the section of gam.cfg to use for processing the rest of the GAM command;
it's how you quickly switch from from one client to another.

The arguments are optional, must appear in this order and must be the first arguments before any other GAM arguments.
```
select <Section> [save] [verify]
        Use <Section> from gam.cfg for the current GAM command.
        <Section> is case-sensitive except for DEFAULT which is case-insensitive.
    save
        Set section = <Section> in the DEFAULT section of gam.cfg
        Write configuration data to gam.cfg
    verify
        Print the variable values for the current section
        Values are determined in this order: Current section, DEFAULT section, Program default
```
Display all of the sections in gam.cfg and mark the currently selected section with a *.
```
showsections
```
The config argument is used to set selected variables in gam.cfg via the command line.
```
config [<VariableName> [=] <Value>]* [save] [verify]
    <VariableName> [=] <Value>
        Set <VariableName> = <Value> in the current section
        All <VariableNames> except section are allowed.
        The = is optional but must be surrounded by spaces if included.
    save
        Write configuration data to gam.cfg
    verify
        Print the variable values for the current section
        Values are determined in this order: Current section, DEFAULT section, Program default

redirect csv <FileName> [multiprocess] [append] [noheader] [charset <Charset>] [columndelimiter <Character>]
        If the pattern {{Section}} appears in <FileName>, it will be replaced with the name of the current section.
        If <FileName> is relative, it is appended to drive_dir in the current section if defined or drive_dir in DEFAULT
        If the GAM command writes a CSV file, it will be written to <FileName> rather than stdout
redirect stdout <FileName> [append]
        If the pattern {{Section}} appears in <FileName>, it will be replaced with the name of the current section.
        If <FileName> is relative, it is appended to drive_dir in the current section if defined or drive_dir in DEFAULT
        GAM output to stdout will be written to <FileName>
redirect stderr <FileName> [append]
        If the pattern {{Section}} appears in <FileName>, it will be replaced with the name of the current section.
        If <FileName> is relative, it is appended to drive_dir in the current section if defined or drive_dir in DEFAULT
        GAM output to stderr will be written to <FileName>
```
Here is a sample multiple domain/client example.

Edit gam.cfg to set up additional clients; it should look like this when complete.
```
[DEFAULT]
activity_max_results = 100
admin_email = ''
api_calls_rate_check = false
api_calls_rate_limit = 1000
api_calls_tries_limit = 10
auto_batch_min = 0
bail_on_internal_error_tries = 2
batch_size = 50
cacerts_pem = ''
cache_dir = /Users/admin/.gam/gamcache
cache_discovery_only = true
channel_customer_id = ''
charset = utf-8
cmdlog = ''
cmdlog_max_backups = 5
cmdlog_max_kilo_bytes = 1000
classroom_max_results = 0
client_secrets_json = client_secrets.json
clock_skew_in_seconds = 10
config_dir = /Users/admin/.gam
contact_max_results = 100
csv_input_column_delimiter = ,
csv_input_no_escape_char = true
csv_input_quote_char = '"'
csv_input_row_drop_filter = ''
csv_input_row_filter = ''
csv_output_column_delimiter = ,
csv_output_convert_cr_nl = false
csv_output_field_delimiter = ' '
csv_output_header_drop_filter = ''
csv_output_header_filter = ''
csv_output_header_force = ''
csv_output_line_terminator = lf
csv_output_no_escape_char = false
csv_output_quote_char = '"'
csv_output_row_drop_filter = 
csv_output_row_filter = ''
csv_output_subfield_delimiter = '.'
csv_output_timestamp_column = ''
csv_output_users_audit = false
customer_id = my_customer
debug_level = 0
device_max_results = 200
domain = 
drive_dir = /Users/admin/Downloads
drive_max_results = 1000
drive_v3_native_names = true
email_batch_size = 100
enable_dasa = false
event_max_results = 250
extra_args =
inter_batch_wait = 0
license_max_results = 100
license_sku = ''
member_max_results = 200
message_batch_size = 50
message_max_results = 1000
mobile_max_results = 100
multiprocess_pool_limit = 0
never_time = Never
no_browser = false
no_cache = false
no_update_check = true
no_verify_ssl = false
num_tbatch_threads = 2
num_threads = 5
oauth2_txt = oauth2.txt
oauth2service_json = oauth2service.json
output_dateformat = ''
output_timeformat = ''
people_max_results = 100
print_agu_domains = ''
print_cros_ous = ''
print_cros_ous_and_children = ''
process_wait_limit = 0
quick_cros_move = False
quick_info_user = False
reseller_id = ''
section =
show_api_calls_retry_data = false
show_commands = false
show_convert_cr_nl = false
show_counts_min = 1
show_gettings = true
show_gettings_got_nl = false
show_multiprocess_info = false
smtp_fqdn = ''
smtp_host = ''
smtp_password = ''
smtp_username = ''
timezone = utc
tls_max_version = ''
tls_min_version = 'TLSv1_2'
todrive_clearfilter = false
todrive_clientaccess = false
todrive_conversion = true
todrive_localcopy = false
todrive_locale = ''
todrive_nobrowser = false
todrive_noemail = true
todrive_no_escape_char = true
todrive_parent = root
todrive_sheet_timeformat = ''
todrive_sheet_timestamp = false
todrive_timestamp = false
todrive_timezone = ''
todrive_upload_nodata = true
todrive_user = ''
truncate_client_id = false
update_cros_ou_with_id = false
use_projectid_as_name = false

user_max_results = 500
user_service_account_access_only = false

[foo]
domain = foo.com
customer_id = my_customer
config_dir = foo

[goo]
domain = goo.com
customer_id = my_customer
config_dir = goo
```
### Existing clients that have been accessed with Legacy GAM.
You have two clients: foo and goo.
Make sub-directories foo and goo in the same folder/directory as gam.cfg.
For each client, copy the client_secrets.json and oauth2service.json files from their Legacy GAM location
to the appropriate sub-directory. If the Legacy Gam files do not have these names,
rename them after copying them to the sub-directory.

Perform the following commands for each client (replace xxx with foo and goo).
```
gam select xxx save
gam update project
gam oauth create
gam info domain
gam config customer_id <CustomerID> save
```

### New clients
You have a new client: foo.

Make a sub-directory foo the same folder/directory as gam.cfg.

Edit gam.cfg to include:
```
[foo]
domain = foo.com
customer_id = my_customer
config_dir = foo
```
Perform the following commands for client foo.
```
gam select foo save
gam create project
gam oauth create
gam info domain
gam config customer_id <CustomerID> save
gam user user@foo.com check serviceaccount
```

To get information about a client, select a section.
```
$gam select foo info domain
Customer ID: C111111111
Primary Domain: foo.com
...
$gam select goo info domain
Customer ID: C222222222
Primary Domain: goo.org
...
```
Suppose you want to work with foo for a while, then switch to goo but don't want to keep typing gam select.
```
$gam select foo save
```
GAM sets section = foo in the DEFAULT section, updates gam.cfg, selects foo for this and subsequent gam commands so you don't have to use select <Section> argument.
```
$gam info user admin
User: admin@foo.com
...
```
When it's time to switch to goo, select and save the section.
```
$gam select goo save
```
GAM sets section = goo in the DEFAULT section, updates gam.cfg, selects goo for this and subsequent gam commands so you don't have to use select <Section> argument.
```
$gam info user admin
User: admin@goo.com
...
```
If you have to switch back to foo for a single command, select foo, but don't save it, further commands without a select will be goo.
```
$gam select foo info user admin
User: admin@foo.com
...
$gam info user admin
User: admin@goo.com
...
```
To configure a keyword with a common value for all clients, select the default section.
```
$gam select default config keyword value save
```
Reselect a client after configuring the common value and then configure a keyword with a unique value for the client.
```
gam select foo config keyword value save
```
The gam csv command and the select argument can be combined to perform powerful operations in a single command line.
Suppose you have the following CSV file, InfoAdmins.csv:
```
Section,AdminUser
foo,fooadmin
goo,gooadmin
```
For each of the domains, you want to get user information about the domain administrator.
```
$gam csv InfoAdmins.csv gam select "~Section" info user "~AdminUser" nolicenses
```
For each of the domains, you also want to list the Google Drive files for the domain administrator.
```
$gam csv InfoAdmins.csv gam select "~Section" user "~AdminUser" print filelist id
```
Suppose you have two CSV files, NewFooUsers.csv and NewGooUsers.csv, with the columns: Email,FirstName,LastName,Password.
You will use these files to create new users in the foo.com and goo.com domains.

To process the files sequentially, there are two forms:
```
$gam select foo save csv NewFooUsers.csv gam create user "~Email" firstname "~FirstName" lastname "~LastName" password "~Password"
$gam select goo save csv NewGooUsers.csv gam create user "~Email" firstname "~FirstName" lastname "~LastName" password "~Password"
```
You could also do:
```
$gam csv NewFooUsers.csv gam select foo create user "~Email" firstname "~FirstName" lastname "~LastName" password "~Password"
$gam csv NewGooUsers.csv gam select goo create user "~Email" firstname "~FirstName" lastname "~LastName" password "~Password"
```
In the first form, the select/save before csv sets the default section which then applies to each gam instance.

In the second form, the select is performed for each gam instance.

To process the files in parallel in separate shells, you have to use the second form.

In shell number 1, do:
```
$gam csv NewFooUsers.csv gam select foo create user "~Email" firstname "~FirstName" lastname "~LastName" password "~Password"
```
In shell number 2, do:
```
$gam csv NewGooUsers.csv gam select goo create user "~Email" firstname "~FirstName" lastname "~LastName" password "~Password"
```
The gam loop command and the select and redirect arguments can be combined to perform powerful operations in a single command line.
```
gam loop (-|<FileName>) [charset <Charset>] (matchfield|skipfield <FieldName> <REMatchPattern>)* gam <GAM argument list>
```
Suppose you have the following CSV file, InfoDomains.csv:
```
Section,Domain,AdminUser
foo,foo.com,googleadmin
goo,goo.com,admin
```
For each of the domains, you want to get user information about the domain administrator. GAM writes this information
to stdout, so you'll redirect stdout. In the first case, you want all of the output in a single file so stdout is
redirected to a file before the csv command.
```
$gam redirect stdout InfoDomainAdmins.lst multiprocess csv InfoDomains.csv gam select "~Section" info user "~AdminUser" nolicenses
```
In the second case, you want the output for each domain administrator in a separate file so stdout is redirected after
the csv command.
```
$gam csv InfoDomains.csv select "~Section" redirect stdout Info-~~Domain~~-Admin.lst info user "~AdminUser" nolicenses
```
For each of the domains, you also want to list the Google Drive files for the domain administrator. GAM writes this information
to a csv file, so you'll redirect csv output. In the first case, you want all of the output in a single file so csv output is
redirected to a file before the csv command.
```
$gam redirect csv FilesDomainAdmins.csv multiprocess csv  InfoDomains.csv gam select "~Section" user "~AdminUser" print filelist id
```
In the second case, you want the output for each domain administrator in a separate file so csv output is redirected after
the csv command.
```
$gam csv InfoDomains.csv select "~Section" redirect csv Files-~~Domain~~-Admin.csv user "~AdminUser" print filelist id
```

## Multiple Users-Projects on One Computer
You can have multiple users with distinct logins on the same computer share the `[DEFAULT]` section of `gam.cfg` but each
reference a unique `[Section]`; this might be done if you want each user to have their own GAM
project for auditing purposes.

The system environment variable GAMCFGDIR references GamCfgDir, the folder containing gam.cfg.
Make a subdirectory in GamCfgDir for each user to contain their authorization files.
In gam.cfg, make a section for each user and set config_dir to the name of the subdirectory.
The subdirectory name and section name do not have to be the same.
```
[foo]
config_dir = foo

[goo]
config_dir = goo
```

Login as each user and set the user environment variable GAMCFGSECTION to reference their section;
e.g., `GAMCFGSECTION=foo`.

Now, create their project and authorization; all files will be written to their sub-directory.
```
gam create project
gam oauth create
gam user user@domain.com update serviceaccount
```

The values, `customer_id` and `domain` for example, in the `[DEFAULT]` section will be shared by all users.
If a user does `gam config <VariableName> <Value> save`, `<VariableName> = <Value>` will be written to their section only.

When GAMCFGSECTION is set, an error will be generated if the user tries to change the section with `gam select <Section>`.
