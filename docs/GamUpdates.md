# Update GAMADV-XTD3 to latest version
Automatic update to the latest version on Linux/Mac OS/Google Cloud Shell/Raspberry Pi/ChromeOS:
- Do not create project or authorizations, default path `$HOME/bin`
  - `bash <(curl -s -S -L https://raw.githubusercontent.com/taers232c/GAMADV-XTD3/master/src/gam-install.sh) -l`
- Do not create project or authorizations, specify a path
  - `bash <(curl -s -S -L https://raw.githubusercontent.com/taers232c/GAMADV-XTD3/master/src/gam-install.sh) -l -d <Path>`

By default, a folder, `gamadv-xtd3`, is created in the default or specified path and the files are downloaded into that folder.
Add the `-s` option to the end of the above commands to suppress creating the `gamadv-xtd3` folder; the files are downloaded directly into the default or specified path.

See [Downloads](https://github.com/taers232c/GAMADV-XTD3/wiki/Downloads) for Windows or other options, including manual installation

### 6.66.13

Updated functionality of option `preservefiletimes` in `gam <UserTypeEntity> update drivefile <DriveFileEntity>`.

* Current
  * `preservefiletimes localfile <FileName>` - `modifiedTime` of `<DriveFileEntity>` is set to that of `localfile <FileName>`
  * `preservefiletimes` - No effect
* Updated
  * `preservefiletimes localfile <FileName>` - `modifiedTime` of `<DriveFileEntity>` is set to that of `localfile <FileName>`
  * `preservefiletimes` - `modifiedTime` of `<DriveFileEntity>` retains its current value

### 6.66.12

Upgraded to Python 3.12.1 where possible.

Updated all drive commands to handle the following error:
```
ERROR: 401: Active session is invalid. Error code: 4 - authError
```
This is due to the Drive SDK API being disabled in the user's OU.
* See: https://support.google.com/a/answer/6105699

### 6.66.11

Fixed/improved handling of shortcuts in `gam <UserTypeEntity> transfer drive`.

### 6.66.10

Updated `gam create datatransfer` to handle the following error:
```
ERROR: 401: Active session is invalid. Error code: 4 - authError
```

### 6.66.09

Fixed bug in `gam <UserTypeEntity> print filelist ... allfields` that caused a trap
when `gam.cfg` contained `drive_v3_native_names = False`.

### 6.66.08

Added additional columns `isBase` and `baseId` to `gam <UserTypeEntity> print fileparenttree`
to simplify  processing the output in a script.

### 6.66.07

Fixed bug in `gam <UserTypeEntity> print diskusage` that caused a trap.

### 6.66.06

Added a command the print the parent tree of file/folder.
```
gam <UserTypeEntity> print fileparenttree <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [stripcrsfromname]
```
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Display#display-file-parent-tree

### 6.66.05

Added column `space.name` to `gam <UserTypeEntity> print chatmembers`.

### 6.66.04

Updated Chat info|show|print commands to display all time fields in local time if specified in `gam.cfg`.

### 6.66.03

Fixed bug in `gam <UserTypeEntity> print filelist select <DriveFileEntity>` where `stripcrsfromname` was not being
applied to files below the selected folder.

### 6.66.02

Updated device commmands to handle the following error caused by an invalid query.
```
ERROR: 400: invalidArgument - Request contains an invalid argument.
```

Added fields `deviceid` and `hostname` to `<DeviceFieldName>`.

### 6.66.01

Added the following variables to gam.cfg that allow control over whether `\` is used as an escape character
when reading/writing CSV files.
```
csv_input_no_escape_char - default value True
csv_output_no_escape_char - default value False
todrive_no_escape_char - default value True
```
When the value is True, `\` is ignored as an escape character; when the value is False,
`\\` on input is converted to `\`, `\` on output is converted to `\\`.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Special-Characters

### 6.66.00

Added support for `Focus Time` and `Out of Office` status events in user's primary calendars.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Calendars-Events#status-events
This is a work-in-progress.

Updated `gam <UserTypeEntity> print|show messages` to allow option `show_size` to be used with option `countsonly`
to display the cumulative size of the messages selected.
```
gam user user@domain.com print messages query "newer_than:31d" countsonly showsize
Getting all Messages for user@domain.com
Got 16 Messagess for user@domain.com...
User,messages,size
user@domain.com,16,92806
```

### 6.65.17

Added the option `mappermissionsdomain <DomainName1> <DomainName2>` to `gam <UserTypeEntity> create drivefileacl <DriveFileEntity>`
that maps `<DomainName1>` to `<DomainName2>` in the `user <UserItem>)|(group <GroupItem>)|(domain <DomainName>)` options;
`<UserItem>` and `<GroupItem>` must specify email addresses for the mapping to succeed.
The option can be specified multiple times to provide different mappings. This option will be most useful
when reading a CSV file containing ACLs referencing `<DomainName1>` and you want a new ACL with the same options but in `<DomainName2>`.

### 6.65.16

Fixed bug in `gam <UserTypeEntity> print filecounts` where `Item Cap` showed an incorrect value.

Added option `addorigfieldstosubject` to `gam <UserTypeEntity> forward messages|threads` that causes GAM
to append  the original `from`, `to` and `date` fields to the message subject.
```
Fwd: Ross to TestUser (Original From: Ross Scroggs <ross.scroggs@gmail.com> To: testuser@domain.com Date: Thu, 23 Nov 2023 07:01:59 -0800)
```

### 6.65.15

Added additional options to `gam <UserTypeEntity> print|show youtubechannels`.

### 6.65.14

Fixed bug in gam <UserTypeEntity> copy|move drivefile` that caused a trap.
```
UnboundLocalError: cannot access local variable 'emailAddress' where it is not associated with a value
```

### 6.65.13

Added support for user language `en-CA`.


Added option `sizefield quotabytesused|size` to the following commands that specifies which
file size field to use when totaling file sizes; the default value is `quotabytesused`; previous versions used `size`.
```
gam <UserTypeEntity> print|show filecounts
gam <UserTypeEntity> print filelist
gam <UserTypeEntity> print|show filetree
gam <UserTypeEntity> print diskusage
```
See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Display#file-size-fields

### 6.65.12

Additional updates on MacOS when a `gam csv` command is interrupted with a contol-C.

### 6.65.11

Updated multiprocessing to handle the following error that occurs on MacOS when a `gam csv` command
is interrupted with a contol-C.
```
multiprocessing/resource_tracker.py:224: UserWarning: resource_tracker: There appear to be N leaked semaphore objects to clean up at shutdown
```

Fixed bug in `gam print|show crostelemetry` where no CrOS device data was displayed if no selection
options were chosen; now, data is displayed for all CrOS devices as documented.

### 6.65.10

Fixed bug in `gam print crostelemetry` that caused a trap: `KeyError: 'reportTime'`.

### 6.65.09

Added option `noduplicate` to `gam <UserTypeEntity> create drivefile` that causes GAM
to issue a warning and not perform the create if a non-trashed item with the same name (regardless of MIME type)
exists in the parent folder.

Updated `gam <UserTypeEntity> get drivefile <DriveFileEntity>` to handle the following error
that seems to occur when multiple tabs from a Google sheet are being downloaded in parallel.
```
Download Failed: HTTP Error: 429
```

### 6.65.08

Added option `addcsvdata <FieldName> <String>` to `gam report <ActivityApplicationName>` that adds
additional columns of data to the CSV file output.

Added option `shownoactivities` to `gam report <ActivityApplicationName>` that causes GAM to display
a row with a key value of `NoActivities` when there are no activities to report.

For example, to find Shared Drives with no activity, see: https://github.com/taers232c/GAMADV-XTD3/wiki/Reports#find-shared-drives-with-no-activity

### 6.65.07

Updated `gam delete building` to handle the following error:
```
ERROR: 412: conditionNotMet - Cannot delete building because there are Calendar resources associated with it.
```

### 6.65.06

Improved error message when trying to add external students/teachers to a course.
```
gam courses 544906261666 add student user@gmail.com
Course: 544906261666, Add 1 Student
  Course: 544906261666, Student: user@gmail.com, Add Failed: 403: permissionDenied - @CannotDirectAddUser Unable to directly add the user to the course. Please check that the user account exists and is within the course admin's domain. Add external user with: gam user user@gmail.com create classroominvitation courses 544906261666 role Student
```

### 6.65.05

Updated `gam info users <UserTypeEntity>` to make option `grouptree` effective when used
with option `formatjson`.

Added option `[formatjson [quotechar <Character>]]]`
to these commands so that event details are displayed in CSV format.
```
gam print|show grouptree <GroupEntity>
gam <UserTypeEntity> print|show grouptree
```

Added option `querytime<String> <Date>` to all commands that process messages.
For example, you can identify all messages within a particular time period, in this case, all messages unread
in the last 30 days.
```
gam user user@domain.com  print messages querytime30d -30d query "after:#querytime30d# is:unread"
```

Updated `gam <UserTypeEntity> import|insert message` to allow `replace <Tag> <UserReplacement>` as documented.

Updated non-owner permission handling in `gam <UserTypeEntity> copy|move drivefile`.

### 6.65.04

Fixed bug where license SKU `1010020031` (Google Workspace Frontline Standard) was improperly entered making it unusable;
its alias `wsflwstan` was usable.

Added support for Google Workspace Additional Storage.
* ProductID - 101043
* SKUID - 1010430001 | gwas | plusstorage

### 6.65.03

Fixed bug in commands that display calendar events where event start and end times were not properly displayed
when `gam.cfg` had `timezone utc`. The API returns the start and end times expressed in the calendar timezone
but GAM replaced the timezone specifier with a `Z`; the date and time values were as expected. This became
a problem when event data was exported and used to create or update events.

### 6.65.02

Updated `gam print|show browsers` to handle the following error:
```
ERROR: 503: serviceNotAvailable - The service is currently unavailable.
```

### 6.65.01

Added option `showmimetypesize` to `gam <UserTypeEntity> print|show filecounts` and
`gam <UserTypeEntity> print filelist countsonly` that displays the total file size for each MIME type.

### 6.65.00

Fixed bug in `gam <UserTypeEntity> create contact <JSONData>` that caused a trap when
contacts were being copied from one user to another.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-People-Contacts-Profiles#copy-user-contacts-to-another-user

Updated the following commands to allow specification of a task list by its title.
```
<TaskListTitle> ::= tltitle:<String>
<TasklistTitleList> ::= "'<TasklistTitle>'(,'<TasklistTitle>')*"
<TasklistEntity> ::=
        <TasklistIDList> | <TaskListTitleList> | <FileSelector> | <CSVFileSelector>

gam <UserTypeEntity> create task <TasklistEntity>
gam <UserTypeEntity> show tasks [tasklists <TasklistEntity>]
gam <UserTypeEntity> print tasks [tasklists <TasklistEntity>]
gam <UserTypeEntity> update tasklist <TasklistEntity>
gam <UserTypeEntity> delete tasklist <TasklistEntity>
gam <UserTypeEntity> clear tasklist <TasklistEntity>
gam <UserTypeEntity> info tasklist <TasklistEntity>
```

Note the quoting in `<TasklistTitleList>`; the entire list should be enclosed in `"` and
each `tltitle:<String>` must be enclosed in `'` if `<String>` contains a space.

### 6.64.16

Fixed bug in `gam <UserTypeEntity> create task <TasklistIDEntity>` that caused a trap
when an invalid TaskListID was specified.

### 6.64.15

Updated `lookerstudioassets|lookerstudiopermissions` commands to handle the following error:
```
ERROR: 500: internalError - Internal error encountered.
```

### 6.64.14

Cleaned up and renamed `gam info appdetails` to `gam info chromeapp`.

### 6.64.13

Added command to get customer app details.
```
gam info appdetails android|chrome|web <AppID> [formatjson]
```

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Chrome-Installed-Apps

### 6.64.12

Upgraded to Python 3.12.0 where possible.
Upgraded to OpenSSL 3.1.3 where possible.

### 6.64.11

Added support for Google Workspace Labs license.
* ProductID - 101047
* SKUID - 1010470002 | gwlabs | workspacelabs

### 6.64.10

Fixed bug introduced in	6.64.09	that caused a trap when	`gam redirect csv <FileName> multiprocess` was used.

### 6.64.09

Eliminated extraneous `permisssions.0.xxxx` headers in `gam <UserTypeEntity> print filelist ... oneitemperrow`
that appeared when some user in `<UserTypeEntity>` had no files to display.

### 6.64.08

Fixed bug in `redirect csv - todrive tdtitle "File Title" tdsheettitle "Sheet Title"` where
"Sheet Title" was not assigned to the new sheet.

### 6.64.07

Updated `gam <UserTypeEntity> move drivefile` to handle the following error:
```
ERROR: 403: targetUserRoleLimitedByLicenseRestriction - Cannot set the requested role for that user as they lack the necessary license
```

### 6.64.06

Added fields `devicelicensetype` and `osupdatestatus` to `<CrOSFieldName>`.

### 6.64.05

Added `matchfield organizerself <Boolean>` to `<EventMatchProperty>` to simplify selecting events
where the user in the following commands is/is not the organizer of the event.
```
gam <UserTypeEntity> update events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> delete events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> purge events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> move events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> info events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> show events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> print events <UserCalendarEntity> [<EventEntity>]
gam <UserTypeEntity> update calattendees <UserCalendarEntity> <EventEntity>
```

### 6.64.04

Updated `gam calendars <CalendarEntity> move events` and `gam <UserTypeEntity> move events <UserCalendarEntity>`
to handle the following error:
```
ERROR: 400: badRequest - Bad Request
```

### 6.64.03

Updated `gam <UserTypeEntity> get drivefile` to allow downloading Jamboard files; they must be downloaded with `format pdf`.

### 6.64.02

Updated `gam <UserTypeEntity> transfer drive` to handle the following error:
```
ERROR: 400: Bad Request. User message: "The action cannot be performed on an item of mime-type: application/vnd.google-apps.shortcut" - invalidSharingRequest
```

### 6.64.01

Updated `gam <UserTypeEntity> print|show youtubechannels` to handle the following error:
```
ERROR: 403: unsupportedSupervisedAccount - Access Forbidden. The authenticated user cannot access this service.
```

### 6.64.00

Added support for displaying users YouTube channels.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-YouTube

### 6.63.19

Fixed bug in `gam print vacation` where `endDate` value was not converted to `yyyy-mm-dd` format.

### 6.63.18

Updated `gam print|show ownership` to show the correct file owner when the most recent event is `change_owner`.

### 6.63.17

Added support for Duet AI license.
* ProductID - 101047
* SKUID - 1010470001 | duetai

Added `api_call_tries_limit` variable to `gam.cfg` that limits the number of tries
for Google API calls that return an error that indicates a retry should be performed.
The default value is 10 and the range of allowable values is 3-10.

### 6.63.16

Arguments `noinherit`, `blockinheritance` and `blockinheritance true` have been removed from the following
commands due to an upcoming API change that no longer allows blocking OU setting inheritance.
Arguments `inherit` and `blockinheritance false` are still valid.
```
gam create org <OrgUnitPath>
gam update org <OrgUnitItem>
gam update orgs <OrgUnitEntity>
```

### 6.63.15

Added `print_cros_ous` and `print_cros_ous_and_children` variables to `gam.cfg` that provide a default list of OUs for these commands:
```
gam print cros
gam print crosactivity
```

Updated `group` commands that manage members to handle the following error:
```
ERROR: 503: serviceNotAvailable - The service is currently unavailable.
```

Updated Data Studio to Looker Studio; added the following command synonyms:
* `lookerstudioassets` for `datastudioassets`
* 'lookerstudiopermissions` for `datastudiopermissions`

Corrected error message in `gam add datastudiopermissions`:
* Old -`ERROR: Missing argument: Expected <DataStudioAssetMembersEntity>`
* New - `ERROR: Missing argument: Expected <LookerStudioPermissionEntity>

### 6.63.14

Added option `verifyorganizer [<Boolean>]` to `gam <UserTypeEntity> copy|move drivefile`. When a copy/move
operation involves a Shared Drive, GAM verifies that the user is an organizer. Unfortunatley, this fails
when the user is not a direct organizer but is a member of a group that is an organizer. Specifying
`verifyorganizer false` suppresses the verification.

Updated the following commands to be able to specify a list of domains rather than a single domain:
```
gam print aliases
gam print groups
gam print|show group-members
gam print users
```
Added `print_agu_domains` variable to `gam.cfg` that provides a default list of domains for these commands.

When multiple domains are specified and a query/queries are specified, an API call is made for each domain/query combination.
```
$ gam print users domains school.org,students.school.org queries "'email:admin*','email:test*'"
Getting all Users that match query (domain=school.org, query="email:admin*"), may take some time on a large Google Workspace Account...
Got 3 Users: admin@school.org - admindirector@school.org
Getting all Users that match query (domain=school.org, query="email:test*"), may take some time on a large Google Workspace Account...
Got 20 Users: testusera@school.org - testuserx@school.org
Getting all Users that match query (domain=students.school.org, query="email:admin*"), may take some time on a large Google Workspace Account...
Got 1 User: admin@students.school.org - admin@students.school.org
Getting all Users that match query (domain=students.school.org, query="email:test*"), may take some time on a large Google Workspace Account...
Got 1 User: testuser1@students.school.org - testuser1@students.school.org
primaryEmail
...
```

### 6.63.13

Updated `gam <UserTypeEntity> print filelist ... showdrivename` and `gam <UserTypeEntity> show fileinfo <DriveFileEntity> ... showdrivename`
to show the actual name of Shared Drives in other domains rather than `Drive`.

### 6.63.12

Updated commands that call the Reports API (including `gam info domain`) to handle a change
in the Reports API that generated the following warning:
```
WARNING: End date greater than LastReportedDate.
```

Added option `showdeleted [<Boolean>]' to `gam <UserTypeEntity> print|show chatmessages`.

### 6.63.11

Added option `ou_and_children  <OrgUnitItem>` to `gam print|show crostelemetry` to simplify getting
telemetry data for all ChromeOS devices in an OU and its children.

### 6.63.10

Added option `addcsvdata <FieldName> <String>` to these commands. This adds additional columns of data to the CSV file output
when the `csv` option is used. If a CSV file of calendar information is being used to specify the calenders, fields, e.g., summary
can be added to the ACL output file.
```
gam <UserTypeEntity> print calendaracls <UserCalendarEntity>
gam resource <ResourceID> print calendaracls
gam resources <ResourceEntity> print calendaracls
gam calendar <CalendarEntity> printacl
gam calendars <CalendarEntity> print acls
```

Added commands to show the number of CrOS devices or Users in an entity.
```
gam <CrOSTypeEntity> show count
gam <UserTypeEntity> show count
```

Updated `gam create project` to prompt user to mark `GAM Project Creation` as a trusted app.

### 6.63.09

Updated `gam create teamdrive` to handle the following error:
```
ERROR: 403: userCannotCreateTeamDrives - The authenticated user cannot create new shared drives.
```

### 6.63.08

Updated `cigroup` commands to handle the following error:
```
ERROR: 400: invalidArgument - Request contains an invalid argument.
```

### 6.63.07

Fixed bug in `gam <UserTypeEntity> append sheetrange` that caused a trap when appending to an empty sheet.

Upgraded to Python 3.11.5 where possible.

### 6.63.06

Updated `cigroup` commands to handle the following error:
```
ERROR: 503: serviceNotAvailable - The service is currently unavailable.
```

### 6.63.05

Updated `inboundsso` commands to handle the following error:
```
ERROR: 503: serviceNotAvailable - The service is currently unavailable.
```

### 6.63.04

