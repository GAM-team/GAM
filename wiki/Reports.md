# Reports
- [API documentation](#api-documentation)
- [Collections of Users](Collections-of-Users)
- [Definitions](#definitions)
- [Special quoting](#special-quoting)
- [Activity reports](#activity-reports)
  - [Find Shared Drives with no activity](#find-shared-drives-with-no-activity)
- [Customer and user reports parameters](#customer-and-user-reports-parameters)
- [Customer usage reports](#customer-usage-reports)
- [Customer reports](#customer-reports)
- [User usage reports](#user-usage-reports)
- [User reports](#user-reports)

## API documentation
* [Reports API - Activities](https://developers.google.com/admin-sdk/reports/v1/reference/activities)
* [Reports API - Customer Usage](https://developers.google.com/admin-sdk/reports/v1/reference/customerUsageReports)
* [Reports API - User Usage](https://developers.google.com/admin-sdk/reports/v1/reference/userUsageReport)

## Definitions
```
<DayOfWeek> ::= mon|tue|wed|thu|fri|sat|sun
<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
```
## Special quoting
If you are going to use `config csv_output_row_filter` when printing reports,
you'll need special quoting in the filter because of the `:` characters in the parameter names.

See: https://github.com/GAM-team/GAM/wiki/CSV-Output-Filtering#quoting-rules

For example:
```
config csv_output_row_filter "'\"accounts:used_quota_in_mb\":count>15000'"
```

## Activity reports
```
<ActivityApplicationName> ::=
        access|accesstransparency|
        admin|
        calendar|calendars|
        chat|
        chrome|
        classroom|
        contextawareaccess|
        currents|gplus|google+|
        datastudio|
        devices|mobile|
        domain|
        drive|doc|docs|
        gcp|cloud|
        gemini|geminiforworkspace|
        groups|group|
        groupsenterprise|enterprisegroups|
        jamboard|
        keep|
        login|logins|
        meet|hangoutsmeet|
        mobile|devices|
        rules|
        saml|
        token|tokens|oauthtoken|
        useraccounts|
        vault

gam report <ActivityApplicationName> [todrive <ToDriveAttribute>*]
        [(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
        [([start <Time>] [end <Time>])|(range <Time> <Time>)|
         yesterday|today|thismonth|(previousmonths <Integer>)]
        [filtertime<String> <Time>] [filter|filters <String>]
        [event|events <EventNameList>] [ip <String>]
        [groupidfilter <String>]
        [maxactivities <Number>] [maxevents <Number>] [maxresults <Number>]
        [countsonly [bydate|summary] [eventrowfilter]]
        (addcsvdata <FieldName> <String>)* [shownoactivities]
```
Select the application with `<ActivityApplicationName>`.

For all `<ActivityApplicationNames>` other than `admin`, select the users for whom information is desired.
* `user all` - All users, the default; there is one API call
* `user <UserItem>` - An individual user; there is one API call
* `orgunit|org|ou <OrgUnitPath>` - All users in the specified OU; there is one API call
  * `showorgunit` - Add a column labelled `actor.orgUnitPath` to the output; an additional API call is made to get the email addresses of the users in `<OrgUnitPath>`
* `select <UserTypeEntity>` - A selected collection of users, e.g., `select group staff@domain.com`; there is one API call per user

For `<ActivityApplicationName>` `admin`, the users selected are the admins that executed the command, not the targeted user.
Use `filter "USER_EMAIL==user@domain.com"` to select the targeted user.

Limit the time period.
* `start <Time>`
* `end <Time>`
* `range <Time> <Time>` - Equivalent to `start <Time> end <Time>`
* `yesterday` - Yesterday
* `today` - Today
* `thismonth` - The current calendar month up to the current time
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month

Apply API filters.
* `filter|filters <String>` - `<String>` is a comma separated list of filter expressions.

Use the `filtertime<String> <Time>` option to allow times, usually relative, to be substituted into the `filters` option.
The `filtertime<String> <Time>` value replaces the string `#filtertime<String>#` in any filters..
The characters following `filtertime` can be any combination of lowercase letters and numbers. This is most useful in scripts
where you can specify a relative date without having to change the script.

You can use `config csv_output_row_filter` to filter the events if the API filter can't produce the results you want.

Limit to a list of specific events.
* `event|events <EventNameList>`

Limit to a specific IP address.
* `ip <String>`

Limit to those users that are a member of at least one of a list of groups.
* `groupidfilter <String>` - Format: "id:abc123,id:xyz456"

Limit the total number of activites.
* `maxactivities <Number>`

Limit the  number of events per activity; this only applies when `countsonly` is False.
* `maxevents <Number>`

Limit the number of activities downloaded per API call; infrequently used.
* `maxresults <Number>`

Setting options `maxactivities 1 maxevents 1 maxresults 1` can be used to as efficiently as possible
show the most recent activity/event; this can be useful when reporting drive activity for individual drive files.

Add additional columns of data from the command line to the output.
* `addcsvdata <FieldName> <String>`

Display a row with a key value of `NoActivities` when there are no activities to report.
* `shownoactivities`

By default, individual event details are displayed, these options modify what's displayed.
* `countsonly` - Display a row per user across all dates with all event counts on one row
* `countsonly bydate` - Display a row per user per date for all dates with any events with all events counts on the row
* `countsonly summary` - Display a row per event with counts for each event summarized across users and dates
* `countsonly [bydate|summary] eventrowfilter` - Apply `config csv_output_row_filter` to the event details rather than the event counts

### Example
You're interested in files with extension `xyz` created yesterday.

Details for each file
```
gam config csv_output_row_filter "doc_title:regex:\.xyz" report drive event create yesterday
```
Number of files by each user
```
gam config csv_output_row_filter "doc_title:regex:\.xyz" report drive event create yesterday countsonly eventrowfilter
```
Number of files summarized across all users
```
gam config csv_output_row_filter "doc_title:regex:\.xyz" report drive event create yesterday countsonly summary eventrowfilter
```
## Find Shared Drives with no activity

Remember that activity events are only available for the past 180 days.

Get Shared Drives ID and Name
```
gam redirect csv ./SharedDrives.csv print shareddrives fields id,name
```

Options for the `gam report drive` commands below:
* `maxactivities 1` - Limits the number of activities displayed for Shared Drives with activity.
* `shownoactivities` - Displays a row for Shared Drives with no activity.
* `addcsvdata shared_drive_id "~id"` adds the Shared Drive ID to the output.
* `addcsvdata shared_drive_name "~name"` adds the Shared Drive name to the output.

Get activities with minimal activty data.
```
gam config csv_output_header_filter "name,id.time,shared_drive_id,shared_drive_name" redirect csv ./SharedDrivesActivity.csv multiprocess redirect stderr - multiprocess csv SharedDrives.csv gam report drive filter "shared_drive_id==~~id~~" maxactivities 1 shownoactivities addcsvdata shared_drive_id "~id" addcsvdata shared_drive_name "~name"

Example output from SharedDrivesActivity.csv:

name,id.time,shared_drive_id,shared_drive_name
NoActivities,,0AERPpMc23znvUkPXYZ,Shared Drive 1
view,2023-10-18T21:27:51-07:00,0AMhgLk82dhsuUkPXYZ,Shared Drive 2
edit,2023-09-05T15:27:01-07:00,0AM8lpdkkJaKYUkPXYZ,Shared Drive 3
```

Get activities with full activty data.
```
gam redirect csv ./SharedDrivesActivity.csv multiprocess redirect stderr - multiprocess csv SharedDrives.csv gam report drive filter "shared_drive_id==~~id~~" maxactivities 1 shownoactivities addcsvdata shared_drive_id "~id" addcsvdata shared_drive_name "~name"

Example output from SharedDrivesActivity.csv:

name,actor.callerType,actor.email,actor.key,actor.profileId,actor_is_collaborator_account,added_role,billable,destination_folder_id,destination_folder_title,doc_id,doc_title,doc_type,id.applicationName,id.customerId,id.time,id.uniqueQualifier,ipAddress,is_encrypted,membership_change_type,new_settings_state,old_settings_state,originating_app_id,owner,owner_is_shared_drive,owner_is_team_drive,owner_team_drive_id,primary_event,removed_role,shared_drive_id,shared_drive_name,shared_drive_settings_change_type,target,team_drive_id,team_drive_settings_change_type,type,visibility
NoActivities,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0AERPpMc23znvUkPXYZ,Shared Drive 1,,,,,,
view,,user1@domain.com,,100016760394505151666,False,,True,,,1SDNu-yzDapqjdJq4y4xKDUATJlOPRIBodpGGeGt1n4I,Digital Poetry Journal,document,drive,C03kt1z99,2023-10-18T21:27:51-07:00,-2856812962461786835,2600:1700:9580:f4b0:2127:3b2:dd21:3806,False,,,,263492796725,Shared Drive 2,True,True,0AMhgLk82dhsuUkPXYZ,True,,0AMhgLk82dhsuUkPXYZ,Shared Drive 2,,,0AMhgLk82dhsuUkPXYZ,,access,people_with_link
edit,,user2@domain.com,,104066776037911136666,False,,True,,,1ZwHi_v-JVXH8W6zwgb7QYoUHrZD6NzIshJEqoTCaDD0,High School Scavenger Hunt,form,drive,C03kt1z99,2023-09-05T15:27:01-07:00,-1272095408714453395,50.204.178.246,False,,,,,Shared Drive 3,True,True,0AM8lpdkkJaKYUkPXYZ,True,,0AM8lpdkkJaKYUkPXYZ,Shared Drive 3,,,0AM8lpdkkJaKYUkPXYZ,,access,shared_internally
```

## Customer and user reports parameters
Display the valid parameters for customer and user reports.
```
gam report usageparameters customer|user [todrive <ToDriveAttribute>*]
```
## Customer usage reports
Display customer usage data over a date range.
```
gam report usage customer [todrive <ToDriveAttribute>*]
        [([start|startdate <Date>] [end|enddate <Date>])|(range <Date> <Date>)|
         thismonth|(previousmonths <Integer>)]
        [skipdates <Date>[:<Date>](,<Date>[:<Date>])*] [skipdaysofweek <DayOfWeek>(,<DayOfWeek>)*]
        [fields|parameters <String>]
        [convertmbtogb]
```
Limit the time period.
* `start <Date>` - Default value is 30 days prior to `end <Date>`
* `end <Date>` - Default value is today
* `range <Date> <Date>` - Equivalent to `start <Date> end <Date>`
* `thismonth` - The current calendar month up to the current time
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month

Option `convertmbtogb` causes GAM to convert parameters expressed in megabytes
(name ends with _in_mb) to gigabytes (name converted to _in_gb) with two decimal places.

### Example
Jay provided this example.
```
gam report usage customer parameters meet:total_call_minutes,meet:total_meeting_minutes start_date 2020-03-01 skipdaysofweek sat,sun todrive 
```
A bit about this command
* call minutes = 1 device joined to a meeting
  * 5 users on a 10 minute meeting = 50 call minutes
  * 2 users on 5 minute call = 10 call minutes
* meeting minutes = length of actual meeting
  * 2 users on 10 minute meeting = 10 meeting minutes
  * 10 users on 10 minute meeting = 10 meeting minutes.
I excluded weekend days when the organization was closed to avoid dramatic "camel humps" in the data.

Open the Sheet and click Insert > Chart

## Customer reports
Customer reports are generally available up to two days before the current date.
```
<CustomerServiceName> ::=
        accounts|
        app_maker|
        apps_scripts|
        calendar|
        chat|
        classroom|
        cros|
        device_management|
        docs|
        drive|
        gmail|
        gplus|
        meet|
        sites
<CustomerServiceNameList> ::= "<CustomerServiceName>(,<CustomerServiceName>)*"

gam report customers|customer|domain [todrive <ToDriveAttribute>*]
        [(date <Date>)|(range <Date> <Date>)|
         yesterday|today|thismonth|(previousmonths <Integer>)]
        [(nodatechange | limitdatechanges <Integer>) | (fulldatarequired all|<CustomerServiceNameList>)]
        [(fields|parameters <String>)|(services <CustomerServiceNameList>)]
        [noauthorizedapps]
        [convertmbtogb]
```
Specify the report date; the default is today's date.
* `date <Date>` - A single date; there is one API call
* `range <Date> <Date>` - A range of dates; there is an API call per date
* `yesterday` - Yesterday; there is one API call
* `today` - Today; there is one API call
* `thismonth` - The current calendar month up to the current time; there is an API call per date
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month; there is an API call per date

Option `convertmbtogb` causes GAM to convert parameters expressed in megabytes
(name ends with _in_mb) to gigabytes (name converted to _in_gb) with two decimal places.

If no report is available for the specified date, can an earlier date be used?
* `limitdatechanges -1' - Back up to earlier dates to find report data; this is the default.
* `limitdatechanges 0 | nodatechange' - Do not report on an earlier date if no report data is available for the specified date.
* `limitdatechanges N' - Back up to earlier dates to find report data; do not back up more than N times.

If only partial report data is available for the specified date and applications, can an earlier date be used?
* `fulldatarequired all` - Back up to an earlier date to get complete data until all applications have full report data
* `fulldatarequired <UserServiceNameList>` - Back up to an earlier date to get complete data until all applications in `<UserServiceNameList>` have full report data

By default, all parameters for all services are displayed, you can select to display fewer parameters.
* `fields|parameters <String>` - A list of service parameters separated by commas
* `services <CustomerServiceNameList>` - All parameters for a list of services
* `noauthorizedapps` - Do not display the `authorized_apps` parameter for the `accounts` service

When no date is specified or `date <Date>` is specified, the data is output in three columns: `date,name,value`.
`name` is the parameter name and `value` is its value. This format is useful for human reading but as useful for manipulating in a spreadsheet.

When `range <Date> <Date>` is specified, the data is output in multiple columns: `date,name1,name2,name3...`.
This format is useful for manipulating in a spreadsheet.

### Examples
Display Gmail traffic for a single day.
```
$ gam report customer parameters gmail:num_emails_sent,gmail:num_emails_received date -2d
date,name,value
2019-03-01,gmail:num_emails_received,4009
2019-03-01,gmail:num_emails_sent,618
$ gam report customer parameters gmail:num_emails_sent,gmail:num_emails_received range -2d -2d
date,gmail:num_emails_received,gmail:num_emails_sent
2019-03-01,4009,618
```
Display Gmail traffic for the last week.
```
$ gam report customer parameters gmail:num_emails_sent,gmail:num_emails_received range -8d -2d
date,gmail:num_emails_received,gmail:num_emails_sent
2019-02-23,772,92
2019-02-24,1015,112
2019-02-25,4544,800
2019-02-26,5429,803
2019-02-27,5232,951
2019-02-28,4691,766
2019-03-01,4009,618
```
## User usage reports
Display user usage data over a date range.
```
gam report usage user [todrive]
        [(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
        [([start|startdate <Date>] [end|enddate <Date>])|(range <Date> <Date>)|
         thismonth|(previousmonths <Integer>)]
        [skipdates <Date>[:<Date>](,<Date>[:<Date>])*] [skipdaysofweek <DayOfWeek>(,<DayOfWeek>)*]
        [fields|parameters <String>]
        [convertmbtogb]
```
Select the users for whom information is desired.
* `user all` - All users, the default; there is one API call
* `user <UserItem>` - An individual user; there is one API call
* `orgunit|org|ou <OrgUnitPath>` - All users in the specified OU; there is one API call
  * `showorgunit` - Add a column labelled `orgUnitPath` to the output; an additional API call is made to get the email addresses of the users in `<OrgUnitPath>`
* `select <UserTypeEntity>` - A selected collection of users, e.g., `select group staff@domain.com`; there is one API call per user

Limit the time period.
* `start <Date>` - Default value is 30 days prior to `end <Date>`
* `end <Date>` - Default value is today
* `range <Date> <Date>` - Equivalent to `start <Date> end <Date>`
* `thismonth` - The current calendar month up to the current time
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month

Option `convertmbtogb` causes GAM to convert parameters expressed in megabytes
(name ends with _in_mb) to gigabytes (name converted to _in_gb) with two decimal places.

## User reports
User reports are generally available up to four days before the current date.
```
<UserServiceName> ::=
        accounts|
        chat|
        classroom|
        docs|
        drive|
        gmail|
        gplus
<UserServiceNameList> ::= "<UserServiceName>(,<UserServiceName>)*"

gam report users|user [todrive <ToDriveAttribute>*]
        [(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
        [allverifyuser <UserItem>]
        [(date <Date>)|(range <Date> <Date>)|
         yesterday|today|thismonth|(previousmonths <Integer>)]
        [(nodatechange | limitdatechanges <Integer>) | (fulldatarequired all|<UserServiceNameList>)]
        [filtertime<String> <Time>] [filter|filters <String>]
        [(fields|parameters <String>)|(services <UserServiceNameList>)]
        [aggregatebydate|aggregatebyuser [Boolean]]
        [maxresults <Number>]
        [convertmbtogb]
```
Select the users for whom information is desired.
* `user all` - All users, the default; there is one API call
* `user <UserItem>` - An individual user; there is one API call
* `orgunit|org|ou <OrgUnitPath>` - All users in the specified OU; there is one API call
  * `showorgunit` - Add a column labelled `orgUnitPath` to the output; an additional API call is made to get the email addresses of the users in `<OrgUnitPath>`
* `select <UserTypeEntity>` - A selected collection of users, e.g., `select group staff@domain.com`; there is one API call per user

By default, when `user all` is specified (or no user specification in supplied), GAM backs up looking for data with a (basically) random user. If the randaom
doesn't have any data, the command reports that no data was found. Use `allverifyuser <UserItem>` to specify a specific user to use to search for data.

Specify the report date; the default is today's date.
* `date <Date>` - A single date; there is one API call
* `range <Date> <Date>` - A range of dates; there is an API call per date
* `yesterday` - Yesterday; there is one API call
* `today` - Today; there is one API call
* `thismonth` - The current calendar month up to the current time; there is an API call per date
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month; there is an API call per date

Option `convertmbtogb` causes GAM to convert parameters expressed in megabytes
(name ends with _in_mb) to gigabytes (name converted to _in_gb) with two decimal places.

If no report is available for the specified date, can an earlier date be used?
* `limitdatechanges -1' - Back up to earlier dates to find report data; this is the default.
* `limitdatechanges 0 | nodatechange' - Do not report on an earlier date if no report data is available for the specified date.
* `limitdatechanges N' - Back up to earlier dates to find report data; do not back up more than N times.

If only partial report data is available for the specified date and applications, can an earlier date be used?
* `fulldatarequired all` - Back up to an earlier date to get complete data until all applications have full report data
* `fulldatarequired <UserServiceNameList>` - Back up to an earlier date to get complete data until all applications in `<UserServiceNameList>` have full report data

By default, when `user <UserItem>` is specified and no report data is available, there is no output.
If `csv_output_users_audit = true` in `gam.cfg`, then a row with columns `email,date` will be displayed
where `date` is the earliest date for which report data was requested.

Apply filters.
* `filter|filters <String>` - `<String>` is a comma separated list of filter expressions.

Use the `filtertime<String> <Time>` option to allow times, usually relative, to be substituted into the `filters` option.
The `filtertime<String> <Time>` value replaces the string `#filtertime<String>#` in any filters..
The characters following `filtertime` can be any combination of lowercase letters and numbers. This is most useful in scripts
where you can specify a relative date without having to change the script.

For example, filter for last logins more that 60 days ago.
```
filtertime60d -60d filters "accounts:last_login_time<#filtertime60d#"
```

Select the fields/parameters to display.
* `fields|parameters <String>` - A list of parameters separated by commas
* `services <UserServiceNameList>` - All parameters for a list of services

Select data format.
* `aggregatebydate|aggregatebyuser` is omitted or <Boolean> is False, there is one row of data per user per date.
* `aggregatebydate` is present and <Boolean> is omitted or is True, the data is aggregated by date for all users so that there is one row per date.
* `aggregatebyuser` is present and <Boolean> is omitted or is True, the data is aggregated by user for all dates so that there is one row per user.

Limit the number of activities downloaded per API call; infrequently used.
* `maxresults <Number>`

### Examples

Report on the users that haven't logged in in the last 5 years.
```
gam report users parameters accounts:last_login_time filters "accounts:last_login_time<#filtertime5y#" filtertime5y -5y
```
Report on the users that haven't ever logged in.
```
gam report users parameters accounts:last_login_time filters "accounts:last_login_time==#filtertimenever#" filtertimenever never
```
Report on users Google Drive usage.
```
gam report users parameters accounts:drive_used_quota_in_mb,accounts:total_quota_in_mb,accounts:used_quota_in_mb,accounts:used_quota_in_percentage
```
Report on users total storage usage.
```
gam report users parameters accounts:drive_used_quota_in_mb,accounts:gmail_used_quota_in_mb,accounts:gplus_photos_used_quota_in_mb,accounts:total_quota_in_mb,accounts:used_quota_in_mb,accounts:used_quota_in_percentage
```
Report on email activity for individual users.
```
$ gam report users select users testuser1,testuser2,testuser3 fields gmail:num_emails_received,gmail:num_emails_sent range 2023-07-01 2023-07-07 
Getting Reports for testuser1@rdschool.org (1/3)
Got 1 Report for testuser1@domain.com on 2023-07-01...
Got 1 Report for testuser1@domain.com on 2023-07-02...
Got 1 Report for testuser1@domain.com on 2023-07-03...
Got 1 Report for testuser1@domain.com on 2023-07-04...
Got 1 Report for testuser1@domain.com on 2023-07-05...
Got 1 Report for testuser1@domain.com on 2023-07-06...
Got 1 Report for testuser1@domain.com on 2023-07-07...
Getting Reports for testuser2@domain.com (2/3)
Got 1 Report for testuser2@domain.com on 2023-07-01...
Got 1 Report for testuser2@domain.com on 2023-07-02...
Got 1 Report for testuser2@domain.com on 2023-07-03...
Got 1 Report for testuser2@domain.com on 2023-07-04...
Got 1 Report for testuser2@domain.com on 2023-07-05...
Got 1 Report for testuser2@domain.com on 2023-07-06...
Got 1 Report for testuser2@domain.com on 2023-07-07...
Getting Reports for testuser3@domain.com (3/3)
Got 1 Report for testuser3@domain.com on 2023-07-01...
Got 1 Report for testuser3@domain.com on 2023-07-02...
Got 1 Report for testuser3@domain.com on 2023-07-03...
Got 1 Report for testuser3@domain.com on 2023-07-04...
Got 1 Report for testuser3@domain.com on 2023-07-05...
Got 1 Report for testuser3@domain.com on 2023-07-06...
Got 1 Report for testuser3@domain.com on 2023-07-07...
email,date,gmail:num_emails_received,gmail:num_emails_sent
testuser1@domain.com,2023-07-01,10,1
testuser1@domain.com,2023-07-02,5,1
testuser1@domain.com,2023-07-03,14,3
testuser1@domain.com,2023-07-04,3,0
testuser1@domain.com,2023-07-05,35,4
testuser1@domain.com,2023-07-06,30,2
testuser1@domain.com,2023-07-07,20,0
testuser2@domain.com,2023-07-01,3,1
testuser2@domain.com,2023-07-02,1,0
testuser2@domain.com,2023-07-03,4,0
testuser2@domain.com,2023-07-04,1,0
testuser2@domain.com,2023-07-05,15,0
testuser2@domain.com,2023-07-06,14,0
testuser2@domain.com,2023-07-07,9,1
testuser3@domain.com,2023-07-01,14,0
testuser3@domain.com,2023-07-02,14,0
testuser3@domain.com,2023-07-03,20,0
testuser3@domain.com,2023-07-04,12,0
testuser3@domain.com,2023-07-05,37,2
testuser3@domain.com,2023-07-06,42,0
testuser3@domain.com,2023-07-07,20,0
```
Report on email activity for individual users, aggregate by date across users.
```
$ gam report users select users testuser1,testuser2,testuser3@domain.com fields gmail:num_emails_received,gmail:num_emails_sent range 2023-07-01 2023-07-07 aggregatebydate
Getting Reports for testuser1@domain.com (1/3)
Got 1 Report for testuser1@domain.com on 2023-07-01...
Got 1 Report for testuser1@domain.com on 2023-07-02...
Got 1 Report for testuser1@domain.com on 2023-07-03...
Got 1 Report for testuser1@domain.com on 2023-07-04...
Got 1 Report for testuser1@domain.com on 2023-07-05...
Got 1 Report for testuser1@domain.com on 2023-07-06...
Got 1 Report for testuser1@domain.com on 2023-07-07...
Getting Reports for testuser2@domain.com (2/3)
Got 1 Report for testuser2@domain.com on 2023-07-01...
Got 1 Report for testuser2@domain.com on 2023-07-02...
Got 1 Report for testuser2@domain.com on 2023-07-03...
Got 1 Report for testuser2@domain.com on 2023-07-04...
Got 1 Report for testuser2@domain.com on 2023-07-05...
Got 1 Report for testuser2@domain.com on 2023-07-06...
Got 1 Report for testuser2@domain.com on 2023-07-07...
Getting Reports for testuser3@domain.com (3/3)
Got 1 Report for testuser3@domain.com on 2023-07-01...
Got 1 Report for testuser3@domain.com on 2023-07-02...
Got 1 Report for testuser3@domain.com on 2023-07-03...
Got 1 Report for testuser3@domain.com on 2023-07-04...
Got 1 Report for testuser3@domain.com on 2023-07-05...
Got 1 Report for testuser3@domain.com on 2023-07-06...
Got 1 Report for testuser3@domain.com on 2023-07-07...
date,gmail:num_emails_received,gmail:num_emails_sent
2023-07-01,27,2
2023-07-02,20,1
2023-07-03,38,3
2023-07-04,16,0
2023-07-05,87,6
2023-07-06,86,2
2023-07-07,49,1
```
Report on email activity for individual users, aggregate by user across dates.
```
$ gam report users select users testuser1,testuser2,testuser3@domain.com fields gmail:num_emails_received,gmail:num_emails_sent range 2023-07-01 2023-07-07 aggregatebyuser
Getting Reports for testuser1@domain.com (1/3)
Got 1 Report for testuser1@domain.com on 2023-07-01...
Got 1 Report for testuser1@domain.com on 2023-07-02...
Got 1 Report for testuser1@domain.com on 2023-07-03...
Got 1 Report for testuser1@domain.com on 2023-07-04...
Got 1 Report for testuser1@domain.com on 2023-07-05...
Got 1 Report for testuser1@domain.com on 2023-07-06...
Got 1 Report for testuser1@domain.com on 2023-07-07...
Getting Reports for testuser2@domain.com (2/3)
Got 1 Report for testuser2@domain.com on 2023-07-01...
Got 1 Report for testuser2@domain.com on 2023-07-02...
Got 1 Report for testuser2@domain.com on 2023-07-03...
Got 1 Report for testuser2@domain.com on 2023-07-04...
Got 1 Report for testuser2@domain.com on 2023-07-05...
Got 1 Report for testuser2@domain.com on 2023-07-06...
Got 1 Report for testuser2@domain.com on 2023-07-07...
Getting Reports for testuser3@domain.com (3/3)
Got 1 Report for testuser3@domain.com on 2023-07-01...
Got 1 Report for testuser3@domain.com on 2023-07-02...
Got 1 Report for testuser3@domain.com on 2023-07-03...
Got 1 Report for testuser3@domain.com on 2023-07-04...
Got 1 Report for testuser3@domain.com on 2023-07-05...
Got 1 Report for testuser3@domain.com on 2023-07-06...
Got 1 Report for testuser3@domain.com on 2023-07-07...
email,gmail:num_emails_received,gmail:num_emails_sent
testuser1@domain.com,117,11
testuser2@domain.com,47,2
testuser3@domain.com,159,2
```

## Monthly Report
### An example, running this on 3rd December 2020;-
If combined with a scheduled task or cron job, this will produce an ongoing report with a new tab/sheet for each month.  
```
$ gam report usage customer parameters meet:total_call_minutes,meet:total_meeting_minutes skipdaysofweek sat,sun previousmonths 1 todrive tdfileid <File ID> tdtitle "Meet Usage" tdtimeformat %Y-%m-%d tdaddsheet tdsheet "" tdsheettimeformat "%B %Y" tdsheetdaysoffset 6
```
**Breakdown**
* **gam report usage customer parameters meet:total_call_minutes,meet:total_meeting_minutes** - The GAM command
* **skipdaysofweek sat,sun** - exclude Sat & Sun, so only working days
* **previousmonths 1** - run against the previous months date range (regardless of how many days in the month, leap year etc)
* **todrive tdfileid <File ID> tdtitle "Meet Usage"  tdtimeformat %Y-%m-%d** - write the data to an existing Google Sheet and append with current date, so it will be called "Meet Usage - 2020-12-03"
* **tdaddsheet tdsheet ""** - Add a new tab/sheet with no name
* **tdsheettimeformat "%B %Y" tdsheetdaysoffset 6** - give the new tab/sheet a time stamp backdated by 6 days of 'Month Year', so for this example "November 2020", which will become the name of the new tab/sheet. The offset number must take you back in time into the previous month.

**Notes**  

You need to have already created the Google Sheet, to get the File ID. And tdtitle is not optional, although you should be able to specify "" (a blank name) if you just want the Google Sheet to show the updated date.
