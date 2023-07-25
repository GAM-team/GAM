# Reports
- [API documentation](#api-documentation)
- [Collections of Users](Collections-of-Users)
- [Definitions](#definitions)
- [Activity reports](#activity-reports)
- [Customer and user reports parameters](#customer-and-user-reports-parameters)
- [Customer usage reports](#customer-usage-reports)
- [Customer reports](#customer-reports)
- [User usage reports](#user-usage-reports)
- [User reports](#user-reports)

## API documentation
* https://developers.google.com/admin-sdk/reports/v1/reference/activities
* https://developers.google.com/admin-sdk/reports/v1/reference/customerUsageReports
* https://developers.google.com/admin-sdk/reports/v1/reference/userUsageReport

## Definitions
```
<DayOfWeek> ::= mon|tue|wed|thu|fri|sat|sun
<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
```
## Activity reports
```
<ActivityApplicationName> ::=
        access|accesstransparency|
        admin|
        calendar|calendars|
        chat|
        chrome|
        contextawareaccess|
        currents|gplus|google+|
        datastudio|
        devices|mobile|
        domain|
        drive|doc|docs|
        gcp|
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
        useraccounts

gam report <ActivityApplicationName> [todrive <ToDriveAttributes>*]
        [(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
        [([start <Time>] [end <Time>])|(range <Time> <Time>)|
         yesterday|today|thismonth|(previousmonths <Integer>)]
        [filtertime.* <Time>] [filter|filters <String>]
        [event|events <EventNameList>] [ip <String>]
        [groupidfilter <String>]
        [maxactivities <Number>] [maxresults <Number>]
        [countsonly [summary] [eventrowfilter]]
```
Select the application with `<ActivityApplicationName>`.

Select the users for whom information is desired.
* `user all` - All users, the default; there is one API call
* `user <UserItem>` - An individual user; there is one API call
* `orgunit|org|ou <OrgUnitPath>` - All users in the specified OU; there is one API call
  * `showorgunit` - Add a column labelled `actor.orgUnitPath` to the output; an additional API call is made to get the email addresses of the users in `<OrgUnitPath>`
* `select <UserTypeEntity>` - A selected collection of users, e.g., `select group staff@domain.com`; there is one API call per user

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

Use the `filtertime.* <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

You can use `config csv_output_row_filter` to filter the events if the API filter can't produce the results you want.

Limit to a list of specific events.
* `event|events <EventNameList>`

Limit to a specific IP address.
* `ip <String>`

Limit to those users that are a member of at least one of a list of groups.
* `groupidfilter <String>` - Format: "id:abc123,id:xyz456"

Limit the total number of activites.
* `maxactivities <Number>`

Limit the number of activities downloaded per API call; infrequently used.
* `maxresults <Number>`

By default, individual event details are displayed, these options modify what's displayed.
* `countsonly` - Limit the display to the number of occurences of each event for each user
* `countsonly summary` - Limit the display to the number of occurences of each event summarized across all users
* `countsonly [summary] eventrowfilter` - Apply `config csv_output_row_filter` to the event details rather than the event counts

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
```
Limit the time period.
* `start <Date>` - Default value is 30 days prior to `end <Date>`
* `end <Date>` - Default value is today
* `range <Date> <Date>` - Equivalent to `start <Date> end <Date>`
* `thismonth` - The current calendar month up to the current time
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month

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

gam report customers|customer|domain [todrive <ToDriveAttributes>*]
        [(date <Date>)|(range <Date> <Date>)|
         yesterday|today|thismonth|(previousmonths <Integer>)]
        [nodatechange|(fulldatarequired all|<CustomerServiceNameList>)]
        [(fields|parameters <String>)|(services <CustomerServiceNameList>)]
        [noauthorizedapps]
```
Specify the report date; the default is today's date.
* `date <Date>` - A single date; there is one API call
* `range <Date> <Date>` - A range of dates; there is an API call per date
* `yesterday` - Yesterday; there is one API call
* `today` - Today; there is one API call
* `thismonth` - The current calendar month up to the current time; there is an API call per date
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month; there is an API call per date

If no report is available for the specified date, can an earlier date be used?
* `nodatechange` - Do not report on an earlier date if no report is available for the specified date.

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

## User reports
User reports are generally available up to four days before the current date.
```
<UserServiceName> ::=
        accounts|
        classroom|
        docs|
        drive|
        gmail|
        gplus
<UserServiceNameList> ::= "<UserServiceName>(,<UserServiceName>)*"

gam report users|user [todrive <ToDriveAttributes>*]
        [(user all|<UserItem>)|(orgunit|org|ou <OrgUnitPath> [showorgunit])|(select <UserTypeEntity>)]
        [allverifyuser <UserItem>]
        [(date <Date>)|(range <Date> <Date>)|
         yesterday|today|thismonth|(previousmonths <Integer>)]
        [nodatechange|(fulldatarequired all|<UserServiceNameList>)]
        [filtertime.* <Time>] [filter|filters <String>]
        [(fields|parameters <String>)|(services <UserServiceNameList>)]
        [aggregatebydate|aggregatebyuser [Boolean]]
        [maxresults <Number>]
```
Select the users for whom information is desired.
* `user all` - All users, the default; there is one API call
* `user <UserItem>` - An individual user; there is one API call
* `orgunit|org|ou <OrgUnitPath>` - All users in the specified OU; there is one API call
  * `showorgunit` - Add a column labelled `orgUnitPath` to the output; an additional API call is made to get the email addresses of the users in `<OrgUnitPath>`
* `select <UserTypeEntity>` - A selected collection of users, e.g., `select group staff@domain.com`; there is one API call per user

Specify the report date; the default is today's date.
* `date <Date>` - A single date; there is one API call
* `range <Date> <Date>` - A range of dates; there is an API call per date
* `yesterday` - Yesterday; there is one API call
* `today` - Today; there is one API call
* `thismonth` - The current calendar month up to the current time; there is an API call per date
* `previousmonths <Integer>` - A number in the range 1 to 6 indicating calendar months previous to the current month; there is an API call per date

If no report is available for the specified date, can an earlier date be used?
* `nodatechange` - Do not report on an earlier date if no report is available for the specified date.

If only partial report data is available for the specified date and applications, can an earlier date be used?
* `fulldatarequired all` - Back up to an earlier date to get complete data until all applications have full report data
* `fulldatarequired <UserServiceNameList>` - Back up to an earlier date to get complete data until all applications in `<UserServiceNameList>` have full report data

Apply filters.
* `filter|filters <String>` - `<String>` is a comma separated list of filter expressions.

Use the `filtertime.* <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

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
gam report users parameters accounts:last_login_time filters "accounts:last_login_time<#filtertime#" filtertime -5y
```
Report on the users that haven't ever logged in.
```
gam report users parameters accounts:last_login_time filters "accounts:last_login_time==#filtertime#" filtertime never
```
Report on users Google Drive usage.
```
gam report users parameters accounts:drive_used_quota_in_mb,accounts:total_quota_in_mb,accounts:used_quota_in_mb,accounts:used_quota_in_percentage
```
Report on email activity for individual users.
```
$ gam report users select users testuser1,testuser2,testuser3 fields gmail:num_emails_received,gmail:num_emails_sent range 2019-02-01 2019-02-07
Getting Reports for testuser1@domain.com (1/3)
Getting Reports for testuser2@domain.com (2/3)
Getting Reports for testuser3@domain.com (3/3)
email,date,gmail:num_emails_received,gmail:num_emails_sent
testuser1@domain.com,2019-02-01,34,0
testuser1@domain.com,2019-02-02,12,0
testuser1@domain.com,2019-02-03,15,0
testuser1@domain.com,2019-02-04,23,0
testuser1@domain.com,2019-02-05,30,0
testuser1@domain.com,2019-02-06,26,0
testuser1@domain.com,2019-02-07,23,0
testuser2@domain.com,2019-02-01,136,18
testuser2@domain.com,2019-02-02,24,0
testuser2@domain.com,2019-02-03,59,1
testuser2@domain.com,2019-02-04,146,19
testuser2@domain.com,2019-02-05,141,17
testuser2@domain.com,2019-02-06,124,36
testuser2@domain.com,2019-02-07,137,26
testuser3@domain.com,2019-02-01,144,5
testuser3@domain.com,2019-02-02,49,0
testuser3@domain.com,2019-02-03,59,1
testuser3@domain.com,2019-02-04,111,4
testuser3@domain.com,2019-02-05,136,11
testuser3@domain.com,2019-02-06,114,12
testuser3@domain.com,2019-02-07,139,10
```
Report on email activity for individual users, aggregate by date.
```
gam report users select users testuser1,testuser2,testuser3 fields gmail:num_emails_received,gmail:num_emails_sent range 2019-02-01 2019-02-07 aggregatebydate
Getting Reports for testuser1@domain.com (1/3)
Getting Reports for testuser2@domain.com (2/3)
Getting Reports for testuser3@domain.com (3/3)
date,gmail:num_emails_received,gmail:num_emails_sent
2019-02-01,314,23
2019-02-02,85,0
2019-02-03,133,2
2019-02-04,280,23
2019-02-05,307,28
2019-02-06,264,48
2019-02-07,299,36
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