Added option `ignorerole` to `gam update groups|cigroups <GroupEntity> sync [<GroupRole>|ignorerole] ... <UserTypeEntity>` that causes GAM
to remove members regardless of role and add new members with role MEMBER. This is a special purpose option, use with caution
and ensure that `<UserTypeEntity>` specifies the full desired membership list of all roles.

### 6.63.03

Added option `externalusersallowed <Boolean>` to `gam <UserTypeEntity> create chatspace`
that allows creation of chat spaces that allow external users.

Updated commands that process chat members to allow external users.

### 6.63.02

Fixed bug in `gam <UserTypeEntity> collect orphans` where shortcuts were being created unnecessarily
when `useshortcuts` was false; either by default or when explicitly set.

### 6.63.01

Added `process_wait_limit` variable to `gam.cfg` that controls how long (in seconds) GAM should wait for all batch|csv processes to complete
after all have been started. If the limit is reached, GAM terminates any remaining processes. The default is 0 which specifies no limit.

Following Jay's lead, added option `alwaysevict` to `gam create|update user` that is used to specify GAM's
behavior when `verifynotinvitable` is not specified and there is a conflict with an unmanaged account.

By default, when creating a user that has a conflict with an unmanaged account, GAM will honor the setting on this page:
  * https://admin.google.com/ac/accountsettings/conflictaccountmanagement

Specifying `alwaysevict` forces GAM to select this setting: `Replace conflicting unmanaged accounts with managed ones`

With `gam update user`, `alwaysevict` only applies if `createifnotfound` is specified and the user was not found to update and must be created.

### 6.63.00

Added support for calendar working location events.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Calendars-Events#working-location-events

### 6.62.08

Added option `addcsvdata <FieldName> <String>` to these commands.  This adds additional columns of data to the CSV file output
when the `csv` option is used.
```
gam create contact
gam <UserTypeEntity> create contact
gam <UserTypeEntity> create contactgroup
```

### 6.62.07

Added option `csv [todrive <ToDriveAttribute>*]` to these commands that causes GAM to output
the contact creator and contact ID in CSV form. This will be useful when bulk contacts are created.

Added `returnidonly` to these commands that causes GAM to return just the
contact ID as output. This will be useful in scripts that create a contact and then
want to perform subsequent GAM commands on the contact.
```
gam create contact
gam <UserTypeEntity> create contact
gam <UserTypeEntity> create contactgroup
```

### 6.62.06

Added output `Item cap` to `gam <UserTypeEntity> print filecounts select select <SharedDriveEntity>` that
displays the total number of files/folders on the Shared Drive divided by 400000, the maximum number of file/folders on a Shared Drive.

### 6.62.05

Added progress messages (suppressible)  to `gam <UserTypeEntity> print diskusage`.

### 6.62.04

Added command `gam <UserTypeEntity> print diskusage` to display disk usage by folder.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Display#display-disk-usage

### 6.62.03

Handled Google Directory API bug in `gam print groups` that caused a trap.

### 6.62.02

Fixed bug introduced in 6.62.01 that caused a trap that broke `redirect csv ... multiprocess`.
My apologies.

### 6.62.01

Updated code so that when `gam.cfg` variables `csv_output_timestamp_column` and `output_timeformat` are both specified,
the timestamp is output in the alternate output time format.

### 6.62.00

Added `output_dateformat` and `output_timeformat` variables to `gam.cfg` that provide alternate
output date and time formats that may be required by programs that will be processing the data.
GAM will not accept alternate date/time formats as input.

* See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

### 6.61.21

Updated `gam <UserTypeEntity> empty drivetrash <SharedDriveEntity>` to use new Drive API v3
functionality for emptying the trash of a Shared Drive with a single API call. Previously, GAM had to purge each
individual file and folder in the trash.

### 6.61.20

Remove `audit.googleapis.com` from the list of project APIs.

### 6.61.19

Fixed bug in `gam <UserTypeEntity> print|show chatmembers <ChatSpace>` that caused a trap.

### 6.61.18

Added the following options to `gam [<UserTypeEntity>] create shareddrive` to allow better control
of the create/update process when attributes other than `themeid` are specified.
```
errorretries <Integer> - Number of create/update error retries; default value 5, range 0-10
updateinitialdelay <Integer> - Initial delay after create before update: default value 10, range 0-60
updateretrydelay <Integer> - Retry delay when update fails; default value 10, range 0-60
```
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Shared-Drives#create-a-shared-drive

### 6.61.17

Updated `gam print|show vaultexports|vaultholds|vaultqueries` to not set a non-zero return code
when a vault matter changes state from `OPEN` to `CLOSED|DELETED` while the command is being processed.

Updated `gam create shareddrive <Name> ou|org|orgunit <OrgUnitItem>` to handle the following error:
```
ERROR: 403: permissionDenied - Request had insufficient authentication scopes.
```
It's not clear what causes the error.

### 6.61.16

Added the following license SKUs.
```
1010060005 - Google Workspace Essentials Plus
1010020031 - Google Workspace Frontline Standard
1010340005 - Google Workspace Business Starter - Archived User
1010340006 - Google Workspace Business Standard - Archived User
```

### 6.61.15

Added option `contentrestrictions ownerrestricted [<Boolean>]` to `<DriveFileAttribute>`.

### 6.61.14

Added `aggregatebyuser [Boolean]` option to `gam report user` to allow data aggregation for users across multiple dates.
Options `aggregatebyuser` and `aggregatebydate` are mutually exclusive.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Reports#user-reports

### 6.61.13

Added commands to display Analytic UA properties.
```
gam <UserTypeEntity> print analyticuaproperties [todrive <ToDriveAttribute>*]
        accountid [accounts/]<String>
        [maxresults <Integer>]
        [formatjson [quotechar <Character>]]
gam <UserTypeEntity> show analyticuaproperties
        accountid [accounts/]<String>
        [maxresults <Integer>]
        [formatjson]
```

### 6.61.12

Updated `gam print|show vaultexports|vaultholds|vaultqueries` to handle the case
where a vault matter changes state from `OPEN` to `CLOSED|DELETED` while the command is being processed.

### 6.61.11

Added option `returnidonly` to `gam create vaultexport|vaulthold|vaultmatter`
that causes GAM to return just the ID of the item created as output.

### 6.61.10

Fixed bug in `gam oauth create admin <EmailAddress>` which caused no scopes to be selected.

### 6.61.09

Updated `gam oauth create` to handle case where Google takes a very long time to respond
after you have allowed access to the scopes.

### 6.61.08

Updated `gam <UserTypeEntity> print messages showlabels` to include a column `LabelsCount` to
display the number of labels a message has. Use option `useronly` to limit the labels to user labels.

Updated `gam <UserTypeEntity> print messages` to display these columns, if applicable, as the
last columns in the CSV file.
```
SizeEstimate, LabelsCount, Labels, Snippet, Body
```

### 6.61.07

Improved action messages in `gam update org|ou <OrgUnitItem> sync <UserTypeEntity> [removetoou <OrgUnitItem>]`.

### 6.61.06

Added option `csv` to `gam <UserTypeEntity> check group|groups` that displays
the results in CSV format.
```
$ gam user testuser check groups csv testgroup1,testgroup2,alladmin
User: testuser@domain.com, Check in 3 Groups
user,group,role
testuser@domain.com,alladmin@domain.com,Not a MEMBER|OWNER|MANAGER
testuser@domain.com,testgroup1@domain.com,MEMBER
testuser@domain.com,testgroup2@domain.com,MANAGER
```

### 6.61.05

Fixed bug in `gam print contacts` that caused a trap when `show_gettings = False` in gam.cfg.

### 6.61.04

Updated `gam create shareddrive <Name>` to wait longer between creating the Drive
and updating any attributes that could not be specified as part of the creation; i.e.,
`<SharedDriveRestrictionsFieldName>`, `hidden`, `customtheme`, `color` and `orgunit`.
The initial wait is 30 seconds. Previously, GAM was not waiting long enough;
the Drive would be created but the update would fail; the attributes were not set.

### 6.61.03

Updated processing of `<UserMultiAttribute> externalid` to allow an empty `custom` type.
```
externalid account|customer|login_id|network|organization|(custom <string>)|<String> <String>
```
These are equivalent ways of expressing an empty custom type:
```
externalid "" "Value"
externalid custom "" "Value"
```

### 6.61.02

Fixed bug in `gam update groups <GroupEntity> sync` introduced in 6.60.31 that caused this error:
```
ERROR: 409: generic409 - Member already exists.
```

### 6.61.01

Added option `noactionifalias` to `gam delete groups <GroupEntity>` that prevents GAM from deleting a
group if `<GroupEntity>` specifies an alias rather than a primary email address.

### 6.61.00

Following Jay's lead, added `no_short_urls` variable to `gam.cfg`. When false, the long scopes URLs in `gam oauth create` and
`gam <UserTypeEntity> check|update serviceaccount` will be shortened at the site `https://gam-shortn.appspot.com`; the shortened
URL redirects to the long URL. For existing configurations, `no_short_urls` defaults to true; the long URLs are used as is.
For new configurations the `no_short_urls` defaults to false unless there is a file named `noshorturls.txt` in the folder
specified by the environment variable `OLDGAMPATH`.

### 6.60.31

Added option `addcsvdata <FieldName> <String>` to `gam print forms|formresponses`. This adds additional columns of data to the CSV file output.
This can be used to combine form information from several GAM commands.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Forms#combine-form-information

Following Jay's lead, projects can now be created with consumer accounts.

### 6.60.30

Added option `countsonly` to `gam <UserTypeEntity> print|show formresponses` that causes GAM to display
the number of responses to a form rather than displaying the response details.

### 6.60.29

Updated `gam <UserTypeEntity> delete|print emptydrivefolders` to show the path to the deleted folder
rather than just its name. Added an option to allow a starting point other that the root of My Drive or a Shared Drive.
Improved the commands performance.

### 6.60.28

Fixed bug in `gam <UserTypeEntity> print filelist countsonly showsource stripcrsfromname` where
carriage returns, linefeeds and nulls were not stripped from file names.

### 6.60.27

Updated `gam <UserTypeEntity> print filelist countsonly` to process `addcsvdata <FieldName> <String>`.
Additional fields are added before `Size` if present, otherwise `Total`.

### 6.60.26

Added option `orgunit|org|ou <OrgUnitPath>` to `gam print|show teamdrives` that limits the display
to Shared Drives in the specified Org Unit.

### 6.60.25

Added option `orgunit|org|ou <OrgUnitPath>` to `gam print|show teamdriveacls` that limits the display
of permissions to Shared Drives in the specified Org Unit.

### 6.60.24

Updated `gam <UserTypeEntity> info|show|print chatmessages` to show the sender email address
when the sender is a human.

### 6.60.23

Fixed bug in `config csv_input_row_filter|csv_output_row_filter` where "field:date<today" was being processed
as "field:date<=today" and "field:date>=today" was being processeed as "field:date>today".

### 6.60.22

Added option `pathdelimiter <Character>` to `gam <UserTypeEntity> create drivefolderpath` to simplify
specifying folder paths where a folder name contains a `/`. In the example, some folder has a '/' in it's name
so specifying `pathdelimiter "|"` allows `fullpath` to be properly processed. `pathdelimiter` defaults to '/'.
```
gam user user@domain.com create drivefolderpath pathdelimiter "|" fullpath "My Drive|Top Folder|Middle/Folder|Bottom Folder"
```

### 6.60.21

Fixed bug in `gam <UserTypeEntity> copy|create|update drivefile` where processing the following `<DriveFileAttribute>` attributes
was not correct. Previously, if multiple properties of the same visibility were specified, only the first was processed;
now, all values are processed.
```
privateproperty <PropertyKey> <PropertyValue>
publicproperty <PropertyKey> <PropertyValue>
property <PropertyKey> <PropertyValue> [private|public]
```

### 6.60.20

Updated `gam <UserTypeEntity> get document|drivefile <DriveFileEntity>` to handle shortcuts by downloading
the file that the shortcut references as the shortcut itself is not downloadable. If you do not want
this behavior and want GAM to report an error, use the option `donotfollowshortcuts`.

### 6.60.19

Updated `gam <UserTypeEntity> archive messages` to handle the following error:
```
ERROR: 400: failedPrecondition - Precondition check failed.
```

### 6.60.18

Updated `gam <UserTypeEntity> print|show tokens` to handle the following error that occurs
when a group email address is specified rather than a user email address.
```
ERROR: 400: badRequest - Type not supported: userKey
```

### 6.60.17

Fixed bug in `gam <UserTypeEntity> move drivefile` that caused an error when moving the contents
of a source Shared Drive to a target Shared Drive when `mergewithparents` was not specified or was
explicitly set False.

### 6.60.16

Updated commands that create files to handle the following error:
```
403: storageQuotaExceeded - The user's Drive storage quota has been exceeded.
```

### 6.60.15

Updated `gam print chromesnvalidity` to do case insenstitive serial number comparisons.

### 6.60.14

Added command to help verify Chrome device serial number validity.
```
gam print chromesnvalidity [todrive <ToDriveAttribute>*]
        cros_sn <SerialNumberEntity> [listlimit <Number>]
        [delimiter <Character>]
```
See: https://github.com/taers232c/GAMADV-XTD3/wiki/ChromeOS-Devices#check-chromeos-device-serial-number-validity

### 6.60.13

Updated `gam <UserTypeEntity> print|show chatspaces` to handle the following error:
```
Error: 403: permissionDenied - Permission denied to perform the requested action on the specified resource
```

### 6.60.12

Added option `tdretaintitle [<Boolean>]` that, when `True` (the default) and used with `tdfileid <DriveFileID>`,
causes GAM to not modify the CSV filename.

### 6.60.11

Fixed bug in `gam print addresses` where non-editable user/group aliases were not displayed.

### 6.60.10

Added a command to get information about a direct message chat space between two users.
```
gam <UserTypeEntity> info chatspacedm <UserItem>
        [formatjson]
```

### 6.60.09

Added option `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]`
to these commands so that event details are displayed in CSV format.
```
gam calendar|calendars <CalendarEntity> create|import|update event
gam <UserTypeEntity> create|import|update event <UserCalendarEntity>
```

Added option `additionalmembers [<GroupRole>] <EmailAddressEntity>` to `gam update group|groups <GroupEntity> sync`
that can be used to specify members in addition to those specified with `<UserTypeEntity>`.
```
gam update group teachers@domain.com sync member additionalmembers counselor@domain.com ou /Teachers
```

Added commands to display Analytic account/property/datastream information.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Analytics-Admin

### 6.60.08

Upgraded to Python 3.11.4 where possible.

### 6.60.07

Simplified specifying a Chat space name; previously, the `space` keyword was required;
now, it can be omittted and you can just enter `spaces/<String>`.
```
<ChatSpace> ::= spaces/<String> | space <String> | space spaces/<String>
```

### 6.60.06

Fixed bug in `gam print aliases` that caused a trap.

### 6.60.05

Updated Chrome Policy commands to handle the following error:
```
ERROR: 403: permissionDenied - The caller does not have permission.
```

### 6.60.04

Updated `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>` to disallow copying/moving
a folder into itself.

### 6.60.03

Updated commands to delete chatmembers; `delete chatmembers` now deletes members by
specifying a chat space and user email addresses; `remove chatmembers` deletes members by
specifying chatmember names.
```
gam <UserTypeEntity> delete chatmember space <ChatSpace>
        ((user <UserItem>)|(members <UserTypeEntity>))+
gam <UserTypeEntity> remove chatmember members <ChatMemberList>
```

### 6.60.02

Added option `<ChatContent>` to `gam <UserTypeEntity> create chatspace` to allow sending an initial message
to the newly created chatspace.

### 6.60.01

Updated `gam <UserTypeEntity> create chatspace` to support chatspace types `GROUP_CHAT` and `DIRECT_MESSAGE`
and to allow specification of members.

### 6.60.00

Added initial support for user chat spaces. This is a work in progress, test and report any problems.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Chat

Improved performance of `gam <UserTypeEntity> delete|move|update othercontacts`.

Upgraded to OpenSSL 3.1.1 where possible.

### 6.59.18

Updated `gam <UserTypeEntity> update drivefile <DriveFileEntity>` to handle the following error:
```
ERROR: 403: fileWriterTeamDriveMoveInDisabled - The domain administrator has not allowed writers to move items into a shared drive.
```

### 6.59.17

Added option `pathdelimiter <Character>` to the following commands that causes GAM to separate
components in a folder path with `<Character>` rather than the default character `/`.
This can help avoid confusion when Google folder names contain a `/`.

Previously, on Windows, path components were separated by `\\` when written to a CSV file and
`\` when written to stdout; now, `/` or `<Character>` will be used in all cases.
```
gam <UserTypeEntity> info drivefile <DriveFileEntity>
gam <UserTypeEntity> show fileinfo <DriveFileEntity>
gam <UserTypeEntity> print filelist
gam <UserTypeEntity> print|show filepaths <DriveFileEntity>
gam <UserTypeEntity> transfer ownership <DriveFileEntity>
gam <UserTypeEntity> claim ownership <DriveFileEntity>
```

### 6.59.16

Updated `<GroupSettingsAttribute> whocancontactowner` to include option `all_owners_can_contact`.

### 6.59.15

Updated error reporting in `gam delete|update chromepolicy <SchemaName>` to show the `<SchemaName>` as originally entered
when an unknown `<SchemaName>` is specified; previously, it was shown in lowercase which could cause confusion.

Updated column order in `gam print chromeschemas` to move `schemaName`, `policyDescription` and `policyApiLifecycle.*`
to follow column `name`.

Added columns `policyDescription` and `policyApiLifecycleStage` to `gam print chromeschemas formatjson`
to follow column `name`.

### 6.59.14

Improve bug fix for `gam <UserTypeEntity> print groups|grouptree|groupslist`.

### 6.59.13

Fixed bug in `gam <UserTypeEntity> print groups|grouptree|groupslist` that caused the following
error whan an email address contained an apostrophe.
```
WARNING: Got 0 Groups: Invalid Member - test.o'user@domain.com
```

Fixed bug in `gam <UserTypeEntity> print|show contacts ... filtercontactgroup <PeopleContactGroupItem>` that returned
no contatcs when neither `allfields` or `fields <PeopleFieldNameList>` was specifiecd.

### 6.59.12

Fixed bug in `gam create user <EmailAddress> ... immutableous <OrgUnitEntity> ... createifnotfound`
that generated the following error when the user `<EmailAddress>` did not exist and needed to be created.
```
User: <EmailAddress>, Service not applicable/Does not exist
```

### 6.59.11

Updated `gam print|show chromepolicies` to query the following nameapaces when
`namespace <NamespaceList>` is not specified. Previously, only the namespaces
marked with a `*` were queried. `chrome.devices.managedguest` was added in 6.59.10.
```
chrome.users *
chrome.users.apps *
chrome.users.appsconfig
chrome.devices *
chrome.devices.kiosk *
chrome.devices.kiosk.apps
chrome.devices.managedguest *
chrome.devices.managedguest.apps
chrome.networks.cellular
chrome.networks.certificates
chrome.networks.ethernet
chrome.networks.globalsettings
chrome.networks.vpn
chrome.networks.wifi
chrome.printers
chrome.printservers
```

### 6.59.10

Fixed bug in `gam print|show chromepolicies` where policies in namespace `chrome.devices.managedguest`
were not displayed unless it was specified in `namespace <NamespaceList>`.

Improved error messages in `gam <UserTypeEntity> move events`.

### 6.59.09

Added option `addnumericsuffixonduplicate <Number>` to `gam create user <EmailAddress>` that
will attempt to create a unique `<EmailAddress>` when the original value is a duplicate user address.
If `<EmailAddress>` is `<String>@<DomainName>`, up to `<Number>` attempts will be made
to create a unique `<EmailAddress>`; `<Number>` defaults to 0.
```
<String>1@<DomainName>
<String>2@<DomainName>
...
```

### 6.59.08

Fixed bug in `csv_output_row_filter "FieldName:date<Operator>Never"` that didn't properly detect matches.
For example, the following command would not display users that had never logged in.
```
gam config csv_output_row_filter "lastLoginTime:date=Never" print users lastlogintime
```

### 6.59.07

Added option `immutableous <OrgUnitEntity>` to `gam <UserTypeEntity> update user ... org <OrgUnitPath>` that
does not update the user's OU to `<OrgUnitPath>` if `<OrgUnitPath>` appears in `<OrgUnitEntity>`. All other
fields are updated.

This can be used when a SIS outputs user data to be updated but students temporarily in special purpose
OUs should not be updated to the SIS specified OU. `<OrgUnitEntity>` and `<OrgUnitPath>` must both
specify OU paths, not IDs.
```
gam csv SISdata.csv gam update user "~primaryEmail" suspended off firstname "~First Name" lastname "~Last Name"
        ou "~OU" immutableous "'/Students/Lower School/Restricted,'/Students/Middle School/Restricted'"
```

### 6.59.06

Added option `sources <PeopleProfileSourceNameList>` to `gam <UserTypeEntity> print|show peopleprofile`
that allows specification of the sources of the data to display. By default, data from all sources is displayed.
```
<PeopleProfileSourceName> ::=
        account|accounts|
        domain|domains|
        profile|profiles
<PeopleProfileSourceNameList> ::= "<PeopleProfileSourceName>(,<PeopleProfileSourceName>)*"
```

Added option `updatefilepermissions [<Boolean>]` to `gam <UserTypeEntity> move drivefile <DriveFileEntity>`.
Previously, file permissions were not updated in the command; now, when `updatefilepermissions` is true,
file permissions will be removed/created as specified by the following noptions:
```
excludepermissionsfromdomains <DomainNameList>
includepermissionsfromdomains <DomainNameList>
mappermissionsdomain <DomainName> <DomainName>
```
Additionally, permissions referencing deleted groups/users will be removed.

The permissions are updated on the file before it is moved.

Test before using in production.

### 6.59.05

Added option `includepermissionsfromdomains <DomainNameList>` to the following commands
that copies only those permissions that reference any domain in `<DomainNameList>`.
It is mutually exclusive with `exludepermissionsfromdomains <DomainNameList>`.
```
gam copy|sync teamdriveacls <SharedDriveEntity>
gam <UserTypeEntity> copy|sync teamdriveacls <SharedDriveEntity>
gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>
```

### 6.59.04

Fixed bug in `gam <UserTypeEntity> print|show filesharecounts` where ACLs for deleted user/groups
were miscounted as external shares.

### 6.59.03

Cleaned up `Getting/Got` messages for several commands.

Improved performance of `gam print admins`.

### 6.59.02

Updated the Analytic account/property commands to use service account access so that data
can be retrieved for any user.

Fixed bug where the Analytics Admin API was not being added in `gam update project`
forcing you to manually enable it.

### 6.59.01

Updated `gam checkconnection` to check connections to the following sites:
```
Contacts API - Domain Shared Contacts - www.google.com
Email Audit API - apps-apis.google.com
Sites API - sites.google.com
```

### 6.59.00

Added commands to display Analytic account/property information.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Analytics-Admin

### 6.58.03

Fixed bug in `gam [<UserTypeEntity>] print shareddriveacls oneitemperrow shownopermissionsdrives true`
where the Shared Drives with no ACLs were not shown; they were shown if `oneitemperrow` was omitted.

### 6.58.02

Updated `gam <UserTypeEntity> print filelist ... filepath|fullpath` to not display parent information
for orphans. Previously, GAM would incorrectly display:
```
...,parents,parents.0.id,parents.0.isRoot,...
...,1,Orphans,False,...
```
Now the corrected display is:
```
...,parents,parents.0.id,parents.0.isRoot,...
...,,,,...
```
This change makes the output the same as when `filepath|fullpath` is omitted.

### 6.58.01

Added the following options to tag replace processing to allow control of the case of replacement data.

You can control the case of the letters in `replace <Tag> <String>` and `replace <Tag> <UserReplacement>`.
  * `{PC}...{Tag1}...{Tag2}...{/PC}` - For all sequences of letters between `{PC}` and `{/PC}`, the first letter is converted to uppercase, subsequent letters to lowercase.
  * `{UC}...{Tag1}...{Tag2}...{/UC}` - All letters between `{UC}` and `{/UC}` will be converted to uppercase
  * `{LC}...{Tag1}...{Tag2}...{/LC}` - All letters between `{LC}` and `{/LC}` will be converted to lowercase

### 6.58.00

Added `license_max_results` variable to `gam.cfg`.  When retrieving licenses from License API,
this variable controls how many should be retrieved in each chunk. The default value is 100; the range is 100-1000.
As of 2023-04-27, larger numbers cause Google to return an incorrect numbert of licenses.

### 6.57.11

Fixed bug where the `csv_output_header_force` variable in `gam.cfg` was being interpreted as
a list of `<RegularExpressions>` rather than a list of `<Strings>` as documented.

### 6.57.10

When doing commands similar to these:
```
gam redirect csv - multiprocess todrive csv Users.csv gam user "~primaryEmail" print filelist ...
gam config auto_batch_min 1 redirect csv - multiprocess todrive <UserTypeEntity> print filelist ...
```
GAM was including the name of the last user processed in the title of the uploaded Google Sheet;
as this is not accurate, it has been eliminated.

### 6.57.09

Added `emailaddresslist <EmailAddressList>` to `<PermissionMatch>` that allows matching any email address in a list.

### 6.57.08

Updated `gam <UserTypeEntity> print|show contacts|othercontacts` to retry the following error:
```
serviceNotAvailable - The service is currently unavailable.
```

### 6.57.07

Updated code to recognize the following Google Drive API error that is issued when Google
doesn't recognize an email address as valid.
```
$ gam user user@domain.com print filelist query "'j@ab.net' in writers" fields id,name
Getting all Drive Files/Folders that match query ('me' in owners and ('j@ab.net' in writers)) for user@domain.com

ERROR: 400: badRequest - Bad Request
$ gam user user@domain.com print filelist query "'j@ab.com' in writers" fields id,name
Getting all Drive Files/Folders that match query ('me' in owners and ('j@ab.com' in writers)) for user@domain.com
Got 0 Drive Files/Folders that matched query ('me' in owners and ('j@ab.com' in writers)) for user@domain.com...
Owner,id,name
```

### 6.57.06

Added `inherited <Boolean>` to `<PermissionMatch>` that applies only to Shared Drive files/folders;
this makes it easy to identify files/folders on Shared Drive with non-inherited permissions.
```
gam user organizer@domain.com print filelist select teamdriveid <TeamDriveID> fields id,name,mimetype pm inherited false em pmfilter oneitemperrow
```
This clause will always cause a permission match failure on My Drive files/folders.

### 6.57.05

Updated `gam batch <BatchContent>` and `gam tbatch <BatchContent>` commands to accept lines with the following form:
```
clear keyword
```
This can improve performance as subsequent lines in `<BatchContent>` will not be scanned for `%keyword%`.

### 6.57.04

Updated `gam batch <BatchContent>` and `gam tbatch <BatchContent>` commands to accept lines with the following form:
```
set keyword value
```
Subsequent lines in `<BatchContent>` will have `%keyword%` replaced with `value`.

### 6.57.03

Updated `gam <UserTypeEntity> info|print|show contacts|othercontacts` and
`gam info|print|show peoplecontacts|peopleprofiles` to default to displaying the fields `names,emailaddresses,phonenumbers`
as documented rather than all fields.

### 6.57.02

Following Jay's lead, removed Google bug (237397223) workaround code in
`gam print devices|deviceusers|crostelemetry` as the bug is now fixed.

### 6.57.01

Updated `gam <UserTypeEntity> vacation` to handle the following error:
```
ERROR: 400: failedPrecondition - Precondition check failed.
```
What the error means is unknown to me at the moment.

Updated GAM so that when the current project ID is required, it will first try to get it from oauth2service.json and
if not successful, try to get it from client_secrets.json. There are cases, e.g., when DASA is enabled,
that client_secrets.json is not present.

Previously, GAM checked for the existence of client_secrets.json on every command; this check has been
eliminated as the file is only required by `gam oauth create`.

### 6.57.00

Following Jay's lead, updated `gam create admin` to allow assignment of a delegated admin role to a group.
Updated `gam print admins` to display whether a role is assigned to a user or a group.

Updated version number to align with Standard GAM.

### 6.54.06

Added options `users <EmailAddressList>` and `groups <EmailAddressList>` to `gam print aliases` that is more
efficient for getting aliases for specific users and groups.

Added option `select <UserTypeEntity>` to `gam print aliases` that allows specification of a list users by `<UserTypeEntity>`;
e.g., a group or an org unit.

Added option `delimiter <Character>` to `gam print aliases` that is applicable when option `onerowpertarget` is specified.
Previously, multiple aliases were separated by a space character. Now, by default, the aliases are separated by the `csv_output_field_delimiter' from `gam.cfg`.
The option `delimiter <Character>` overrides that value.

### 6.54.05

Added option `addcsvdata <FieldName> <String>` to `gam print aliases`. This adds additional columns of data to the CSV file output.
This can be used when printing aliases for departed employees to indicate the new target for the user's alises. Subsequent
commands using the CSV file can reassign the aliases to the new target.

### 6.54.04

Updated `gam print|show channelcustomerentitlements` to handle the following error when
none of `gam.cfg/channel_customer_id` or command line arguments `channelcustomerid` or `name` are set.
```
ERROR: Parameter "parent" value "accounts/C03kt1789/customers/" does not match the pattern "^accounts/[^/]+/customers/[^/]+$"
```

### 6.54.03

By special request, British spelling of various keywords/arguments is now available.
```
backgroundcolor backgroundcolour
color colour
colorindex colourindex
costcenter costcentre
fileorganizer fileorganiser
foregroundcolor foregroundcolour
license licence
licenses licences
nolicenses nolicences
organization organisation
organizationname organisationname
organizations organisations
organizer organiser
organizeremail organiseremail
organizername organisername
textcolor textcolour
```

### 6.54.02

Updated `gam <UserTypeEntity> get photo` and `gam <UserTypeEntity> get profilephoto` to inspect the
photo data and add the appropriate extension: `jpg`, `png`, `gif`. If the type of the photo can't be
determined, `img` is used as the extenstion. If you use `[filename <FileNamePattern>]`, `#ext#` will be replaced
with the extension. 

Updated `gam <UserTypeEntity> [create|add] sendas <EmailAddress> [name] <String>` to allow the
optional argument `name` before `<String>` to make clear that `<String>` is the sendas display name.

### 6.54.01

Added commands to export messages/threads in EML/raw format.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Gmail-Messages-Threads#export-messagesthreads

### 6.54.00

Following Jay's lead, updated `gam delete inboundssoassignment <SSOAssignmentSelector>` to allow
more flexibility in selecting assignments to delete.

Fixed bug in `gam <UserTypeEntity> print|show filesharecounts` that would cause a trap.

Updated `gam <UserTypeEntity> print filelist ... fullpath showparent` and `gam <UserTypeEntity> print filepath`
to properly display the file path of My Drive.

Upgraded to Python 3.11.3 where possible.

Added commands to create and delete Chrome networks.
```
gam create chromenetwork
        <OrgUnitItem> <String> <JSONData>
gam delete chromenetwork
         <OrgUnitItem> <NetworkID>
```

### 6.53.03

`gam gam print|show svcaccts` now requires password authentication.

### 6.53.02

Added commands to display the share type counts of a user's files.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Display#display-file-share-counts

### 6.53.01

Following Jay's lead, added instructions to `gam create project` to have GAM be a trusted app.

### 6.53.00

Updated build steps to avoid trap with `gam create project` on M1 Macs.

Added option `noshowtextplain` to `gam <UserTypeEntity> show messages|threads` that suppresses
the default display of `text/plain` attachment content when `showattachments` is specified.

### 6.52.08

Added `maximumfilesize <Integer>` to the following commands to allow selection of files with content of size <= `<Integer>`.
```
gam <UserTypeEntity> print filelist
gam <UserTypeEntity> print|show filetree
gam <UserTypeEntity> print|show filecounts
```

Added field `workinglocationproperties` to `<EventFieldName>`.

* See: https://workspaceupdates.googleblog.com/2023/03/manage-working-location-feature-with-calendar-api.html

### 6.52.07

Fixed bug in `gam <UserTypeEntity> copy drivefile` that caused the following error:
```
ERROR: 403: parentNotAFolder - The specified parent is not a folder.
```

Current time is now printed in `gam version`.

### 6.52.06

Updated `gam <UserTypeEntity> create|update drivefile` to handle the following error that occurs when an attempt is
made to create/move a third-party shortcut on/to a Shared Drive.
```
ERROR: 403: teamDrivesShortcutFileNotSupported - The application associated with this third-party shortcut file does not support shared drives.
```

### 6.52.05

Added option `formatjson` to all commands that display Vault Matters, Exports, Holds adn Saved Queries.

Updated `gam <UserTypeEntity> move drivefile` to handle the following error that occurs when an attempt is
made to move a third-party shortcut to a Shared Drive.
```
ERROR: 403: teamDrivesShortcutFileNotSupported - The application associated with this third-party shortcut file does not support shared drives.
```

### 6.52.04

Fixed bug in `gam info vaultquery` and `gam print|show vaultqueries` that caused a trap
when the `query` field was omitted from the `fields <VaultQueryFieldNameList>`.

### 6.52.03

Added commands to display Vault Matter saved queries.
```
gam info vaultquery <QueryItem> matter <MatterItem>
        [fields <VaultQueryFieldNameList>] [shownames]
gam info vaultquery <MatterItem> <QueryItem>
        [fields <VaultQueryFieldNameList>] [shownames]
gam print vaultqueries [todrive <ToDriveAttribute>*] [matters <MatterItemList>]
        [fields <VaultQueryFieldNameList>] [shownames]
gam show vaultqueries [matters <MatterItemList>]
        [fields <VaultQueryFieldNameList>] [shownames]
```

Updated `gam info resoldcustomer <CustomerID>` to display the customer primary email.

Following Jay's lead, the following scopes will be off by default as changes to Google Cloud session control
may require frequent use of `gam aouth create`.

* See: https://workspaceupdates.googleblog.com/2023/03/google-cloud-session-length-default-update.html
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Authorization#introduction

```
[ ] 21)  Cloud Storage API (Read, Vault/Takeout Download)
[ ] 22)  Cloud Storage API (Write, Vault/Takeout Copy)
```

### 6.52.02

Following Jay's lead, added the following License SKUs:
```
1010380001 - AppSheet Core 
1010380002 - AppSheet Enterprise Standard
1010380003 - AppSheet Enterprise Plus
```

### 6.52.01

Fixed bug where `API calls retry data` was displaying incorrect values when processing CSV files.

### 6.52.00

Updated process handling for `gam batch|csv`.

### 6.51.08

Updated `gam create|update user <EmailAddress> ... <JSONData>` to exclude additional fields
from the JSON data that can't be copied; the following error was displayed:
```
User: user@domain.com, Create Failed: Invalid Input: Bad request for 
```

### 6.51.07

Fixed bug introduced in 6.51.06 that caused a trap in `gam create project`.

### 6.51.06

Following Jay's lead, added option `validityhours <Number>` to `gam create|replace|update sakeys` and `gam rotate sakey`
that let's you set the length of time a Service Account key is valid.

### 6.51.05

With input from Jay, further upgraded `gam <UserTypeEntity> check serviceaccount` to avoid a trap when a proxy is being used.

### 6.51.04

Upgraded `gam <UserTypeEntity> check serviceaccount` to avoid a trap when a proxy is being used.

### 6.51.03

* Upgraded to OpenSSL 3.1.0 where possible.

### 6.51.02

Added support for `externalid`, `im`, `posix`, `relation`, `sshkeys` and `website` subfields in `gam <UserTypeEntity> signature` and
`gam <UserTypeEntity> create|update sendas` option `replace <Tag> <UserReplacement>`.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Tag-Replace

### 6.51.01

Added option `nogcspath` to `gam download storagefile <StorageBucketObjectName>` that causes GAM
to store the downloaded file directly into the target folder without any Google Cloud Storage path information.

### 6.51.00

Added the ability to read data from Google Cloud Storage bucket objects.
```
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>
```
Anywhere you can enter `gdoc|ghtml <UserGoogleDoc>)` you can enter `gcsdoc|gcshtml <StorageBucketObjectName>`.

Anywhere you can enter `gsheet <UserGoogleSheet>)` you can enter `gcscsv <StorageBucketObjectName>`.

The Type of the Cloud Storage bucket objects must match the option keyword.

* gcsdoc - text/plain
* gcshtml - text/html
* gcscsv - text/csv

These options require that scope `Cloud Storage (Read, Vault/Takeout Download)` be enabled in `gam oauth create`.

Added a command to download a Cloud Storage bucket object.
```
gam download storagefile <StorageBucketObjectName>
        [targetfolder <FilePath>]
```

### 6.50.14

Fixed bug in `gam <UserTypeEntity> copy drivefile` that caused a trap.

Fixed bug where `removefeature` but not `removefeatures` was recognized in `gam update resource`.

### 6.50.13

Added options `addfeatures <FeatureNameList>` and `removefeatures <FeatureNameList>` to `<ResourceAttribute>`.
These can be used in in the following commands to make incremental changes to resource features.
```
gam update resource <ResourceID> <ResourceAttribute>*
gam update resources <ResourceEntity> <ResourceAttribute>*
```

Updated processing of `<FeatureNameList>` which is a `<ResourceAttribute>` to properly handle `<FeatureName>s` containing spaces.
When entering `<FeatureNameList>` with `<FeatureName>s`containing spaces, enclose the list in `"` and the names containing spaces in `'`.
```
features "CameraSet"
features "'Laptop Cart'"
features "CameraSet,'Laptop Cart'"
```

### 6.50.12

Handle new trap in `gam <UserTypeEntity> forward messages`.

### 6.50.11

Handle new trap in `gam <UserTypeEntity> forward messages`.

### 6.50.10

Fixed bug in `gam <UserTypeEntity> forward messages altcharset <String>` where `<String>` was marked as an invalid argument.

Updated `gam <UserTypeEntity> copy drivefile <DriveFileEntity>` to allow copying Google Sites.

### 6.50.09

Added command `gam info adminrole <RoleItem> [privileges]` that displays a specific admin role and optionally its privileges.

Added option `privileges` to `gam print|show admins` that displays the privileges for each role
for the admin.

### 6.50.08

Added option `altcharset <String>` to `gam <UserTypeEntity> forward messages` to attempt to handle
errors like the following which occur when the message can not be decoded with character set UTF-8.
You can specify an alternate character set, e.g. latin1, that is used if the UTF-8 decode fails.
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x92 in position 1643: invalid start byte
```

### 6.50.07

Fixed build bug that caused the following error:
```
ERROR: Discovery File: /usr/local/gamadv-xtd3/datastudio-v1.json, Does not exist or has invalid format, No data
```

### 6.50.06

Fixed bug in `gam report usage customer` where an extraneous column `email` was displayed.

### 6.50.05

Fixed bug in `gam update resoldsubscription` that caused an error:
```
ERROR: 400: invalid - The seats provided are not valid
```

### 6.50.04

Added `allowcontentmanagerstosharefolders` to `<SharedDriveRestrictionsSubfieldName>` that is used in
`gam create|update teamdrive`. This terminology matches the Admin console setting `Allow Content Managers to share folders`.

Each pair of commands below are equivalent:
```
gam update teamdrive <SharedDriveEntity> allowcontentmanagerstosharefolders true
gam update teamdrive <SharedDriveEntity> sharingfoldersrequiresorganizerpermission false

gam update teamdrive <SharedDriveEntity> allowcontentmanagerstosharefolders false
gam update teamdrive <SharedDriveEntity> sharingfoldersrequiresorganizerpermission true
```

Updated status reporting in `gam update chromepolicy` to supply more details.

Fixed bug in `gam update chromepolicy` when processing an schema field with an empty list.

### 6.50.03

Fixed bug in `gam update resoldsubscription` that caused an error:
```
ERROR: 400: invalid - Request contains an invalid argument. 
```

### 6.50.02

Fixed bug in `gam create project` where invalid data was written to client_secrets.json.

### 6.50.01

Fix YubiKey issue that caused a trap.

### 6.50.00

Following Jay's lead (with many thanks), added commands to enable running GAM securely on a Google Compute Engine.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Running-GAMADV-XTD3-securely-on-a-Google-Compute-Engine
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Using-GAMADV-XTD3-with-a-delegated-admin-service-account

Following Jay's lead (with many thanks), added commands to enable using a Yubikey.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Using-GAMADV-XTD3-with-a-YubiKey

These Wiki pages are a work in progress, contact me if you need help.

Updated handling of `seats` option in `gam create|update resoldsubscription` to properly assign
the API fields `numberOfSeats` and `maximumNumberOfSeats`.
Previously, this is how the option was processed:
  * Plan name `ANNUAL_MONTHLY_PAY` or `ANNUAL_YEARLY_PAY`
    * `seats <NumberOfSeats>` - `<NumberOfSeats>` was properly passed to the API
    * `seats <NumberOfSeats> <MaximumNumberOfSeats>` - `<NumberOfSeats>` was properly passed to the API; `<MaximumNumberOfSeats>` was passed to the API which ignored it
  * Plan name `FLEXIBLE` or `TRIAL`
    * `seats <NumberOfSeats>` - `<NumberOfSeats>` was improperly passed to the API; an API error was generated
    * `seats <NumberOfSeats> <MaximumNumberOfSeats>` - `<MaximumNumberOfSeats>` was properly passed to the API; `<NumberOfSeats>` was passed to the API which ignored it

Now, you can still use the above option which has been corrected or you can specify `seats <Number>` which will be properly passed in the correct form to the API based on plan name.

Hopefully fixed a bug in `gam <UserTypeEntity> forward messages` that caused a trap when the subject
contained Latin-1 characters.

### 6.42.10

Added option `accesstype public|team|announcementonly|restricted` to `gam create|update group`.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Groups#gui-api-group-access-type-settings-mapping

### 6.42.09

Cleaned up output in `gam print crostelemetry`; fields that are lists weren't being correctly sorted by index.

### 6.42.08

Added additional fields to `<CrOSTelemetryFieldName>`:
```
audiostatusreport|
bootperformancereport|
networkinfo|
networkdiagnosticsreport|
peripheralsreport|
thunderboltinfo|
networkdevices|
```

### 6.42.07

Improved `gam <UserTypeEntity> create|add drivefolderpath` to allow specifying paths
as returned by `gam <UserTypeEntity> print filepath`.

### 6.42.06

Fixed another bug in `gam <UserTypeEntity> create|add drivefolderpath` that failed when
trying to build a folder hierarchy on a Shared Drive.

### 6.42.05

Fixed bug in `gam <UserTypeEntity> create|add drivefolderpath` that failed when
trying to build a folder hierarchy on a Shared Drive.

### 6.42.04

Added a command that creates a folder hierarchy.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Manage#create-folder-hierarchy

### 6.42.03

Updated `gam <UserTypeEntity> get drivefile <DriveFileEntity> ... csvsheet <SheetEntity>` to allow
selection of the output format with `format <FileFormat>`. Previously, `csv` was always selected and
it is still the default. Valid formats are: `csv,tsv,ods,pdf,xlsx`.

### 6.42.02

Added `sha1checksum` and `sha256checksum` to `<DriveFieldName>`.
```
The SHA1/SHA256 checksum associated with a file, if available.
This field is only populated for files with content stored in Google Drive;
it isn't populated for Docs Editors or shortcut files.
```

Added option `addcsvdata <FieldName> <String>` to `gam <UserTypeEntity> print filelist` and
`gam print ownership`. This adds additional columns of data to the CSV file output.
```
Get a list of a user's shortcuts
gam redirect csv ./TSShortcuts.csv user user@domain.com print filelist fields id,name,parents,shortcutdetails showmimetype gshortcut
Headers
Owner,id,name,parents,parents.0.id,parents.0.isRoot,shortcutDetails.targetId,shortcutDetails.targetMimeType

For each shortcut, get the target file information; add the shortcut id, name and parent to the output
gam redirect csv ./TSShortcutFiles.csv multiprocess csv ./TSShortcuts.csv gam user user@domain.com print filelist select "~shortcutDetails.targetId" norecursion showownedby any
    fields id,name,mimetype,parents,owners.emailaddress addcsvdata shortcut.id "~id" addcsvdata shortcut.name "~name" addcsvdata shortcut.parents "~parents.0.id"
Headers
Owner,id,name,mimeType,owners,owners.0.emailAddress,parents,parents.0.id,parents.0.isRoot,shortcut.id,shortcut.name,shortcut.parents
```

### 6.42.01

Updated processing of option `matchlabel <LabelName>` to replace the following characters with a `-`
so that the query generated will work correctly. Previously, only ` ` (space) and `/` were replaced.
```
 &()"|{}/
```

### 6.42.00

Following Jay's lead, added commands commands to copy Google Vault and Organization Takeout data to your own GCS bucket.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Vault-Takeout#copy-vault-exports
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Vault-Takeout#copy-a-takeout-bucket

Updated `gam <UserTypeEntity> create contact` to treat the following options as errors;
previously, they were silently ignored.
```
addcontactgroup <ContactGroupItem>
removecontactgroup <ContactGroupItem>
```

Updated version number to align with Standard GAM.

### 6.32.05

Fixed bug in `gam show chromepolicies` that caused a trap.

Following Jay's lead, added `sharingfoldersrequiresorganizerpermission` to `<SharedDriveRestrictionsFieldName>` and
`<SharedDriveRestrictionsSubfieldName>`.

* See: https://workspaceupdates.googleblog.com/

### 6.32.04

Fixed bug in `gam <UserTypeEntity> move drivefile <DriveFileEntity>` where the following
error was not retried when `sendemailifrequired` was specified.
```
    User: user@domain.com, Drive Folder: Test, Permission: noninherited/writer/user/user@external.com, Copy Failed: You are trying to invite user@external.com. Since there is no Google account
              associated with this email address, you must check the "Notify people" box to invite this recipient.
```

### 6.32.03

Following Jay's lead, updated `gam create project` to handle the following error:
```
ERROR: 403: Permission 'resourcemanager.projects.get' denied on resource
```

### 6.32.02

Added support for `gender` subfields in `gam <UserTypeEntity> signature` and
`gam <UserTypeEntity> create|update sendas` option `replace <Tag> <UserReplacement>`.
```
<GenderSubfieldName> ::=
        addressmeas|
        customgender|
        type
<UserReplacementFieldSubfield> ::=
        ...
        gender.<GenderSubfieldName>|
        ...
```

### 6.32.01

Extended `csv_input_row_filter`, `csv_input_row_drop_filter`, `csv_output_row_filter` and `csv_output_row_drop_filter`
to allow specification of filters based on text comparisons.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Input-Filtering
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Output-Filtering

### 6.32.00

Added option `oneitemperrow` to `gam <UserTypeEntity> print filelist` to have each of a
files permissions displayed on a separate row with all of the other file fields. This produces
a CSV file that can be used in subsequent commands without further script processing.

Added option `pmfilter` to `gam <UserTypeEntity> print filelist` that is used in conjunction
with permission matching. By default, permission matching simply selects which files to display,
all ACLS are displayed. With `pmfilter`, only the ACLs that match are displayed.

### 6.31.09

Updated `gam gam <UserTypeEntity> create label <String>`, `gam <UserTypeEntity> create labellist <LabelNameEntity>`
and `gam <UserTypeEntity> update labelsettings <LabelName>` to expand the choices for label colors.
```
<ColorHex> ::= "#<Hex><Hex><Hex><Hex><Hex><Hex>"
<LabelColorHex> ::=
        #000000|#076239|#0b804b|#149e60|#16a766|#1a764d|#1c4587|#285bac|
        #2a9c68|#3c78d8|#3dc789|#41236d|#434343|#43d692|#44b984|#4a86e8|
        #653e9b|#666666|#68dfa9|#6d9eeb|#822111|#83334c|#89d3b2|#8e63ce|
        #999999|#a0eac9|#a46a21|#a479e2|#a4c2f4|#aa8831|#ac2b16|#b65775|
        #b694e8|#b9e4d0|#c6f3de|#c9daf8|#cc3a21|#cccccc|#cf8933|#d0bcf1|
        #d5ae49|#e07798|#e4d7f5|#e66550|#eaa041|#efa093|#efefef|#f2c960|
        #f3f3f3|#f691b3|#f6c5be|#f7a7c0|#fad165|#fb4c2f|#fbc8d9|#fcda83|
        #fcdee8|#fce8b3|#fef1d1|#ffad47|#ffbc6b|#ffd6a2|#ffe6c7|#ffffff
<LabelBackgroundColorHex> ::=
        #16a765|#2da2bb|#42d692|#4986e7|#98d7e4|#a2dcc1|
        #b3efd3|#b6cff5|#b99aff|#c2c2c2|#cca6ac|#e3d7ff|
        #e7e7e7|#ebdbde|#f2b2a8|#f691b2|#fb4c2f|#fbd3e0|
        #fbe983|#fdedc1|#ff7537|#ffad46|#ffc8af|#ffdeb5
<LabelTextColorHex> ::=
        #04502e|#094228|#0b4f30|#0d3472|#0d3b44|#3d188e|
        #464646|#594c05|#662e37|#684e07|#711a36|#7a2e0b|
        #7a4706|#8a1c0a|#994a64|#ffffff

backgroundcolor "<LabelColorHex>|<LabelBackgroundColorHex>|custom:<ColorHex>"
textcolor "<LabelColorHex>|<LabelTextColorHex>|custom:<ColorHex>"
```

### 6.31.08

Updated `csv_output_header_force` variable in `gam.cfg` that is a list of `<Strings>`
to be the exact list of headers to be included in the CSV file written by a gam print command.
This might be used when the CSV file data is to be uploaded into a database
and some headers may not be present in the output but must be included for the upload to work.

### 6.31.07

Added `csv_output_header_force` variable to `gam.cfg` that is a list of `<Strings>`
that are forced for inclusion in the CSV file written by a gam print command.
This might be used when the CSV file data is to be uploaded into a database
and some headers may not be present in the output but must be included for the upload to work.

### 6.31.06

Added support for new ChromeOS device fields:
```
<CrOSFieldName> ::=
        deprovisionreason|
        firstenrollmenttime|
        lastdeprovisiontimestamp|
```

### 6.31.05

Google can return an error `Internal error` on API calls; by default, GAM retries these API calls an additional 9 times
for a total of 10 tries. In some cases, determined by experience, the additional retries are unlikely to succeed and
GAM performs 1 additional retry rather than 9 for a total of 2 tries.

Added `bail_on_internal_error_tries` variable to `gam.cfg` that is used by GAM to control
the total number of tries for these API calls; Google seems to be sending this error when it is very busy.
The default value is 2 and values from 1 to 10 are allowed.
This is a rare event, this is an experiment to see if retrying these errors more times leads to success.

### 6.31.04

Added commands to display Chrome Devices Needing Attention counts.
```
gam print chromeneedsattn [todrive <ToDriveAttribute>*]
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [formatjson [quotechar <Character>]]
gam show chromeneedsattn
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [formatjson]
```

### 6.31.03

Added commands to display Chrome Auto Update Expiration counts.
```
gam print chromeaues [todrive <ToDriveAttribute>*]
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [minauedate <Date>] [maxauedate <Date>]
        [formatjson [quotechar <Character>]]
gam show chromeaues
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [minauedate <Date>] [maxauedate <Date>]
        [formatjson]
```

### 6.31.02

Updated `gam <UserTypeEntity> vacation` to process `(replace <Tag> <String>)*` in the subject.

### 6.31.01

Added option `nofile` to `gam <UserTypeEntity> get photo|profilephoto` that causes GAM to suppress
writing the photo data to a file. This would typicically be used when you are capturing the photo data
written to stdout.

### 6.31.00

Added `retry_api_service_not_available` variable to `gam.cfg` that is used to have GAM retry
`Service not applicable` errors on API calls; Google seems to be sending this error when it is very busy.
This is a rare event, this is an experiment to see if GAM can identify these errors and retry them.

### 6.30.18

Fixed bug in `gam <UserTypeEntity> move drivefile` where the modified time of files was inappropriately being changed.

### 6.30.17

Updated code for `gam <UserTypeEntity> get profilephoto size <Integer>` to account for API documentation error.

### 6.30.16

Added option `nodefault` to `gam <UserTypeEntity> get profilephoto` that causes GAM to display an
error message and set the return code to 50 if the user has a default profile photo.

### 6.30.15

Added option `gphoto <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>` to `gam <UserTypeEntity> update photo`
that specifies an owner and file to be used as the source of the photo.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Photo

### 6.30.14

Fixed bug in `gam <UserTypeEntity> print|show peopleprofile fields ...` where metadata was being displayed
even when `showmetadata` was not specified.

### 6.30.13

Fixed bug in `gam <UserTypeEntity> show fileinfo <DriveFileEntity> fields shortcutdetails.targetid` that caused a trap.

Added option `size <Integer>` to `gam <UserTypeEntity> get profilephoto` that specifies the size in pixels of the file to download.

### 6.30.12

Updated `gam update group <GroupEntity> update [<GroupRole>] [[delivery] <DeliverySetting>] <UserTypeEntity>`
to handle the following error when `<UserTypeEntity>` is an external member.
```
ERROR: 404: resourceNotFound - Does not exist
```
This is a Google bug where some external members can't be updated by email address.

### 6.30.11

Added option `emailmatchpattern [not] <RegularExpression>` to `gam <UserTypeEntity> delete group|groups`
that allows deleting a user from all groups of which they are a member based on (not) matching the group email address.

### 6.30.10

Added the ability to specify fields when displaying calendars.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Calendars
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Calendars

### 6.30.09

Added the following shortcuts to `<DriveFileQueryShortcut>`:
```
* my_top_files - "'me' in owners and mimeType != application/vnd.google-apps.folder and 'root' in parents"
* my_top_folders - "'me' in owners and mimeType = application/vnd.google-apps.folder and 'root' in parents"
* my_top_items - "'me' in owners and 'root' in parents"
```

### 6.30.08

Following Jay's lead, added the following License SKUs:
```
1010390001 - Assured Controls
1010400001 - Beyond Corp Enterprise
```

### 6.30.07

Added option `sheetsfields <SpreadsheetSheetsFieldList>` to `gam <UserTypeEntity> print|show sheet <DriveFileEntity>`
that lets you specfiy the desired subfields from the `sheets` field of a spreadsheet that should be displayed.
By default, all `sheets` subfields are displayed.
```
<SpreadsheetSheetsField> ::=
        bandedranges|
        basicfilter|
        charts|
        columngroups|
        conditionalformats|
        data|
        developermetadata|
        filterviews|
        merges|
        properties|
        protectedranges|
        rowgroups|
        slicers
<SpreadsheetSheetsFieldList> ::= "<SpreadsheetSheetsField>(,<SpreadsheetSheetsField>)*"
```

### 6.30.06

Fixed bug in `gam <UserTypeEntity> create|update|delete drivefileacl <DriveFileEntity> ... updatesheetprotectedranges`
that caused a trap.

### 6.30.05

Cleaned up code for option `updatesheetprotectedranges` in `gam <UserTypeEntity> create|update|delete drivefileacl <DriveFileEntity>`.

### 6.30.04

Improved output formatting for field `sheets` in  `gam <UserTypeEntity> info sheet <DriveFileEntity>`.

### 6.30.03

Updated `gam <UserTypeEntity> create|update drivefileacl <DriveFileEntity>` commands to handle the following error.
```
ERROR: 403: fileOrganizerOnFoldersInSharedDriveOnly - FileOrganizer role is only allowed on folders.
```

Added option `updatesheetprotectedranges` to `gam <UserTypeEntity> create|update|delete drivefileacl <DriveFileEntity>`
commands that causes GAM to update Sheet Protected Ranges if `<DriveFileEntity>` is a Google Sheet.

### 6.30.02

Fixed error message in `gam print cigroups` when an invalid field was specified.

### 6.30.01

Fixed bug in `gam create cigroup <EmailAddress> name <String> <GroupAttribute>+` where the group name was set to `<EmailAddress>` rather than `<String>`.

### 6.30.00

Added option `returnidonly` to `gam <UserTypeEntity> show fileinfo <DriveFileEntity>`
that causes GAM to return just the file ID of the files in `<DriveFileEntity>` file as output.
```
$ gam user user@domain.com show fileinfo root returnidonly
0AHYenC8f12ALUk9xyz

$ gam user testsimple show fileinfo name "Test File" returnidonly
0B3YenC8f12ALflhUTmtNS3E2Vk9LSUpBVXRSUG5lQ29GWkRtWHM1VzU1blc4ZW1pb2FnNTA
```

Changed the display format of file paths for files on Shared Drives.

* Old format - SharedDrive(TS Shared Drive 6)/TS SD6 Folder/TS TD6 Doc
* New format -SharedDrives/TS Shared Drive 6/TS SD6 Folder/TS TD6 Doc

Added option `returnpathonly` to `gam <UserTypeEntity> show filepath <DriveFileEntity>`
that causes GAM to return just the file path of the files in `<DriveFileEntity>` file as output.
```
$ gam user user@domain.com show filepath name "Test File" returnpathonly
My Drive/Classroom/Test File

$ gam user user@domain.com show filepath 0AJ6mqwXP9wHxUk9xyz returnpathonly
TS Shared Drive 6

$ gam user testsimple show filepath 0AJ6mqwXP9wHxUk9xyz returnpathonly fullpath
SharedDrive(TS Shared Drive 6)

$ gam user user@domain.com show filepath teamdriveid 0AJ6mqwXP9wHxUk9xyz teamdrivefilename "TS TD6 Doc" returnpathonly
SharedDrive(TS Shared Drive 6)/TS SD6 Folder/TS TD6 Doc
```

Added command `gam comment <String>*` that displays the comment data on stdout.
This can be used to validate `csv_input_row_filters` and column value extraction.
```
$ more Comment.csv 
col1,col2
aaa,111
bbb,222
ccc,333
$ gam config csv_input_row_drop_filter "col1:regex:bbb" csv Comment.csv gam comment "Col1:~~col1~~" "Col2:~~col2~~"
2022-12-16T12:41:50.045-08:00,0/2,Using 2 processes...
Col1:aaa Col2:111
Col1:ccc Col2:333
```

Updated `gam <UserTypeEntity> create|delete license <SKUIDList>` to take a list of SKUs.

Updated `gam create user <EmailAddress> ... license <SKUIDList>` to take a list of SKUs.

Updated `gam <UserTypeEntity> sync license <SKUIDList>` to take a list of SKUs and
added option `allskus|onesku` that is required when multiple SKUs are specified.

* `allskus` indicates that users in `<UserTypeEntity>` will  be updated to have all of the SKUs in `<SKUIDList>`.
  * This is typically used when assigning different types of licenses, such as an Enterprise license and a Voice license.
* `onesku` indicates that users in `<UserTypeEntity>` with none of the licenses in`<SKUIDList>` will be updated to have the first available license SKU in `<SKUIDList>`.
  * This is typically used with Google Education Plus or Google Education Standard licenses, which are split across multiple SKUs.

Added option `basic` to `gam print cigroups` that causes GAM to display the basic
Cloud Identity Group fields, i.e., those fields that do not require an additional API call per group.

Following Jay's lead, added option `query <String>` to `gam print cigroups`.

### 6.29.21

Fixed bugs in `gam selectfilter` that caused traps or inappropriate error messages.

### 6.29.20

Fixed bug in `gam <UserTypeEntity> archive messages <GroupItem>` that caused a trap.

### 6.29.19

Fixed bug introduced in 6.29.17 in `todrive` that caused a trap.

### 6.29.18

Added the following variables to `gam.cfg` to provide more flexibility when multiple row filters are specified.

* `csv_input_row_filter_mode allmatch|anymatch`
  * `allmatch` - all filters must match to include in input; this is the default and is the current behavior
  * `anymatch` - any filter must match to include in input
* `csv_input_row_drop_filter_mode allmatch|anymatch`
  * `allmatch` - all filters must match to drop from input
  * `anymatch` - any filter must match to drop from input; this is the default and is the current behavior
* `csv_output_row_filter_mode allmatch|anymatch`
  * `allmatch` - all filters must match to include in output; this is the default and is the current behavior
  * `anymatch` - any filter must match to include in output
* `csv_output_row_drop_filter_mode allmatch|anymatch`
  * `allmatch` - all filters must match to drop from output
  * `anymatch` - any filter must match to drop from output; this is the default and is the current behavior

### 6.29.17

Added option `todrive tdcellnumberformat text|number` that causes GAM to set the Sheet Number format when uploading files with `todrive`.

### 6.29.16

Fixed bug introduced in 6.29.15 that caused an error like this:
```
ERROR: Config File: gam.cfg, Section: DEFAULT, Item: todrive_locale, Value: "en_us", Expected: ,ar-eg,az-az,be-by,bg-bg,bn-in,ca-es,...
```

### 6.29.15

Updated `gam [<UserTypeEntity>] info|print|show drivelabels languagecode <DriveLabelLanguageCode>` to use the BCP-47 language code.

### 6.29.14

Added option `stripcrsfromtitle` to `gam <UserTypeEntity> print|show datastudioassets` that causes carriage returns,
linefeeds and nulls to be stripped from asset titles.

### 6.29.13

Updated status messages in `gam delete|update chromepolicy` to be more informative.

Fixed bug in `gam delete chromepolicy` with schema chrome.users.apps.InstallType.

### 6.29.12

Fixed issue in `gam update chromepolicy` with schemas `chrome.users.apps.ManagedConfiguration`,
`chrome.devices.managedguest.apps.ManagedConfiguration` and `chrome.devices.kiosk.apps.ManagedConfiguration`.

### 6.29.11

Improved performance of `gam update chromepolicy`.

### 6.29.10

Attempted to fix issues in `gam update chromepolicy` with schemas `chrome.users.apps.InstallType`
and `chrome.users.apps.IncludeInChromeWebStoreCollection`.

### 6.29.09

Fixed bug in `gam <UserTypeEntity> create tasklist` that caused a trap.

Added `countsonly` option to `gam <UserTypeEntity> print|show tasks|tasklists` that causes GAM to display
the number of tasks|tasklists for a user rather than listing the details.

Added option `due <Time>` to `<TaskAttribute>` that can be used to set a task due date
in `gam <UserTypeEntity> create|update` task.

Fixed bug in `gam update chromepolicy` that caused an error with this prefix:
`1 Chrome Policy Update Failed: Invalid enum value:`

### 6.29.08

Fixed bug where `csvfile -:fieldName` was not properly recognized on Windows.

### 6.29.07

Added option `from <EmailAddress>` to `gam create|update user ... notify <EmailAddressList>` that
uses `<EmailAddress>` as the from address rather than the admin user identified in oauth2.txt.

### 6.29.06

Following Jay's lead, added option `returnnameonly` to `gam create|update inboundssoprofile` that
causes GAM to display just the profile name of the created|updated profile. This will be useful
in scripts that create|update a profile and then want to perform subsequent GAM commands that
reference the profile.

### 6.29.05

Improved code for `gam [<UserTypeEntity>] create teamdrive <Name> ou <OrgUnitItem>`.

### 6.29.04

Updated multiprocessing on MacOS to use `spawn` instead of `fork` when starting subprocesses
as `fork` was unreliable when large numbers (>20) of threads were used; subprocesses would
hang and never complete.

### 6.29.03

Thanks to Jay, added support for the user field `displayName` that can be set independently of `fullName`.

### 6.29.02

Thanks to Jay, updated `gam info|print|show crostelemetry` to avoid the following trap:
```KeyError: 'temperatureCelsius'```

### 6.29.01

Fixed bug in `gam <UserTypeEntity> print|show labels` where fields `messageListVisibility`,
`labelListVisibility` and `color` were not displayed.

Fixed bug in `gam <UserTypeEntity> draft|insert|import message emlfile <FileName>` where the
`Date` header in the file was overridden with the current date.

### 6.29.00

Added option `emlfile <FileName>` to `gam <UserTypeEntity> draft|insert|import message` that
allows processing an EML message file. SMTP headers specified in the command will replace those in the message file.

Following Jay's lead, added commands to manage/display Inbound SSO.
* https://github.com/taers232c/GAMADV-XTD3/wiki/Inbound-SSO
* https://admin.google.com/ac/security/sso

### 6.28.12

Fixed bug in `gam create|update user ... password random notify <EmailAddress>` that caused a trap
when the random password contained `{` and `}`.

### 6.28.11

Fixed bug in  `gam <UserTypeEntity> update contact ... birthday ""` that caused a trap
rather that clearing the birthday from the contact.

### 6.28.10

Added option `addcsvdata <FieldName> <String>` to `gam create shareddrive ... csv`. This adds
additional columns of data to the CSV file output. For example, you are building student Shared Drives
and want to add ACLs to them adding the students as organizers. By adding the student's primary email address
to the CSV output, it can be used in subsequent commands.
```
StudentSharedDrives.csv
primaryEmail,Name
bob@domain.com,Bob Jones
mary@domain.com,Mary Smith
...

# Create the student Shared Drives
gam redirect stdout ./StudentSharedDrivesCreated.txt multiprocess redirect stderr stdout redirect csv ./StudentSharedDrivesCreated.csv multiprocess csv StudentSharedDrives.csv gam create shareddrive "~Name" csv addcsvdata primaryEmail "~primaryEmail"
# Add ACLs granting the students organizer access to their Shared Drives.
gam redirect stdout ./StudentSharedDrivesAccess.txt multiprocess redirect stderr stdout csv StudentSharedDrivesCreated.csv gam add drivefileacl "~id" user "~primaryEmail" role organizer
```

### 6.28.09

Updated `gam <UserTypeEntity> print filelist "query:mimeType='application/vnd.google-apps.folder'" to prevent the
following error.
```
ERROR: Invalid choice (query:mimetype='application/vnd): Expected <capabilities|contentrestrictions|labelinfo|labels|lastmodifyinguser|owners|parents|permissions|sharinguser|shortcutdetails|trashinguser>
```

### 6.28.08

Added option `today` to `gam report` to look for events on the current day. This will be most useful
with `gam report <ActivityApplictionName>` as `gam report users|customers` rarely has data for the current day.

Added option `today` to `gam <UserTypeEntity> print|show driveactivity` to look for events on the current day.

### 6.28.07

Added option `csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*` to `gam <UserTypeEntity> copy drivefile`
that causes GAM to output CSV data detailing the name, id and mimeType of the copied files and folders
rather than text messages. These are the CSV headers:
```
User,name,id,newName,newId,mimeType
```
You can add additional columns of data from the command line to the CSV data with `(addcsvdata <FieldName> <String>)*`.

Added option `suppressnotselectedmessages [<Boolean>]` to `gam <UserTypeEntity> copy drivefile`
that causes GAM to suppress text messages referencing files and folders not selected for copying by the following options:
```
copysubfiles false [filenamematchpattern <RegularExpression>] [filemimetype [not] <MimeTypeList>]
copysubfolders false [foldernamematchpattern <RegularExpression>
copysubshortcuts false [shortcutnamematchpattern <RegularExpression>
```

### 6.28.06

Fixed bug in `gam <UserTypeEntity> print|show messages ... showbody` that caused a trap.

Added code to handle the following error that occurs when copying permissions:
```
ERROR: 400: shareInNotPermitted - Bad Request. User message: "An item can't be shared with user@domain.com because of domain.com sharing policy"
```

### 6.28.05

Added the following items to `<UserMultiAttribute>`:
* `employeeid <String>` as a synonym for `externalids organization <String>`
* `manager <String>` as a synonym for `relations manager <String>`

Added the following items to `<UserFieldName>`:
* `employeeid` as a synonym for `externalids`
* `manager` as a synonym for `relations`

### 6.28.04

Added `filtercontactgroup <PeopleContactGroupItem>` to `<PeoplePrintShowUserContactSelection>`
that is used by `gam <UserTypeEntity> print|show contacts`. When `selectcontactgroup <PeopleContactGroupItem>`
is used in these commands, GAM makes an API call to get the list of contacts in `<PeopleContactGroupItem>`
and then makes an API call per contact to get the details; this may exceed quota limits.
When `filtercontactgroup <PeopleContactGroupItem>` is used, GAM makes an API call to get all contacts and
then filters the list to only those in `<PeopleContactGroupItem>`; quota limits should not apply.

### 6.28.03

Build MacOS x86_64 and arm64 executables.

### 6.28.02

Fixed bug in `gam forward message|thread` that misformatted the message when `Cc:` was present.

### 6.28.01

Fixed bug in `gam forward message|thread` where subject was blanked out.

### 6.28.00

* Upgraded to Python 3.11.0 where possible.
* Upgraded to OpenSSL 3.0.7 where possible.

Fixed bug in `gam forward message` where messages originally sent to multiple recipients
were not forwarded correctly.

Added command to forward threads; all messages referenced by the thread are forwarded; this is experimental, test.
```
gam <UserTypeEntity> forward thread|threads recipient|to <RecipientEntity>
        (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_forward <Number>])|(ids <MessageIDEntity>)
        [subject <String>]
```

### 6.27.21

Eliminated superfluous column header `labels` in `gam print cigroups`.

Added command to forward messages; this is experimental, test.
```
gam <UserTypeEntity> forward message|messages recipient|to <RecipientEntity>
        (((query <QueryGmail>) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_forward <Number>])|(ids <MessageIDEntity>)
```

### 6.27.20

Added option `url <URL>` to `gam <UserTypeEntity> create|update drivefile` that allows
GAM to upload files referenced by `URL` to Google Drive.

Added `csv_input_row_limit` variable to `gam.cfg` that is used to limit the number of rows read from a CSV file.

Added `csv_output_row_limit` variable to `gam.cfg` that is used to limit the number of rows written to a CSV file.

### 6.27.19

Added option `embedimage <FileName> <String>` to the following commands that allows
embedding images in HTML email messages.
```
gam sendemail [recipient|to] <RecipientEntity>
gam <UserTypeEntity> sendemail recipient|to <RecipientEntity>
gam <UserTypeEntity> sendemail from <EmailAddress>
gam <UserTypeEntity> draft|import|insert message
```

Your HTML message will contain lines like this:
```
<img src="cid:image1"/>
<img src="cid:image2"/>
```

Your command line will have: `embedimage file1.jpg image1 embedimage file2.jpg image2`

Added `archive` as a synonym for `archived` and `suspend` as a synonym for `suspended`
in `<UserBasicAttribute>`.

### 6.27.18

Added option `tdshare <EmailAddress> commenter|reader|writer` to `<ToDriveAttribute>`. When a new
todrive file is created, i.e., `tdfileid <DriveFileID>` is not specified, the uploaded file will
be shared as specified. `<EmailAddress>` must be valid within your Google Workspace.

### 6.27.17

Updated `todrive tdfileid <DriveFileID>` to display an informative error message when Google generates
an `Internal Error`. It appears that the file was successfully uploaded and converted to a sheet but
the conversion took longer that the API was willing to wait, so it generated the error.

### 6.27.16

Updated `todrive tdfileid <DriveFileID>` to not perform retries for `Internal Error` when updating an existing file
as the 6.27.15 update didn't fix the underlying problem.

### 6.27.15

Fixed bug in `gam show chromeschemas` that caused a trap due to unexpected data from Google.

Updated `gam <UserTypeEntity> collect orphans` to handle the error:
```
ERROR: 403: shortcutTargetInvalid - The specified file is not an allowed shortcut target type.
```
These are typically Google Backup & Sync images of laptops.

Fixed bug in `gam <UserTypeEntity> sendemail from <EmailAddress>` that reported:
```
User: user@domain.com, Send Email to 0 Recipients
```

Updated `todrive tdfileid <DriveFileID>` to perform retries for `Internal Error` when updating an existing file.

Added option `noselfowner` to all commands that print or show calendar ACls;
it suppresses the display of ACLs that reference the calendar itself as its owner.

### 6.27.14

Extended `gam print addresses` to include information about domains and resource calendars.
A new column `Target` was added that displays target information for user, group and domain aliases.

### 6.27.13

Added option `showdate` to `gam <UserTypeEntity> print|show messages|threads` that displays
the `internalDate` field for a message|thread.
```
The internal message creation timestamp (epoch ms), which determines ordering in the inbox.
For normal SMTP-received email, this represents the time the message was originally accepted by Google,
which is more reliable than the Date header. 
```

### 6.27.12

Added option `labellist <LabelNameEntity>` to `gam <UserTypeEntity> print|show labels`
to allow selection of labels to display.

Added option `cigrouptree` to `gam info user`. Previously, the `grouptree` option used
the Cloud Identity Groups API to display the users group tree structure. This API is licensed
and the command would generate an error if you didn't have the license. Now, the `grouptree` option
uses the Directory API and the `cigrouptree` option uses the Cloud Identity Groups API.

Updated `gam <UserTypeEntity> collect orphans` to not use shortcuts by default.
If an orphan file can have its parent changed without affecting its access by other users, the parent is changed.
If a parent change would affect the access by other users, a shortcut is created. You can still use
the `useshortcuts true` option to force the use of shortcuts. If you specify the `preview` option,
a new column, `action`, shows `changeParent` or `createShortcut` to indicate what action will be taken
when `preview` is omitted.

### 6.27.11

Added options `showparentsaslist [<Boolean>]` and `delimiter <Character>` to `gam print grouptree` and
`gam <UserTypeEntity> print grouptree` that display the group parent emails and names in two columns
as delimited lists rather than multiple indexed columns.

Added options `downloadattempts <Integer>` and `retryinterval <Integer>` to `gam download vaultexport`
that cause GAM to wait for a vault export to be completed. By default, GAM makes only one download attempt.
If multiple attempts are specified with `downloadattempts <Integer>`, GAM waits `retryinterval <Integer>` seconds between attempts; the default
retry interval is 30 seconds.

### 6.27.10

Added command `gam <UserTypeEntity> print|show grouptree` to display a user's groups and their parent groups.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Group-Membership#display-groups-and-their-parents

### 6.27.09

Corrected JSON output in `gam <UserTypeEntity> print userlist`.

### 6.27.08

Added command `gam <UserTypeEntity> print userlist` to display the list of users in `<UserTypeEntity>` in a single row.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users#print-user-list

### 6.27.07

Fixed bug introduced in 6.27.06 that caused commands that get a list of groups for a specific user to fail;
e.g., `gam info user user@domain.com`.

### 6.27.06

Fixed bug in `gam print addresses` where no output was generated.

Updated multiprocessing to fix issues on Mac OS where excuting commands from a CSV file would
hang if the number of threads was 20 or greater.

### 6.27.05

Updated `gam create vaultexport` to handle the following error that occurs when the
`region` option is specified but is not allowed by your licenses.
```
ERROR: 400: invalidArgument - Request contains an invalid argument.
```

### 6.27.04

Updated `gam download vaultexport` to replace `:` with `-` in the download filename to avoid
issues on Windows.

### 6.27.03

Fixed update in 6.27.01 to allow empty resource calendar feature lists.

### 6.27.02

Added options `labelinfo` and `<DriveLabelInfoSubfieldName>` to `<DriveFieldName>` and
option `includelabels <DriveLabelIDList>` to `gam <UserTypeEntity> show fileinfo` and
`gam <UserTypeEntity> print filelist` to allow easier access to display drive file labels.
This options do not require an extra API call like the `showlabels details|ids` option does.
```
gam user user@domain.com show fileinfo 1kM4T2K4l0CCdR8lmp0pdXcytghAzXZ2fe5ThQpDwxyz fields id,name,mimetype,labelinfo includelabels "mRoha85IbwCRl490E00xGLvBsSbkwIiuZ6PRNNEbbFcb"
gam user user@domain.com print filelist query "'labels/mRoha85IbwCRl490E00xGLvBsSbkwIiuZ6PRNNEbbFcb' in labels" fields id,name,mimetype,labelinfo.fields includelabels "mRoha85IbwCRl490E00xGLvBsSbkwIiuZ6PRNNEbbFcb"
```

### 6.27.01

Updated `<ResourceAttribute>` to allow `features ""` for resources.

### 6.27.00

Updated code to use Python yield functionality when downloading long lists of items from Google APIs.

### 6.26.17

Fixed bug in `gam <UserTypeEntity> print filelist ... showparent` where parent folder was not shown in all cases.

Following Jay's lead, updated `gam info customer|domain` to provide better information when executed by a non super admin.

### 6.26.16

Updated `gam <UserTypeEntity> collect orphans` to include orphaned folders that were previously
excluded due to multi-parenting issues.

### 6.26.15

Updated `gam <UserTypeEntity> collect orphans` to use shortcuts by default rather than making parent changes.

This addresses the following issue:
* `testuser2` owns a file `X1234` located in a folder owned by user `testuser1` and shared with additional users
* `testuser1` removes `testuser2's` access to that folder
* File `X1234` now looks like an orphan to `testuser2`
* `gam user testuser2 collect orphans useshortcuts false`
* This moves `X1234` to the folder `testuser2 orphaned files`; i.e., it has a new parent
* `testuser1` and all other users no longer have access to `X1234` as it is now in a folder for which they have no access

Updated `gam <UserTypeEntity> add|delete|update|print|show datastudiopermissions` to display an appropriate
error message, `The caller does not have permission`, when the user doesn't have permission to execute the command.
Previously, the following incorrect error message was displayed:
`ERROR: Data Studio API not enabled. Please run "gam update project" and "gam user user@domain.com check serviceaccount"`

### 6.26.14

Extended `csv_input_row_filter`, `csv_input_row_drop_filter`, `csv_output_row_filter` and `csv_output_row_drop_filter`
to allow specification of filters based on field string length.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Input-Filtering
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Output-Filtering

### 6.26.13

Fixed bug in `gam <UserTypeEntity> copy othercontacts` that caused it to move a contact rather than copy it.

### 6.26.12

Fixed bug in `gam <UserTypeEntity> replacedomain contacts` that caused the error `ERROR: Invalid argument`.

Fixed bug in `gam <UserTypeEntity> print filetree` where some orphaned files were not displayed.

### 6.26.11

Updated `gam info group <GroupEntity> ... formatjson` to omit `"cloudIdentity": {},`
from the output when no Cloud Identity fields are requested.

Updated `gam info user <UserTypeEntity>` error message reporting to give this
message for non-existent users in the primary or sub domains.
```
User: user@domain.com, Does not exist
User: user@sub.domain.com, Does not exist
```
Previously, a non-existent user in a sub domain gave this error.
```
User: user@sub.domain.com, Service not applicable/Does not exist
```
### 6.26.10

Fixed bug in `gam print deviceusers` where command would never terminate. This would also occur
in `gam print devices` when `nodeviceusers` was not specified.

Added option `select <DeviceID>` to `gam print deviceusers` that displays device users for a specific device.

### 6.26.09

With many thanks to Jay:

* Added more OpenSSL 3.0.5 support
* Added support for Linux Ubuntu 22.04 Jammy Jellyfish x86_64

### 6.26.08

* Upgraded to Python 3.10.7
* Updated google-api-python-client to version 2.60.0
* Dropped support for Linux Precise (glibc 2.15)

### 6.26.07

Fixed bug in `gam <UserTypeEntity> update photo "https://drive.google.com/thumbnail?sz=w300&id=xxxxxxxxxxxxxxxxx"`
that generated a `Update Failed: Not Found: xxxxxxxxxxxxxxxxx` error.

### 6.26.06

Added `endpointverificationspecificattributes` to `<DeviceFieldName>` used by `gam info device`
and `gam print devices`.

* See: https://cloud.google.com/endpoint-verification/docs/overview

### 6.26.05

Fixed bug in `gam <UserTypeEntity> update contacts ... removecontactgroup <ContactGroupItem>` that failed
to remove the contact group `<ContactGroupItem>` when it was specified as the contact group formatted name
as opposed to the resource name; e.g., `Work Contacts` as opposed to `contactGroups/2ef39b48f4e361a`.

### 6.26.04

Updated `gam print courses ... aliasesincolumns` to properly align `Aliases` columns.

### 6.26.03

Updated the following commands to display a usage error (`ERROR: Invalid file selection with adminaccess|asadmin`)
if `<DriveFileEntity>` does not reference Shared Drives. Previously, execution errors (`Shared drive not found: xxxx`) would be displayed.
```
gam [<UserTypeEntity>] create|add drivefileacl <DriveFileEntity> [adminaccess|asadmin]
gam [<UserTypeEntity>] update drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail> [adminaccess|asadmin]
gam [<UserTypeEntity>] delete drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail> [adminaccess|asadmin]
gam [<UserTypeEntity>] info drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail> [adminaccess|asadmin]
gam [<UserTypeEntity>] print drivefileacls <DriveFileEntity> [todrive <ToDriveAttribute>*] [adminaccess|asadmin]
gam [<UserTypeEntity>] show drivefileacls <DriveFileEntity> [adminaccess|asadmin]
gam [<UserTypeEntity>] create|add permissions <DriveFileEntity> <DriveFilePermissionsEntity> [adminaccess|asadmin]
gam [<UserTypeEntity>] delete permissions <DriveFileEntity> <DriveFilePermissionIDEntity> [adminaccess|asadmin]
```

### 6.26.02

Added option 'includederivedmembership' to `gam <UserTypeEntity> check groups` to allow 
checking if a user is a member of a group or one of its sub-groups.

### 6.26.01

Added option `nodetails` to gam <UserTypeEntity> print|show groups` that simply lists
the user's groups without making the addtional API call per group to get role, status and delivery settings.

Added command that allows checking if a user is a member of specific groups.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Group-Membership#check-users-group-membership

### 6.26.00

Build MacOS universal version.

* Upgraded to OpenSSL 3.0.5 where possible.

Updated code in `gam create course <CourseAttribute>* copyfrom <CourseID>` to avoid a trap
caused by Google returning unexpected data in the `DueTime` field for course work.

### 6.25.21

Fixed bug in `gam <UserTypeEntity> check drivefileshortcut` that caused a trap when checking
a shortcut on a Shared Drive.

### 6.25.20

Updated `gam <UserTypeEntity> print|show shareddrives` to handle spurious Google Drive API error.
```
ERROR: 404: fileNotFound - Does not exist
```

### 6.25.19

Updated code to reflect Google change in how Cloud Identity User Invitations API is authenticated.

### 6.25.18

Updated processing of CSV files to allow a Google Doc to be downloaded as plain text and processed as a CSV file.

These are allowed
```
gdoc <UserGoogleDoc>
gdoc:<FieldName>)+ <UserGoogleDoc>
```
wherever the following are allowed.
```
gsheet <UserGoogleSheet>
gsheet(:<FieldName>)+ <UserGoogleSheet>
```

### 6.25.17

Added options `[formatjson [quotechar <Character>]]` to `gam print group-members|cigroup-members`.

Following Jay's lead, improved command `gam checkconnection`.

### 6.25.16

Added the following option to `gam <UserTypeEntity> copy drivefile ... recursive` to allow more control
over what sub files are copied when a top folder is copied.
```
filemimetype [not] <MimeTypeList>
```

### 6.25.15

Following Jay's lead, added command `gam checkconnection` that performs checks to verify the network connection to Google.
This is an initial effort to help diagnose Google connection issues usually caused by firewalls and/or proxies.

* Upgraded to Python 3.10.6

### 6.25.14

Added the following options to `gam <UserTypeEntity> copy drivefile ... recursive` to allow more control
over what sub files, folders and shortcuts are copied when a top folder is copied.
```
copysubfiles [<Boolean>] filenamematchpattern <RegularExpression>
copysubfolders [<Boolean>] foldernamematchpattern <RegularExpression>
copysubshortcuts [<Boolean>] shortcutnamematchpattern <RegularExpression>
```

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Copy-Move#copy-files-and-folders

Added the following mutually exclusive options to `gam <UserTypeEntity> delete|update|sync|print|show groups`
to allow more control over which groups are processed for a user. The `customerid <CustomerID>` option
will be most useful to resellers.
```
domain <DomainName>
customerid <CustomerID>
```

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Group-Membership

### 6.25.13

Updated code in `gam report users` to handle bug in Report API that caused a trap; when the `userEmail` field is
mistakenly omitted, GAM backs up to an earlier date.

Updated `gam info user` to display the same data (in different formats) when `quick` is used with and without `formatjson`.

### 6.25.12

Added option `selectmaincontacts` to `<PeoplePrintShowUserContactSelection>` to allow more flexibility in selecting contacts to display
with `gam <UserTypeEntity> print|show contacts`.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-People-Contacts-Profiles#select-user-contacts

### 6.25.11

Updated error handling for `gam create|delete admin`.

### 6.25.10

Added option `norecursion [<Boolean>]` to `gam <UserTypeEntity> transfer ownership` to allow
ownership transfer of a folder but not its contents.

### 6.25.09

Fixed bug in `gam oauth info` that deleted the scopes in oauth2.txt if it had expired.

### 6.25.08

Added error checking to `gam create datatransfer` to avoid a trap.

### 6.25.07

Fixed bug introduced in 6.25.06 where only one row of a CSV file/Google Sheet was read by default.

### 6.25.06

Updated option `maxrows <Integer>` for `gam csv|loop` to be applied after input row filtering;
this allows limiting the number of filtered rows processed as opposed to the number of rows read.
* `maxrows 0` - All rows are processed, this is the default
* `maxrows N` - N filtered rows are processed

### 6.25.05

Added option `maxrows <Integer>` to `gam csv|loop` that allows you to limit the number of rows
read from the CSV file/Google Sheet. This can be used during testing in order to verify the functioning
of the command on a few rows before committing to all of the rows.
```
gam csv|loop <FileName>|-|(gsheet <UserGoogleSheet>) [charset <Charset>] [warnifnodata]
        [columndelimiter <Character>] [quotechar <Character>] [fields <FieldNameList>]
        (matchfield|skipfield <FieldName> <RegularExpression>)* [showcmds [<Boolean>]]
        [maxrows <Integer>]
        gam <GAMArgumentList>
```
* `maxrows -1` - All rows are read, this is the default
* `maxrows 0` - No rows are read
* `maxrows N` - N rows are read

### 6.25.04

Updated `gam create|update course ... copyfrom <CourseID> ... copytopics true` to preserve the topics order.

### 6.25.03

Updated `gam print users` to properly display the `languages` attribute based on the output format:
* `default` - `languages` column has the value `en+`
* `formatjson` - `JSON` column contains `"languages": [{"languageCode": "en", "preference": "preferred"}]`

### 6.25.02

Added option `missingtextvalue <String>` to `gam <UserTypeEntity> create note json ...` that causes GAM
to supply a value for JSON `list` and `text` items that are missing text fields. This option must appear
before the `json` option. If not specified and a text field is missing, you'll get the following error:
`Request contains an invalid argument.`

### 6.25.01

Updated license commands to retry the following error:
```
ERROR: 503: serviceNotAvailable - The service is currently unavailable.
```

Updated `https://apps.google.com/user/hub` to `https://workspace.google.com/dashboard` in the new user email message; thanks to @jay-eleven.

### 6.25.00

Added initial support for the Drive Labels API. GAM can display drive labels and it can apply them to files
and display drive labels on files. Please test/experiment and report any issues.

To use these commands you must add the 'Drive Labels API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com check serviceaccount
```
Supported editions for this feature: Business Standard and Business Plus; Enterprise; Education Standard and Education Plus; G Suite Business; Essentials.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Labels
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Display

### 6.24.27

Following Jay's lead, updated Cloud Identity API from v1beta1 to v1 for `userinvitations` commands.

### 6.24.26

Updated handling of shortcuts in `gam <UserTypeEntity> claim|transfer ownership`.

### 6.24.25

Corrected progress messages for `gam print groups showownedby`.

### 6.24.24

Added `gradebooksettings` to `<CourseFieldName>`.

### 6.24.23

Increase wait time in `gam create project` as Google is taking much longer to create projects.

### 6.24.22

Added option `license <SKUID> [product|productid <ProductID>]` to `gam create user` that assigns a
license to a user at the time of creation.

### 6.24.21

Fixed bug in `gam <UserTypeEntity> move drivefile ... createshortcutsfornonmovablefiles` that caused the following error:
```
ERROR: 403: shortcutTargetInvalid - The specified file is not an allowed shortcut target type.
```

### 6.24.20

Fixed bug in `gam <UserTypeEntity> claim ownership` that caused a trap.

### 6.24.19

* Upgraded to OpenSSL 1.1.1q

### 6.24.18

Added the following items to `<CrOSTypeEntity>`:
```
cros_ou_query <OrgUnitItem> <QueryCrOS>
cros_ou_and_children_query <OrgUnitItem> <QueryCrOS>
cros_ous_query <OrgUnitList> <QueryCrOS>
cros_ous_and_children_query <OrgUnitList> <QueryCrOS>
cros_ou_queries <OrgUnitItem> <QueryCrOSList>
cros_ou_and_children_queries <OrgUnitItem> <QueryCrOSList>
cros_ous_queries <OrgUnitList> <QueryCrOSList>
cros_ous_and_children_queries <OrgUnitList> <QueryCrOSList>
```
These allow specifying an OU, or a list of OUs, and a query or a list of queries
that apply to those OUs.

See: https://github.com/taers232c/GAMADV-XTD3/wiki/Collections-of-ChromeOS-Devices

Example:
```
gam cros_ou_query /StudentChromebooks "sync:..2019-01-01" update ou "/OldChromebooks"
```

### 6.24.17

Updated `gam report user` to avoid a trap due to an unexpected change in the Reports API.

### 6.24.16

Fixed bug in `gam update cros <CrOSEntity> ... updatenotes "#notes#"abc"` that caused a trap
when the ChromeOS device didn't previously have notes.

### 6.24.15

Added `pre_provisioned_disable` and `pre_provisioned_reenable` to `<CrOSAction>`.

Updated code to take advantage of an update to the directory API that simplifies getting
ChromeOS devices from an OU and its children.

Fixed bug in `gam create|update adminrole` where child privileges were not recognized in `<PrivilegesList>`.

### 6.24.14

Fixed bug introduced in 6.24.13 that prevented specifying a contact group by name.

### 6.24.13

The Customer ID value that the Cloud Channel API describes is not the Google Workspace Customer ID value; it is unique to the Cloud Channel API.

Added `channel_customer_id` variable to `gam.cfg` that is used in `gam print|show channelcustomercentitlements` to specify the default value for `customerid`
rather than `customer_id` from `gam.cfg`.

### 6.24.12

Changed how `selectcontactgroup <ContactGroupItem>` is processed in commands that process
user contacts. Previously, GAM would download all of a user's contacts and locally filter
to get only the contacts in `<ContactGroupItem>`. Now, the People API is used to get the
list of contacts in `<ContactGroupItem>` and they are are individually downloaded for processing.

### 6.24.11

Following Jay's lead, updated `gam print devices|deviceusers` to try to work around
a Google API internal bug (237397223) that generates the following error after an hour:
```
ERROR: 400: invalidArgument - Request contains an invalid argument.
```

### 6.24.10

Updated `gam print devices` to refresh the access token between listing the devices
and listing the device users to try to avoid the following error:
```
ERROR: 400: invalidArgument - Request contains an invalid argument.
```

### 6.24.09

Updated `gam print devices|deviceusers` to handle the following error:
```
ERROR: 503: serviceNotAvailable - The service is currently unavailable.
```

### 6.24.08

Added option `adminaccess` to `gam [<UserTypeEntity>] delete teamdrive <SharedDriveEntity>`
to allow Super Admins to delete Shared Drives even if they are not an organizer.

Added option `[<DriveFileParentAttribute>]` to `gam <UserTypeEntity> claim ownership <DriveFileEntity>`.
By default, `claim ownership` does not change the parents of `<DriveFileEntity>`; this options allows
specification of a parent folder in the My Drive of the claiming user `<UserTypeEntity>`.

Added option `[<DriveFileParentAttribute>]` to `gam <UserTypeEntity> transfer ownership <DriveFileEntity> <UserItem>`.
By default, `transfer ownership` does not change the parents of `<DriveFileEntity>`; this options allows
specification of a parent folder in the My Drive of the target user `<UserItem>`.

* Upgraded to Python 3.10.5
* Upgraded to OpenSSL 1.1.1p

### 6.24.07

Updated commands that process group settings to handle the following error:
```
ERROR: 401: authError - Authorization Failed
```

### 6.24.06

Improved `gam user user@domain.com print filecounts select teamdriveid "<DriveFileID>" summary only`
to display the Shared Drive ID and name on the summary line.

### 6.24.05

Updated option `orderby completed|due|updated` to `gam <UserTypeEntity> print|show tasks` to
display tasks in date order regardless of the hierarchy.

Fixed bug in 6.24.03 bug fix in `gam <UserTypeEntity> transfer drive <UserItem> ... targetfolderid root ...`.

### 6.24.04

Updated `gam update chromepolicy` to allow zero-length values for `TYPE_STRING` policy values;
this is required to be able to clear a value from such a policy.

### 6.24.03

Fixed bug in `gam <UserTypeEntity> transfer drive <UserItem> ... targetfolderid root ...` that
transferred data to the source user's root folder, not the target user's root folder.

### 6.24.02

Fixed bug in `gam print crostelemetry` that included a spurious column header, `devicdId`, in the output.

### 6.24.01

Updated `gam <UserTypeEntity> print|show tasks` to display tasks in hierarchical order.

Added option `orderby completed|due|updated` to `gam <UserTypeEntity> print|show tasks` to
display tasks in date order within the hierarchy.

### 6.24.00

Added commands to manage and display Google Tasks.
* https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Tasks

### 6.23.01

Updated `gam <UserTypeEntity> create|update|show|print form` to give a better error message when the Forms API is not enabled.
```
ERROR: 403: permissionDenied - Google Forms API has not been used in project XXXXXXX before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/forms.googleapis.com/overview?project=XXXXXXX then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.
```
is replaced with
```
ERROR: Forms API not enabled. Please run "gam update project" and "gam user user@domain.com check serviceaccount"
```

### 6.23.00

Updated `gam <UserTypeEntity> copy|move drivefile` to produce more
informative progress messages. The source file name(ID) are shown
as well as the target parent folder name(ID) and target file/folder name(ID).

Deleted options `copytopfileparents`, `copytopfolderparents` `copysubfileparents` and `copysubfolderparents`
from `gam <UserTypeEntity> copy drivefile` as multi-parent file/folders can not be copied with multiple parents.

Updated `gam <UserTypeEntity> copy drivefile` to use shortcuts when the same file appears more that once in the copy.
The first time the file is processed, it is copied; if it is processed again (because of multiple parents within the source
folder structure), a shortcut is created that points to the first copy.

Added option `copiedshortcutspointtocopiedfiles [<Boolean>]` to `gam <UserTypeEntity> copy drivefile`.
In previous versions, copying shortcuts caused an error because shortcuts can't be copied, they must be re-created.

If a shortcut in the source structure points to a file/folder that is not in the source structure:
 * The shortcut is re-created to point to the original file/folder.
If a shortcut in the source structure points to a file/folder that is in the source structure:
* `copiedshortcutspointtocopiedfiles` omitted or `copiedshortcutspointtocopiedfiles true` - The shortcut is re-created to point to the copied file/folder.
* `copiedshortcutspointtocopiedfiles false` - The shortcut is re-created to point to the original file/folder.

Deleted options `copysubfileparents` and `copysubfolderparents`
from `gam <UserTypeEntity> move drivefile` as multi-parent file/folders can not be moved with multiple parents.

Added option `createshortcutsfornonmovablefiles [<Boolean>]` to `gam <UserTypeEntity> move drivefile`
to control processing of non-movable files; for example, files owned by users outside of your domain.
It causes GAM to create a shortcut in the target folders for files in the source folders that are not movable.
* `createshortcutsfornonmovablefiles` omitted or `createshortcutsfornonmovablefiles false` - No shortcuts
are created and an error message is given explaining why the file can't be moved.
* `createshortcutsfornonmovablefiles true` - A shortcut is created that points to the non-movable file.

### 6.22.22

Fixed bug in `gam <UserTypeEntity> create|update contact` where the `relation` property was not properly processed.

### 6.22.21

Fixed bug where redirected stderr output from GAM main process was written
after GAM sub processes redirected stderr output.

### 6.22.20

The following update applies to one or two GAM users, if you're not one of them, stop reading.

When GAM is processing commands with data from a CSV file, `csv_input_row_drop_filter` and
`csv_input_row_filter` are evaluated and utilized by the GAM main process and are not
evaluated or processed by the GAM sub processes.

When GAM is processing commands with data from a CSV file, `csv_output_header_drop_filter`,
`csv_output_header_filter`, `csv_output_row_drop_filter` and `csv_output_row_filter` are
evaluated by the GAM main process and utilized by the GAM sub processes.

Evaluating the row filters once in the GAM main process means that `<RowValueFilter>`
forms `data:<DataSelector>` and `notdata:<DataSelector>` only read the data from `<DataSelector>` once.

### 6.22.19

Updated code to handle OUs with a `%` in their name. OUs with a `+` in their name
are still handled incorrectly by the API when accessed directly.

### 6.22.18

Added option `oneitemperrow` to `gam print vaultexports|exports` to have each of an
exports cloudStorageSink files displayed on a separate row.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Vault#display-vault-exports

Added options `bucketmatchpattern <RegularExpression>` and `objectmatchpattern <RegularExpression>`
to `gam download vaultexport|export` to allow selective downloading of export files.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Vault#download-vault-exports

### 6.22.17

Added `quick_cros_move` variable to `gam.cfg` that is used to provide the default value for `quickcrosmove [<Boolean>]` in:
```
gam update cros <CrOSEntity> <CrOSAttribute>+ [quickcrosmove [<Boolean>]] [nobatchupdate]
gam <CrOSTypeEntity> update <CrOSAttribute>+ [quickcrosmove [<Boolean>]] [nobatchupdate]
gam update org|ou <OrgUnitItem> add|move <CrOSTypeEntity> [quickcrosmove [<Boolean>]]
gam update org|ou <OrgUnitItem> sync <CrOSTypeEntity> [removetoou <OrgUnitItem>] [quickcrosmove [<Boolean>]]
```

Added `use_projectid_as_name` variable to `gam.cfg` that modifies `gam create project` to set
the default project name to the project ID instead of 'GAM Project' and to set the
default app name to the project ID instead of 'GAM'.

Improved error handling for the following error that occurs when the Customer ID is invalid.
```
ERROR: 400: invalidInput - Invalid Input
```

### 6.22.16

Corrected spelling of `spreadcheetid` to `spreadsheetid` and `spreadcheeturl` to `spreadsheeturl`
in `<SpreadsheetField>` used by `gam <UserTypeEntity> info|print|show sheet <DriveFileEntity>`.
```
<SpreadsheetField> ::=
        developermetadata|
        namedranges|
        properties|
        sheets|
        spreadsheetid|
        spreadsheeturl
```

### 6.22.15

Updated code to handle the following Oauth2 error:
```
ERROR: Authentication Token Error - access_denied: Account restricted
```

### 6.22.14

Added option `stripcrsfromname` to `gam <UserTypeEntity> print|show filepath` that causes carriage returns,
linefeeds and nulls to be stripped from file names.

Added option `fullpath` to `gam <UserTypeEntity> print|show filepath` and `gam <UserTypeEntity> show fileinfo`
that adds additional path information indicating that a file is an Orphan or Shared with me.

Added keywords `mydriveid` and `rootid` to `<DriveFileEntity>` as synonyms for `mydrive` and `root` in all
commands except `gam <UserTypeEntity> print filelist|filetree`. In those commands, `select mydrive|root`
is used to select a class of files; `select mydriveid|rootid` is used to select a folder starting point.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Display#display-file-list

### 6.22.13

Updated code to handle another Google API problem when updating the OU of a Chromebook.

### 6.22.12

Updated code to handle a Google API problem when updating the OU of a Chromebook.

### 6.22.11

Fixed bug in `gam download vaultexport|export` that caused a trap when the
`usenewexport true` option was used on the `gam create vaultexport|export` command
that created the matter.

### 6.22.10

Dropped deprecated argument `enforcesingleparent <Boolean>` from these commands:
```
gam <UserTypeEntity> create|add|update drivefile
gam <UserTypeEntity> create|add drivefileacl
gam <UserTypeEntity> create|add permissions
gam <UserTypeEntity> create|add sheet
```

### 6.22.09

Fixed bug in `gam print cros ...showdvrsfp` that caused a 'ZeroDivisionError: division by zero' trap.

### 6.22.08

Fixed bug where `gam info people` was not recognized as a valid command.

### 6.22.07

Fixed bug in `gam <UserTypeEntity> print|show filetree select <DriveFileEntity>` where the `stripcrsfromname`
option was not applied.

### 6.22.06

Updated code to handle Enterprise Licensing API issue with SKU 1010060001 (Google Workspace Essentials).

### 6.22.05

Fixed bug introduced in 6.22.04 in `gam print users` that caused a trap.

### 6.22.04

Fixed bug in `gam update drivefile <DriveFileEntity> ... parentid <DriveFolderID> newfilename <DriveFileName>`
where the file was not renamed.

The Enterprise License Manager API doesn't provide an option to get a list of the licenses a user holds.
For `gam info user`, GAM makes a batch API call with 47 product/SKU pairs querying whether the user holds
a license for the product/SKU. An error is returned (and suppressed) for each product/SKU pair for which
the user does not hold a license.

Currently, when you specify the `license` option with `gam print users`, GAM downloads all licenses for the domain
and from that data determines which licenses a user holds. For large numbers of users this works reasonably well;
for a small number of users the all license download might be overly expensive. The following options (synonyms)
`licensebyuser|licensesbyuser|licencebyuser|licencesbyuser` were added to `gam print users` that cause it
to use the batch API call method to retrieve the licenses for each user.

Additionally, these options `(products <ProductIDList>)|(skus <SKUIDList>)` can be used with both `gam info user`
and `gam print users` to limit the licenses retrieved.

Added `license_skus` variable to `gam.cfg` that defines the SKUs that will be processed when getting licenses.
Each item in the list can be  a `<SKUID>` which will be validated or `<ProductID>/<SKUID>` which will not.
The default, an empty string, means that all SKUs will be processed when getting licenses.

### 6.22.03

Fixed bug in `gam report customers|users ... date <Date> nodatechange` where previous
bug fix in 6.20.10 changed the format of the output.

### 6.22.02

Google has updated the Directory API to explicitly allow updating the OU of a Chromebook
with the OU ID rather than the OU path. The `update_cros_ou_with_id` variable in `gam.cfg` specifies
whether to use the OU ID or path to update the OU of a Chromebook.

The Directory API now supports displaying the OU ID of a Chromebook; added `orgunitid` to `<CrOSFieldName>`
to allow display of this attribute in `gam info|print cros`.

Added display of the OU ID of a Chromebook to `gam print crosactivity`.

### 6.22.01

Fixed bug in code introduced in 6.22.00 that caused a trap.

### 6.22.00

Extended `csv_input_row_filter`, `csv_input_row_drop_filter`, `csv_output_row_filter` and `csv_output_row_drop_filter`
to allow specification of filter values from a list, flat file or CSV file.

* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Input-Filtering
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/CSV-Output-Filtering

### 6.21.07

When setting a multivalued custom schema field for a user, if `type home|other|work|(custom <String>)` is not specified, 
`work` will be assigned. Previously, if type was not specified, Google would accept the field without a type
but would eventually set type to `work` itself in the background.

Added ProuctID `101036: Google Meet Global Dialing` and SKUID `meetdialing|googlemeetglobaldialing`;
thanks to @jay-eleven.

Added option `formatjson` to `gam info resoldcustomer <CustomerID>`.

### 6.21.06

Fixed bug in `gam update|use project` that caused the command to fail on Windows.

### 6.21.05

Fixed bug in `gam print|show projects|svcaccts` that caused a trap.

Added support for new calendar event read-only field `eventType`; thanks to @josemdv.

### 6.21.04

Updated handling of multivalued custom schema fields that are specified without a type;
the type will be shown as `work` as Google eventually sets the type to `work` itself in the background.

### 6.21.03

Fixed bug in `gam info|show schema` that caused a trap.

### 6.21.02

Updated `gam update chromepolicy` to allow specification of policy data with JSON.
For complex policies, this is the only way to enter the policy data.
```
gam update chromepolicy
        (<SchemaName>
          (<Field> <Value>)+ |
          (json [charset <Charset>] <JSONData>) |
          (json file <FileName> [charset <Charset>])
        )+
        ou|org|orgunit <OrgUnitItem> [(printerid <PrinterID>)|(appid <AppID>)]
```

### 6.21.01

Added `clock_skew_in_seconds` variable to `gam.cfg` that defines the number of seconds
of clock skew allowed between local time and Google time. The default value is 10 seconds
which was the previous hard-coded value.

Updated GAM spreadsheet commands to handle the following error:
```
ERROR: 400: failedPrecondition - This operation is not supported for this document
```

### 6.21.00

Following Jay's lead, added option `allowitemdeletion` to `gam [<UserTypeEntity>] delete shareddrive <SharedDriveEntity>`
that allows deletion of non-empty Shared Drives. This option requires a Super Admin user.

### 6.20.10

Fixed bug in `gam report customers|users ... date <Date> nodatechange` where no data was returned
in some cases when `allverifyuser <UserItem>` was not specified.

### 6.20.09

Added option `aliasmatchpattern <RegularExpression>` to `gam print users` that limits the display of aliases
to those that match `<RegularExpression>`.

### 6.20.08

Fixed bug in `gam <UserTypeEntity> copy|move drivefile` that caused a trap when a Shared Drive was involved.

### 6.20.07

Additional fixes to bug that caused a trap when `config csv_output_timestamp_column` and `formatjson` were used in the same command.

### 6.20.06

Fixed bug that caused a trap when `config csv_output_timestamp_column` and `formatjson` were used in the same command.

### 6.20.05

Updated options `notarchived|archived` in `gam update group|groups <GroupEntity> add|remove|sync`
to be usable with additional `<UserTypeEntity>`.

### 6.20.04

Added option `dynamicsecurity|makedynamicsecuritygroup` to `gam update cigroups <GroupEntity>`
so you can update a dynamic group to be a security group. You should use this option if you use
this option `security|makesecuritygroup` and get this error:
```
ERROR: 400: invalidArgument - Error(2022): Removing labels is not supported.
```

### 6.20.03

Fixed handling of Shared Drive API errors that was broken in 6.20.00.

### 6.20.02

Fixed bug in `gam <UserTypeEntity> create drivefileacl <DriveFileEntity ... csv formatjson` that caused a trap.

### 6.20.01

Added code to validate values in `<CAARegionList>` in `gam create|update caalevel`.

### 6.20.00

Following Jay's lead, updated `gam [<UserTypeEntity>] print|show teamdrives` to display
the `orgUnit` path for a Shared Drive in addition to its `orgUnitId`. The org unit information
is only available when the command is run as an administrator. Additional API calls are
necessary to get the `orgUnit` path; the option `noorgunits` disables the additional API
calls and display of the path .

Following Jay's lead, added option `ou|org|orgunit <OrgUnitItem>` to `gam [<UserTypeEntity>] update teamdrive` to
move the Team Drive to the specified OU. This option is only available when the command is run as an administrator.
As Jay says: THIS FEATURE IS CURRENTLY ALPHA.

Follwing Jay's lead, added commands to manage/display Context-Aware Access Levels.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Context-Aware-Access-Levels

### 6.18.04

Added the ability to upload Note attachments to Google Drive.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Keep#download-note-attachments

### 6.18.03

Added command to download Note attachments.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Keep#download-note-attachments

Updated `gam delete|update schema` to handle the following error:
```
ERROR: 500: FIELD_IN_USE - Cannot delete a field in use.resource.fields
```

### 6.18.02

Updated `gam create project` to proceed even if one or two APIs fail to be enabled;
currently, any failure terminates the project creation.

### 6.18.01

* Upgraded to Python 3.10.4

### 6.18.00

Added initial support for the Cloud Channel API; this is used by resellers.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Cloud-Channel

### 6.17.02

Added a command to update basic form settings.
```
gam <UserTypeEntity> update form <DriveFileEntity>
        [title <String>] [description <String>] [isquiz [Boolean>]
```

### 6.17.01

Fixed bug in `gam <UserTypeEntity> print forms` that caused a trap when a form has no title.

### 6.17.00

Added initial support for the Forms API.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Forms

Fixed bug in `gam <UserTypeEntity> print|show filecounts ... showmimetype [not] <MimeTypeList>` that
removed `'me' in owners` from the query.

* Upgraded to Python 3.10.3
* Upgraded to OpenSSL 1.1.1n

### 6.16.19

Fixed bug in `gam print vaultcounts matter <MatterItem> corpus mail accounts <EmailAddressEntity>` where
extraneous lines `emails,0,` appeared in the output.

### 6.16.18

Fixed bug in `gam update contactphotos` and `gam <UserTypeEntity> update contactphotos` where
option `drivedir|(sourcefolder <FilePath>)` was not properly processed. Unfortunately, the
Domain Shared Contacts API seems to be broken when trying to manage contact photos.

### 6.16.17

Updated `gam <UserTypeEntity> replacedomain contacts emailmatchpattern <RegularExpression> domain <OldDomainName> <NewDomainName>`
to only replace `<OldDomainName>` with `<NewDomainName>` in the email addresses within the contact that match `<RegularExpression>`.
Previously, `emailmatchpattern <RegularExpression>` selected a contact and all email addresses within the contact had
their domain names updated if applicable.

### 6.16.16

Added option `aggregateusersby clientid|appname` to `gam <UserTypeEntity> print|show tokens` that
aggregates the users by `clientid|appname` and displays a count of the number of users rather
than the individual users for each `clientid|appname`.

### 6.16.15

Updated to allow new 10 million cell limit in Google Sheets.
* See: https://workspaceupdates.googleblog.com/2022/03/ten-million-cells-google-sheets.html

### 6.16.14

Added command to replace domain names in contact email addresses; this can be useful
when merging/renaming domains.
```
gam <UserTypeEntity> replacedomain contacts
        [<PeopleResourceNameEntity>|<PeopleUserContactSelection>]
        (domain <OldDomainName> <NewDomainName>)+
```

Fixed sorting of permissions in `gam <UserTypeEntity> print drivefileacls`.

### 6.16.13

Fixed the fix in 6.16.12.

### 6.16.12

Updated code to eliminate fix for a Python 3.10.0 bug that caused `gam <UserTypeEntity> print notes ... formatjson`
to display quotes in note text incorrectly.

### 6.16.11

Fixed bug in `gam <UserTypeEntity> show notes` that caused a trap when a note has no text
or a check box has no text.

### 6.16.10

Fixed bug in `gam <UserTypeEntity> print notes ... formatjson` where carriage returns and line feeds
were not properly displayed.

Fixed bug in `gam <UserTypeEntity> create note ... json` where carriage returns and line feeds
were not properly input.

### 6.16.09

Added option `role|roles <DriveFileACLRoleList>` to `gam <UserTypeEntity> print|show drivefileacls`
to simplify limiting displayed ACLs by role.

### 6.16.08

Added command to upload image files for use in Chrome policies.
```
<ChromePolicyImageSchemaName> ::=
        chrome.devices.managedguest.avatar |
        chrome.devices.managedguest.wallpaper |
        chrome.devices.signinwallpaperimage |
        chrome.users.avatar |
        chrome.users.wallpaper

gam create chromepolicyimage <ChromePolicyImageSchemaName> <FileName>
```

### 6.16.07

Extended option `stripcrsfromname` option in the following commands to strip nulls and linefeeds
from displayed file names in addition to carriage returns.
```
gam <UserTypeEntity> info drivefile <DriveFileEntity>
gam <UserTypeEntity> print|show filerevisions <DriveFileEntity>
gam <UserTypeEntity> show fileinfo <DriveFileEntity>
gam <UserTypeEntity> print|show filetree
gam <UserTypeEntity> print filelist
```

### 6.16.06

Updated code to remove Python 3.9 dependency introduced in 6.16.05.

### 6.16.05

Added option `domain <DomainName>` to `gam print aliases` to simplify printing aliases from a secondary domain.

### 6.16.04

Fixed bug in `gam <UserTypeEntity> get drivefile` that caused a trap when the target file couldn't be written.

### 6.16.03

Fixed bug that broke `vault` commands.

Updated `gam oauth create` to use client access authentication flow as in Standard GAM, `config no_browser true` is no longer necessary.

### 6.16.02

Following Jay's lead, added option `removeresetlock` to `gam wipe device <DeviceEntity>` that will remove the account lock
on the Android or iOS device. This lock is enabled by default and requires the existing device user to log in after the wipe in order to unlock the device.
* See: https://support.google.com/android/answer/9459346

Following Jay's lead, added option `usenewexport <Boolean>` to `gam create vaultexport ... corpus mail`.
* See: https://support.google.com/vault/answer/4388708#new_gmail_export&zippy=%2Cfebruary-new-gmail-export-system-available

### 6.16.01

Updated `gam oauth create` to allow retries when `no_browser` is true and the user
enters an invalid authentication code.

### 6.16.00

With many thanks to Jay, updated `gam oauth create` to use a new client access authentication flow
as required by Google for headless computers/cloud shells; this is required as of February 28, 2022.
* See: https://developers.googleblog.com/2022/02/making-oauth-flows-safer.html
  * OAuth out-of-band (oob) flow will be deprecated

### 6.15.24

Cleaned up `gam report` commands again to improve verification that valid data has been received.

Fixed bug in `gam <UserTypeEntity> dedup contacts` where `<PeopleResourceNameEntity>|<PeopleUserContactSelection>`
was not optional as documented.

### 6.15.23

Added option `replacefilename <RegularExpression> <String>` to `gam <UserTypeEntity> copy|update drivefile`
that allows using regular expressions to modify the copied/updated file name.
```
gam user user@domain.com update drivefile query "name contains '2020-2021'" replacefilename "2020-2021" "2021-2022"
gam user user@domain.com copy drivefile name Template parentid root recursive replacefilename Template NewCustomer
```
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Files-Manage#update-files
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Copy-Move#copy-files-and-folders

### 6.15.22

Cleaned up `gam report` commands to improve verification that valid data has been received.

### 6.15.21

Added email audit monitor commands that were deleted in 5.34.00.
```
gam audit monitor create <EmailAddress> <DestEmailAddress> [begin <DateTime>] [end <DateTime>]
        [incoming_headers] [outgoing_headers] [nochats] [nodrafts] [chat_headers] [draft_headers]
gam audit monitor delete <EmailAddress> <DestEmailAddress>
gam audit monitor list <EmailAddress>
```
To use these commands, you should do:
```
gam update project
gam oauth create
```

### 6.15.20

Fixed bug in `gam <UserTypeEntity> print datastudiopermissions` where `todrive` was not recognized.

### 6.15.19

Further cleanup of `gam create|update alias`.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Aliases

### 6.15.18

After discussions with Jay, the default for creating/updating aliases is to verify that
the target `<UniqueID>|<EmailAddress>` exists by making extra API calls;
if you know that the target exists, you can suppress the verification with `notargetverify`.

### 6.15.17

Added option `verifytarget` to `gam create|update alias <EmailAddressEntity> user|group|target <UniqueID>|<EmailAddress>`
that causes Gam to verify that the target `<UniqueID>|<EmailAddress>` exists.

### 6.15.16

Updated `gam <UserTypeEntity> deprovision` and `gam <UserTypeEntity> delete|update backupcodes`
to give a more informative error message when a user is suspended and backup codes can't be deleted|updated.

### 6.15.15

Fixed bug in `gam print crosactivity recentusers oneuserperrow` that caused a trap.

### 6.15.14

Added option `setchangepasswordoncreate [<Boolean>]` to `gam <UserTypeEntity> update user` that can be used
to force created (as opposed to updated) users to change their password at their next login.

### 6.15.13

Updated error messages in `gam <UserTypeEntity> update user createifnotfound`.

### 6.15.12

Added option `notifyonupdate [<Boolean>]` to `gam <UserTypeEntity> update user` that can be used
to suppress the email notificaton when options `notify <EmailAddressList> notifypassword <String>`
are specified for use in the case when the user must be created but not used when the user does exist
and is simply updated.

### 6.15.11

Updated `gam create cigroup` to handle the following error:
```
ERROR: 403: permissionDenied - Error(3006): This feature (Dynamic Groups) requires a premium SKU.
```

### 6.15.10

Fixed bug in `gam update ou / add|move ...` that caused the following error:
```
ERROR: 400: invalid - Invalid field selection orgUnitPath
```

### 6.15.09

Updated option `corpus` in `gam print vaultcounts` to only allow `mail` and `groups` as
required by the API.

### 6.15.08

Following Jay's lead, added option `condition securitygroup|nonsecuritygroup` to `gam create admin`
and option `condition` to `gam print|show admins`.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Administrators

### 6.15.07

Updated code in `gam print cros` to handle a missing data field that caused a trap.

### 6.15.06

Added option `dateheaderconverttimezone [<Boolean>]>` to `gam <UserTypeEntity> print|show messages|threads` that allows
converting `<SMTPDateHeader>` values to the `gam.cfg timezone`.

Updated option `dateheaderformat iso|rfc2822|<String>` to `gam <UserTypeEntity> print|show messages|threads` that allows
reformatting of the message `Date` header value from RFC2822 format to the the following:
* `iso` - Format is `%Y-%m-%dT%H:%M:%S%z`
* `rfc2822` - Format is `%a, %d %b %Y %H:%M:%S %z`
* `<String>` - Format according to: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

### 6.15.05

Added option `dateheaderformat <String>` to `gam <UserTypeEntity> print|show messages|threads` that allows
reformatting of the message `Date` header from RFC2822 format to the format specified by `<String>`.
If `<String>` is `iso`, then ISO 8601 format is used, otherwise see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
If the `Date` header can't be parsed as RFC2822, it is left unchanged.

### 6.15.04

Fixed bug in `gam <UserTypeEntity> copy drivefile <DriveFileEntity> ... excludepermissionsfromdomains <DomainNameList>` that caused a trap.

### 6.15.03

Updated `<CourseAttribute>` and `<CourseFieldName>` to use `descriptionheading` and `heading` synonymously.

### 6.15.02

Added the following options to `gam <UserTypeEntity> copy drivefile <DriveFileEntity>`
that provide more flexibility in managing permissions when copying/moving folders.
* Thanks to Kevin Sanghvi for suggesting these enhancements.
```
copysheetprotectedrangesinheritedpermissions [<Boolean>]
copysheetprotectedrangesnoninheritedpermissions [<Boolean>]
```
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Copy-Move#copy-permissions

### 6.15.01

Fixed bug in `gam <UserTypeEntity> print|show messages ... showattachments|saveattachments` where
some attachments were not recognized.
* Thanks to Craig Millsap for spending the time with me to find the solution.

### 6.15.00

Updated processing of `teamdrive <SharedDriveName>` in the following commands.
Previously, if there were multiple Shared Drives with the same `<SharedDriveName>`, GAM silently processed
the first one which may not have been the desired action. Now, a message is issued listing the multiple `<DriveFileIDs>` and
no processing is performed. Determine which Shared Drive ID is desired and reissue the command with `teamdriveid <DriveFileID>`.
```
gam <UserTypeEntity> print filelist select teamdrive <SharedDriveName>
gam <UserTypeEntity> print|show filecounts select teamdrive <SharedDriveName>
gam <UserTypeEntity> print|show filetree select teamdrive <SharedDriveName>
gam <UserTypeEntity> update teamdrive teamdrive <SharedDriveName>
gam <UserTypeEntity> delete teamdrive teamdrive <SharedDriveName>
gam <UserTypeEntity> hide teamdrive teamdrive <SharedDriveName>
gam <UserTypeEntity> unhide teamdrive teamdrive <SharedDriveName>
gam <UserTypeEntity> info teamdrive teamdrive <SharedDriveName>
gam <UserTypeEntity> print emptydrivefolders teamdrive <SharedDriveName>
gam <UserTypeEntity> delete emptydrivefolders teamdrive <SharedDriveName>
gam <UserTypeEntity> empty drivetrash teamdrive <SharedDriveName>
```

Added the following commands to transfer top level ACLs from one Shared Drive to another.
```
gam [<UserTypeEntity>] copy teamdriveacls <SharedDriveEntity> to <SharedDriveEntity>
        [adminaccess|asadmin]
        [showpermissionsmessages [<Boolean>]]
        [excludepermissionsfromdomains <DomainNameList>]
        (mappermissionsdomain <DomainName> <DomainName>)*
gam [<UserTypeEntity>] sync teamdriveacls <SharedDriveEntity> with <SharedDriveEntity>
        [adminaccess|asadmin]
        [showpermissionsmessages [<Boolean>]]
        [excludepermissionsfromdomains <DomainNameList>]
        (mappermissionsdomain <DomainName> <DomainName>)*
```

Added option `shownopermissionsdrives false|true|only` to `gam <UserTypeEntity> print|show teamdriveacls` that
controls whether Shared Drives with no permissions are displayed.
* `false` - Do not display Shared Drives with no permissions; this is the default
* `true` - Display Shared Drives with no permissions in addition to Shared Drives with permissions
* `only` - Display only Shared Drives with no permissions

Added the option `mappermissionsdomain <DomainName1> <DomainName2>` to `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>`
that maps `<DomainName1>` to `<DomainName2>` in any non-inherited permissions that are copied. The option can be specified multiple times
to provide different mappings.
* Thanks to Kevin Sanghvi for suggesting this enhancement.

Updated `gam <UserTypeEntity> delete othercontacts` to retry the delete step when
`notFound` errors are returned after the update step.

Fixed bug in `gam courses <CourseEntity> add|remove students|teachers` that caused API
call retries to fail with the following error:
```
Temporary error: notFound - @CourseNotFound The course was not found.
```

Improved performance when converting Shared Drive names to IDs.

Updated code to handle Shared Drive names that contain single quotes.

### 6.14.07

Corrected `gam.cfg` variable `cmdlog_max__backups` to be `cmdlog_max_backups`.

### 6.14.06

Fixed bug in `gam sync devices` where option `serialnumber_column` was not recognized.

Fixed bug in `gam sync devices` where a trap occurred when option `assigned_missing_action` was not specified.

### 6.14.05

Upgraded the `countsonly` suboption `showsource` in `gam <UserTypeEntity> print filelist` to display
the name of the source drive/folder (Name column) in addition to its ID (Source Column).

### 6.14.04

Added a command to move Other Contacts to My Contacts.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-People-Contacts-Profiles#move-user-other-contacts
```
gam <UserTypeEntity> move othercontacts <OtherContactResourceNameEntity>|<OtherContactSelection>
```

Improved action performed messages in `gam <UserTypeEntity> update othercontacts`.

### 6.14.03

Added a command to delete Other Contacts.
* Thanks to Kim Nilsson for finding a Stack Overflow page that showed the way to do this.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-People-Contacts-Profiles#delete-user-other-contacts
```
gam <UserTypeEntity> delete othercontacts <PeopleResourceNameEntity>|<PeopleUserOtherContactSelection>
```

Added a command to update Other Contacts and move them to My Contacts.
* Thanks to Kim Nilsson for finding a Stack Overflow page that showed the way to do this.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-People-Contacts-Profiles#update-user-other-contacts
```
gam <UserTypeEntity> update othercontacts <PeopleResourceNameEntity>|<PeopleUserOtherContactSelection>
        <PeopleContactAttribute>+
        (contactgroup <ContactGroupItem>)*
```

### 6.14.02

Updated `gam print|show teamdriveacls` to display the creation time of the Team/Shared drives.

### 6.14.01

Added the option `excludepermissionsfromdomains <DomainNameList>` to `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>`
that excludes permissions that reference any domain in `<DomainNameList>` from being copied.
* Thanks to Kevin Sanghvi for suggesting this enhancement.

Fixed bug `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>` where option `copymergewithparentfolderpermissions`
was not recognized.

### 6.14.00

Added the following options to `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>`
that provide more flexibility in managing permissions when copying/moving folders.
Thanks to Kevin Sanghvi for suggesting these enhancements.
```
copyfileinheritedpermissions [<Boolean>]
copyfilenoninheritedpermissions [<Boolean>]
copymergewithparentfolderpermissions [<Boolean>]
copymergedtopfolderpermissions [<Boolean>]
copytopfolderinheritedpermissions [<Boolean>]
copytopfoldernoninheritedpermissions never|always|syncallfolders|syncupdatedfolders
copymergedsubfolderpermissions [<Boolean>]
copysubfolderinheritedpermissions [<Boolean>]
copysubfoldernoninheritedpermissions never|always|syncallfolders|syncupdatedfolders
```
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Copy-Move#copy-permissions
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Drive-Copy-Move#move-permissions

Following Jay's lead, added command `gam <UserTypeEntity> show vaultholds` to display all vault holds
affecting a user. This allows you to investigate the error `Delete Failed: Precondition is not met.`
when trying to delete a user.

Added option `buildpath [<Boolean>]` to `gam <UserTypeEntity> create filter label <LabelName>` that controls whether
`<LabelNames>` of the form `Top/Middle/Bottom` will be created as single-level or multi-level.

Added option `hidden <Boolean>' to `gam <UserTypeEntity> update teamdrive`.

Fixed bug in `gam print|show matters matterstate <MatterStateList>` that caused a trap.

Fixed bug in `gam update mobile <MobileEntity> action block` that caused the following error:
```
ERROR: 400: invalidInput - Invalid value for: action_block is not a valid value
```

* Upgraded to Python 3.10.2
* Updated google-api-python-client to version 2.35.0

### 6.13.09

Fixed bug in `gam <UserTypeEntity> update chromepolicy` that caused a trap.

Fixed bug in `gam print|show datatransfers oldowner|newowner <UserItem>` that did not
properly handle `<UserItem>` of form `uid:<String>`.

### 6.13.08

* Updated to OpenSSL 1.1.1m

Added command `gam info currentprojectid` that displays the current Project ID.

### 6.13.07

Added options `showpermissionmessages` and `sendemailifrequired` to `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity>`.
Previously, when attempting to copy ACLs, GAM would report any errors; some errors were generated when an attempt
was made to inappropriately copy an ACL. Now, GAM will not attempt to copy ACLs unless they are appropriate.
When `showpermissionmessages` is specified GAM will display messages about ACLs not copied, ACLs that were copied
and any remaining copy errors.

When copying an ACL that references a non Google account, an error is generated unless an email is sent to the account;
by default, no email notifications are sent. The `sendemailifrequired` options instructs GAM to send an email notification in this case.

### 6.13.06

Added option `formatjson` to `gam <UserTypeEntity> info filters` and `gam <UserTypeEntity> show filters`.

### 6.13.05

Handle the following error in `gam <UserTypeEntity> signout`:
```
ERROR: 400: invalidInput - Invalid Input
```
This can be caused by applying the command to a suspended user.

### 6.13.04

Added option `showsize` to `gam <UserTypeEntity> print|show filecounts` that displays the
size (in bytes) of the files counted.

Following Jay's lead, added commands to display ChromeOS device telemetry data.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/ChromeOS-Devices#display-chromeos-telemetry-data

To use these commands  you must authorize an additional scope:
* `Chrome Management API - Telemetry read only`
```
gam oauth create
```

Added option `reverselists <ListFieldNameList>` to commands that display ChromeOS device information.
For each list in `<ListFieldNameList>`, the list order is changed from ascending (oldest to newest) to descending (newest to oldest);
this makes it easy to get the `N` most recent values with `listlimit N reverselists <ListFieldNameList>`.

### 6.13.03

Added options `parentselector <OrgUnitSelector>` and `childselector <OrgUnitSelector>` to
`gam print orgs|ous` that add an additional column `orgUnitSelector` to the output. This column
value can be used in subsequent `gam csv` commands to appropriately select members without duplication.
```
<OrgUnitSelector> ::=
        cros_ou | cros_ou_and_children|
        ou| ou_ns | ou_susp|
        ou_and_children | ou_and_children_ns | ou_and_children_susp

Get file count summariess by OU; top level selector is ou, sub level selectors are ou_and_children

gam redirect csv ./TopLevelOUs.csv print ous showparent toplevelonly parentselector ou childselector ou_and_children fields orgunitpath
gam redirect csv ./FileCounts.csv multiprocess csv ./TopLevelOUs.csv gam "~orgUnitSelector" "~orgUnitPath" print filecounts excludetrashed summary only summaryuser "~orgUnitPath"
```

### 6.13.02

Updated error handling in `gam <UserTypeEntity> copy drivefile` when copying files to a shared drive folder.

### 6.13.01

Added option `summaryuser <String>` to `gam <UserTypeEntity> print filecounts` and
`gam <UserTypeEntity> print filelist countsonly` that replaces the default summary user `Summary`
with `<String>`.
```
gam redirect csv ./FileCounts.csv multiprocess csv ./OUs.csv gam ou_ns "~orgUnitPath" print filecounts excludetrashed summary only summaryuser "~orgUnitPath"
```

Uodated `gam <UserTypeEntity> update drivefile <DriveFileEntity> teamdriveparentid <DriveFolderID>
to handle the following error:
```
ERROR: 400: shareOutNotPermitted - Bad Request. User message: "shareOutNotPermitted"
```

### 6.13.00

Fixed bug in `gam <UserTypeEntity> copy drivefile` where `contentManager|fileOrganizer` ACLs
were not copied from a source shared drive folder to a target shared drive folder.

### 6.12.06

Fixed bug where `redirect csv - multiprocess todrive redirect stdout - multiprocess` would disable
`multiprocess` for `redirect csv` which resulted in multiple files being uploaded.

Added option `showshareddrivepermissions` to `gam <UserTypeEntity> show fileinfo <DriveFileEntity>` that is applicable
when no fields are selected and `<DriveFileEntity>` is a shared drive file/folder. In this case,
the Drive API returns the permission IDs but not the permissions themselves so GAM makes an additional API call
to get the permissions.

Added option `showshareddrivepermissions` to `gam <UserTypeEntity> print filelist` that is applicable
when no fields are selected and shared drives are queried/selected. In this case,
the Drive API returns the permission IDs but not the permissions themselves so GAM makes an additional API call
per file to get the permissions.

Added commands that can process lists of Gmail labels.
* See: https://github.com/taers232c/GAMADV-XTD3/wiki/Users-Gmail-Labels

### 6.12.05

Updated `gam info|print cros showdvrsfp formatjson` to include `diskVolumeReports.volumeInfo.storageFreePercentage`.

Improved error messages for `gam create resource` when options `capacity <Number>` and `floor <String>`
are required but not provided.

### 6.12.04

Added option `showdvrsfp` to `gam info|print cros` that causes GAM to display a field
`diskVolumeReports.volumeInfo.storageFreePercentage` which is calculated as:
* `(diskVolumeReports.volumeInfo.storageFree/diskVolumeReports.volumeInfo.storageTotal)*100`

You can use an output row filter to only show ChromeOS devices with a limited amount of free space:
* `config csv_output_row_filter "diskVolumeReports.volumeInfo.0.storageFreePercentage:countrange=1/15"`
Use `countrange=1/15` instead of `count<15` as the latter will display ChromeOS devices with no
diskVolumeReports; a blank entry is treated as a zero.

ChromeOS devices can have multiple diskVolumeReports; some experimentation may be required to
get the desired results.

### 6.12.03

The 6.12.02 bug fix in `gam <UserTypeEntity> print|show filetree select <DriveFileEntity>`
was too aggressive; when showing a file tree, folders owned by others must be processed
so that files owned by the user within those folders are displayed.

### 6.12.02

When running `gam oauth create` and `gam.cfg no_browser = true`, the authorization link is
no longer copied to the file `gamoauthurl.txt` as this functionality required modifying
a Google supplied library.

Removed the option `writeurltofile` from `gam check| svcacct` that caused GAM to write
the authorization link to the file `gamsvcaccturl.txt`.

Fixed bug in `gam <UserTypeEntity> print|show filetree select <DriveFileEntity>` where
file ownership was not being checked which resulted in files not owned by the user being displayed.

### 6.12.01

Updated code to perform retries when a `serviceNotAvailable` error occurs when listing file permissions.

### 6.12.00

Fixed bug in `gam <UserTypeEntity> copy drivefile <DriveFileEntity> <DriveFileParentAttribute> recursive`
that mis-copied files when the target parent folder `<DriveFileParentAttribute>` was within the folder structure of `<DriveFileEntity>`.

Fixed bug in `gam <UserTypeEntity> check drivefileshortcut <DriveFileEntity> csv` that caused a trap.

### 6.11.07

Added command `gam <UserTypeEntity> delete labelid <LabelID>` that is used to 
delete Gmail labels by ID rather than by name.

### 6.11.06

Fixed bug in 6.11.05 for updating Chromebook OU by ID.

### 6.11.05

Added `update_cros_ou_with_id` variable to `gam.cfg` that causes GAM to update
the OU of a Chromebook with the OU ID rather than the OU path.
Set this value to true if you are getting the following error:
```
400: invalidInput - Invalid Input: Inconsistent Orgunit id and path in request
```

### 6.11.04

When specifying `<UserAttribute> languages`, it is an error to specify a custom language with a preference suffix `+-`.

Added option `includederivedmembership` to `gam print|show cigroup-members`.
This option causes the API to list indirect members of groups.
See: https://github.com/taers232c/GAMADV-XTD3/wiki/Cloud-Identity-Groups-Membership

Updated `gam oauth export|refresh` to privent the following error.
```
ERROR: Authentication Token Error - Not all requested scopes were granted by the authorization server, missing scopes , https://sitesgooglecom/feeds, https://wwwgooglecom/m8/feeds
```

### 6.11.03

Added option `noinvitablecheck` to `gam whatis <EmailItem>` that suppresses the user invitation check
to avoid exceeding quota limits when checking a large number of addresses.

Following Jay's lead, updated processing of `<UserAttribute> languages`.
You could always set a user's languages via the API; Google has added the ability to
indicate whether a language is `preferred` or `not_preferred`. This is implemeted in
GAM by optionally appending a `+` to a language code to set `preferred` and a '-' to set `not_preferred`.
In the user's profile, only `preferred` languages are displayed.
```
gam update user user@domain.com languages en+,fr+.
```

Updated all Cloud Identity API group calls to use version `v1` of the API rather than version `v1beta1`.

### 6.11.02

Added option `nobatchupdate` to `gam <CrOSTypeEntity> update ou <OrgUnitPath>` and
`gam update cros <CrOSEntity> ou <OrgUnitPath>` that prevents GAM from using batch mode
to update the devices; this allows handling the `rateLimitExceeded` error described below.

### 6.11.01

Updated code to to handle the following error as retryable:
```
403: rateLimitExceeded - Quota exceeded for quota metric 'Queries' and limit 'Queries per minute per user' of service 'admin.googleapis.com' for consumer 'project_number: (project)'
```

### 6.11.00

Updated `gam print groups` and `gam print|show group-members` to allow identification of groups
with the `All users in the organization` member with: `member id:<CustomerID>`.

Upgraded to Python 3.10.1

### 6.10.05

Added option to the `copyfrom` option used with `gam create/update course` that modifies how
course work and materials are copied.
* `markdraftaspublished` - Mark all draft course work and materials as published

Updated `todrive` options to simplify updating an existing sheet within an existing file.
Previously, if you specified `tdfileid <DriveFileID> tdsheet (id:<Number>)|<String> tdupdatesheet`,
the sheet had to exist. The updated behavior is:
* `tdfileid <DriveFileID> tdsheet id:<Number> tdupdatesheet` - The specified sheet must exist
* `tdfileid <DriveFileID> tdsheet <String> tdupdatesheet` - The specified sheet will be created if necessary

### 6.10.04

Fixed bug introduced in 6.10.03 that broke `gam <UserTypeEntity> update drivefileacl <DriveFileEntity>`.

Updated `gam whatis <EmailItem>` to give a better message if `<EmailItem>` is not a group/user email address
or alias and Service Account scope `Cloud Identity User Invitations API` is not enabled.

Renamed client access scope `Directory API Printers` to `Chrome Printer Management API`; there is
no change in functionality.

### 6.10.03

Updated `gam <UserTypeEntity> copy|move drivefile <DriveFileEntity> <DriveFileParentAttribute>`
to enforce the requirement that the specified user be a Shared Drive organizer
if either `<DriveFileEntity>` or `<DriveFileParentAttribute>` specifies a Shared Drive.

Added options `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` to
`gam <UserTypeEntity> create|update drivefileacl <DriveFileEntity>` that causes GAM to
output the new ACL details in CSV form rather than indented keywords and values.

### 6.10.02

Following Jay's lead, fixed obscure problem when creating a project in timezones ahead of GMT.

### 6.10.01

Updated `gam create domainalias|aliasdomain <DomainAlias> <DomainName>` to handle error when
an invalid `<DomainAlias>` is specified.

### 6.10.00

Added `csv_output_subfield_delimiter` and `people_max_results` variables to `gam.cfg`.
```
csv_output_subfield_delimiter
    Character used to delimit fields and subfields in headers when writing CSV files;
    this must be a single character
    Default: '.'

people_max_results
    When retrieving lists of People from API,
    how many should be retrieved in each API call
    Default: 100
    Range: 0 - 1000
```
