- [Printing All Users](#printing-all-users)
- [Printing All Groups](#printing-all-groups)
- [Print All Aliases](#print-all-aliases)
- [Print All Organizational Units](#print-all-organizational-units)
- [Print All Resource Calendars](#print-all-resource-calendars)
- [Print All Domains and Domain Aliases](#print-all-domains-and-domain-aliases)
- [Print Mobile Devices](#print-mobile-devices)
- [Print Chrome OS Devices](#print-chrome-os-devices)
- [Print Chrome OS Device Activity](#print-chrome-os-device-activity)
- [Print Licenses](#print-licenses)
- [Reports](#reports)
  - [User Report](#users-report)
  - [Customer Report](#customer-report)
  - [Usage Reports](#usage-reports)
  - [Possible Usage Parameters](#possible-usage-parameters)
  - [Drive Report](#drive-report)
  - [Admin Actions Report](#admin-actions-report)
  - [Calendar Actions Report](#calendar-actions-report)
  - [Group Actions Report](#group-actions-report)
  - [Login Audit Report](#login-audit-report)
  - [Mobile Audit Report](#mobile-audit-report)
  - [OAuth Token Activities Report](#oauth-token-activities-report)

# Printing All Users

### Syntax
```
gam print users [allfields] [custom all|list,of,schemas] [userview] [ims] [emails] [externalids] [relations] [addresses] [organizations] [phones] [licenses] [firstname] [lastname] [emailparts] [deleted_only] [orderby email|firstname|lastname] [ascending|descending] [domain] [query <query>] [fullname] [ou] [suspended] [changepassword] [agreed2terms] [admin] [gal] [id] [creationtime] [lastlogintime] [aliases] [groups] [todrive]
```
prints a CSV file of all users in the G Suite Organization. The CSV output can be redirected to a file using the operating system's pipe command (such as "> users.csv") see examples below. By default, the only column printed is the user's full email address. The optional argument allfields adds all fields (except groups which requires per-user API calls) to the CSV. The optional argument deleted\_only prints only users deleted within the past 5 days. The optional custom argument adds custom schemas. If all is specified, all custom schemas will be included. Otherwise only those listed in a comma separated list will be included. The optional userview parameter returns only fields that are viewable by regular users and can be run even if GAM is authenticated against a regular user account. The optional licenses parameter includes a column for all SKUs assigned to each user. The optional query parameter should match the [API search for users](https://developers.google.com/admin-sdk/directory/v1/guides/search-users) format. All other arguments add the respective additional column to the CSV output. Note that adding groups will require 1 additional call to Google's servers <b>per user</b> which will significantly increase the length of time for the command to complete. The optional todrive argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
This example will generate the csv file users.csv showing with columns many fields
```
gam print users allfields > users.csv
Getting all users in the organization (may take some time on a large G Suite account)...

users.csv contains:
--
Email,Firstname,Lastname,Fullname,Username,OU,Suspended,SuspensionReason,ChangePassword,AgreedToTerms,DelegatedAdmin,Admin,CreationTime,LastLoginTime,Aliases,NonEditableAliases,ID,PhotoURL,IncludeInGlobalAddressList
jsmith@acme.com,Jon,Smith,Jon Smith,jsmith,/Sales,False,,False,True,False,False,2012-03-23T15:04:19.000Z,2013-05-06T16:02:36.000Z,,jsmith@acme-alias.gov,106100537778424449519,,True
--
```

---


# Printing All Groups
### Syntax
```
gam print groups [name] [description] [admincreated] [id] [aliases] [members] [owners] [managers] [settings] [todrive]
```
prints a CSV file of all groups in the G Suite domain. The CSV output can be redirected to a file using the operating system's pipe command (such as "> groups.csv") see examples below. By default, the only column printed is the Group email address. The optional arguments name, description, id and admincreated add the respective additional column to the CSV output. The optional arguments members, owners, managers and settings each perform 1 additional API call per group which may greatly increase the time it takes the command to complete. settings will add multiple columns for the groups advanced settings. The optional todrive argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Examples
this example will output all details for all groups to the file groups.csv
```
gam print groups name description admincreated id aliases members owners managers settings > groups.csv
```

---


# Print All Aliases
### Syntax
```
gam print aliases [todrive]
```
prints a CSV file of all email aliases in the G Suite domain for both users and groups. The CSV output can be redirected to a file using the operating system's pipe command (such as "> nicknames.csv") see examples below. The optional todrive argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
this example will output all nicknames to the file aliases.csv
```
gam print aliases > aliases.csv
```

---


# Print All Organizational Units
### Syntax
```
gam print orgs [name] [description] [parent] [inherit] [allfields] [todrive]
```
prints a CSV file of all organizational units in the G Suite account. The CSV output can be redirected to a file using the operating system's pipe command (such as "> orgs.csv") see examples below. By default, the only column output is "Path" (OUs full path). The optional argument allfields will include all possible fields in the CSV. The optional arguments name, description, parent and inherit add the respective additonal column to the CSV output. Only 1 call to Google's servers is done no matter which arguments are specified so the optional arguments should not significantly increase the time it takes for the command to complete. The optional todrive argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
this example will output all organizations to the file orgs.csv including all optional columns
```
gam print orgs name description parent inherit > orgs.csv
```

---


# Print All Resource Calendars
### Syntax
```
gam print resources [description] [type] [allfields] [todrive]
```
prints a CSV file of all resource calendars in the G Suite account. The CSV output can be redirected to a file using the operating system's pipe command (such as "> resources.csv") see examples below. The optional arguments description and type add the respective additional column to the CSV output. The optional argument allfields will add all returned fields (including description and type) to the output. The optional todrive argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
this example will output all resource calendars to the file resources.csv including all optional columns
```
gam print resources allfields > resources.csv
```
---

# Print All Domains and Domain Aliases

### Syntax
```
gam print domains [todrive]
```

Outputs CSV of all domains. The todrive parameter causes GAM to create a Google Spreadsheet of results rather than outputting a CSV.

---

# Print Mobile Devices
### Syntax
```
gam print mobile [query <query>] [basic|full] [orderby deviceid|email|lastsync|model|name|os|status|type] [ascending|descending] [todrive]
```

Prints all mobile devices connected to the G Suite instance. All fields are included in the CSV. The optional argument `query` specifies an optional query to limit output results. The format of the query parameter should match the [Search format of the Control Panel](http://support.google.com/a/bin/answer.py?hl=en&answer=1408863#search). The `basic` and `full` arguments control the selection of fields that are output. The `orderby` and `ascending/descending` parameters determine how the CSV output is sorted. The optional `todrive` argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
This example prints details on all mobile devices in the domain
```
gam print mobile
```

This example prints all of jsmith@acme.org's mobile devices
```
gam print mobile query "email:jsmith@acme.org"
```

---


# Print Chrome OS Devices
### Syntax
```
gam print cros [query <query>] [orderby location|user|lastsync|serialnumber|supportenddate] [ascending|descending] [todrive] [allfields|full|basic] [nolists] [listlimit <Number>] <CrOSFieldName>* [fields <CrOSFieldNameList>]
```
Print all Chrome OS devices enrolled in the G Suite instance. By default, the only column printed is the deviceId. The optional arguments `allfields/full` add all fields to the output; the optional argument `basic` adds some essential fields to the output. The `<CrOSFieldName>*` and `fields <CrOSFieldNameList>` arguments give you the ability to select the specific fields you want output. The optional parameter `query` specifies a query to perform, limiting the results to matching devices. The query format is described in Google's [help article](http://support.google.com/chrome/a/bin/answer.py?hl=en&answer=1698333). The `orderby` and `ascending/descending` parameters determine sorting of CSV output. The optional `todrive` argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

The full data for a Chrome OS device includes two repeating fields, `recentUsers` and `activeTimeRanges`, with multiple entries of two columns each that makes for a large number of columns in the CSV output. Use the `listlimit <Number>` argument to limit each of the repeating fields to `<Number>` entries of two columns each. The `nolists` argument eliminates these two fields from the output. Specifying either or both of `recentusers` or `activetimeranges` as a field includes the fields in the output, but there are only two columns per field per row; multiple rows are written to the CSV output to include all of the values. The `listlimit <Number>` argument limits the rows written to `<Number>`.

### Example
This example prints basic data for all Chrome OS Devices enrolled in the domain.

```
gam print cros basic
```

This example prints all Chrome OS devices annotated as belonging to jsmith@acme.org

```
gam print cros query "user:jsmith@acme.org"
```

---

# Print Chrome OS Device Activity
### Syntax
```
gam print crosactivity [query <query>] [todrive] [times] [users] [start <yyyy-mm-dd>] [end <yyyy-mm-dd>]
```
Print information about Chrome OS device activity and recent users. Outputs one line per device per daily usage and one line per device with recent users. The optional parameter `query` specifies a query to perform, limiting the results to matching devices. The query format is described in Google's [help article](http://support.google.com/chrome/a/bin/answer.py?hl=en&answer=1698333). The optional `todrive` argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally. The optional times and users arguments specify whether only times or users should be output. By default, both times and users are included in the CSV output. The optional start and end date parameters specify the oldest and newest activity dates that should be included in the output, be default all dates returned by the API are included (usually max 14 entries).

### Example
This example prints all Chrome OS activity times to a spreadsheet.
```
gam print crosactivity todrive
```
----

# Print Licenses
### Syntax
```
<ProductID> ::=
        Google-Apps|
        Google-Chrome-Device-Management|
        Google-Coordinate|
        Google-Drive-storage|
        Google-Vault|
        101001|
        101005|
        101031
<ProductIDList> ::= "(<ProductID>|SKUID>)(,<ProductID>|SKUID>)*"
<SKUID> ::=
        cloudidentity|identity|1010010001|
        cloudidentitypremium|identitypremium|1010050001|
        free|standard|Google-Apps|
        gafb|gafw|basic|gsuitebasic|Google-Apps-For-Business|
        gafg|gsuitegovernment|gsuitegov|Google-Apps-For-Government|
        gams|postini|gsuitegams|gsuitepostini|gsuitemessagesecurity|Google-Apps-For-Postini|
        gal|lite|gsuitelite|Google-Apps-Lite|
        gau|unlimited|gsuitebusiness|Google-Apps-Unlimited|
        gae|enterprise|gsuiteenterprise|1010020020|
        gsefe|e4e|gsuiteenterpriseeducation|1010310002|
        chrome|cdm|googlechromedevicemanagement|Google-Chrome-Device-Management|
        coordinate|googlecoordinate|Google-Coordinate|
        drive20gb|20gb|googledrivestorage20gb|Google-Drive-storage-20GB|
        drive50gb|50gb|googledrivestorage50gb|Google-Drive-storage-50GB|
        drive200gb|200gb|googledrivestorage200gb|Google-Drive-storage-200GB|
        drive400gb|400gb|googledrivestorage400gb|Google-Drive-storage-400GB|
        drive1tb|1tb|googledrivestorage1tb|Google-Drive-storage-1TB|
        drive2tb|2tb|googledrivestorage2tb|Google-Drive-storage-2TB|
        drive4tb|4tb|googledrivestorage4tb|Google-Drive-storage-4TB|
        drive8tb|8tb|googledrivestorage8tb|Google-Drive-storage-8TB|
        drive16tb|16tb|googledrivestorage16tb|Google-Drive-storage-16TB|
        vault|googlevault|Google-Vault|
        vfe|googlevaultformeremployee|Google-Vault-Former-Employee
<SKUIDList> ="<SKUID>(,<SKUID>)*"

gam print license|licenses|licence|licences [todrive] [(products|product <ProductIDList>)|(skus|sku <SKUIDList>)]

```
Print G Suite, Google Drive storage and Google Coordinate license assignments for the domain. The optional todrive argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
This example gets all license assignments for the G Suite instance and uploads the spreadsheet to Google Docs.
```
gam print licenses todrive
```

---


# Reports
## Users Report
### Syntax
```
gam report users [todrive] [date <yyyy-mm-dd>] [user <email>] [filter <filter terms>] [fields <included fields>]
```

Display or upload to Google Drive a CSV report of current users. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional date parameter specifies when the report should be pulled for, when not specified, GAM pulls the most recently available report from Google. The optional user parameter specifies the email address of a single user whose data should be returned, by default all users in the G Suite instance are pulled. The optional filter parameter specifies search terms as described in [Google's API documentation](https://developers.google.com/admin-sdk/reports/v1/reference/userUsageReport/get). The optional fields parameter specifies a comma-separated list of fields (columns) to be included in the output, if not specified all columns are returned. A list of account parameters can be found [here](https://developers.google.com/admin-sdk/reports/v1/reference/usage-ref-appendix-a/users-accounts)

### Example
This command will pull the most recently available users report and upload to drive.
```
gam report users todrive
```

This command will pull a list of users who have not logged in since the beginning of the year.
```
gam report users filter 'accounts:last_login_time<2013-01-01T00:00:00.000Z'
```

This command will pull a list of users and their usage of Drive and Gmail.
```
gam report users parameters accounts:drive_used_quota_in_mb,accounts:gmail_used_quota_in_mb
```

---


## Customer Report
### Syntax
```
gam report customer [todrive] [date <yyyy-mm-dd>]
```
Display or upload to Google Drive a CSV report of aggregate user data across the G Suite instance (all users). The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional date parameter specifies when the report should be pulled for, when not specified, GAM pulls the most recently available report from Google.

### Example
This example uploads to Google Drive the most recent customer report
```
gam report customer todrive
```

## Usage Reports
### Syntax
```
gam report usage user|customer parameters <comma separated parameters> [start_date yyyy-mm-dd] [end_date yyyy-mm-dd] [orgunit <ou of users>] [skip_dates yyyy-mm-dd...] [skip_days_of_week mon,tue...] [todrive] [users|group|csvfile]
```
Provides CSV output of customer or user service usage. When the optional todrive argument is specified a Google Sheet is created and a chart can easily be added to present a graphical timeline. The parameters argument is required and specifies a comma-separated list of which parameters to retrieve. Possible parameter values can be discovered with the [gam report usageparameters](#possible-usage-parameters) command. The optional start_date and end_date arguments specify the date range to retrieve. When not specified, start_date will be one month ago and end_date will be the most recent report (may be 3-4 days old). The optional orgunit argument specifies a Google Organizational unit of users to retrieve report data against, orgunit works only with user, not customer. The optional arguments skip_dates and skip_days_of_week specify precise dates or days of week when usage should not be retrieved. This allows you to remove weekends or holidays from the usage data reducing "camel humping" of the data. By default with the user usage report, all users are retrieved or, if orgunit is specified users of a given orgunit are retrieved. Optionally you can specify a group, list of users or csvfile of users to retrieve. Note that this option can be very slow as an API call will be made per-user, per date.

### Example
This example generates a Google Sheet of Google Meet total usage across your users. Once in the Sheet a chart can easily be added to provide a graphical timeline of usage trends. Note that total_call_minutes = sum of all user time spent on a meeting, 5 users in a 10 minute meeting = 50 call minutes and total_meeting_minutes = sum of all meeting times, 5 users in a 10 minute meeting = 10 meeting minutes.
```
gam report usage customer parameters meet:total_call_minutes,meet:total_meeting_minutes todrive start_date 2020-03-01 skip_days_of_week sat,sun skip_dates 2020-03-06
```
----
## Possible Usage Parameters
### Syntax
```
gam report usageparameters customer|user
```
provides a printed list of all possible parameters which can be used with the [gam report usage](#usage-reports) parameters argument.

### Example
Shows all usage parameters available for customer
```
gam report usageparameters customer
```
## Drive Report
### Syntax
```
gam report drive [todrive] [user <user email> [ip <ip address>] [start <start time>] [end <end time>] [event view|edit|<other>] [filter <filter>]
```
Display or upload to Google Drive a CSV report of Google Drive activities by users in the past 180 days. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to documents viewed or edited by the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period.

The optional event parameter narrows the results down to specific event types such as just views or just edits. Refer to the [Drive Event Names appendix](https://developers.google.com/admin-sdk/reports/v1/reference/activity-ref-appendix-a/drive-event-names) for details.

For more granular control, use the optional filter parameter and pass in a filter query as documented in the [Reports API documentation](https://developers.google.com/admin-sdk/reports/reference/rest/v1/activities/list#body.QUERY_PARAMETERS.filters). Useful filter parameters include `doc_title` to list all activities for files with a given name and `doc_id` to list all activities for a specific file (both of which might be helpful to identify the owner of a file).

### Example
This example uploads to Drive a CSV of all doc actions:
```
gam report drive todrive
```

This example narrows the results down to actions performed by john@acme.com on Christmas Day 2013 (GMT):
```
gam report drive user john@acme.com start 2013-12-25T00:00:00.000Z end 2013-12-25T23:59:59.999Z
```

This example narrows the results down to just files with the name _All files in Policies Shared Drive_ and can be used to help identify the owner of a file when all you know is the name (will also match other files with the same name):
```
gam report drive filter "doc_title==All files in Policies Shared Drive"
```

This example narrows the results down to just files with the ID _9gEtJNb85tK87Py2SJl8uwq78BxSMMR_ and can be used to identify the owner of a file when all you know is the ID:
```
gam report drive filter "doc_id==9gEtJNb85tK87Py2SJl8uwq78BxSMMR"
```


## Admin Actions Report
### Syntax
```
gam report admin [todrive] [user <user email>] [ip <ip address>] [start <start time>] [end <end time>] [event <event name>]
```
Display or upload to Google Drive a CSV report of administrator activities for the G Suite domain. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to admin activities performed by the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period. The optional event parameter narrows the results down to the given admin event type.

[Details.](https://developers.google.com/admin-sdk/reports/v1/reference/activity-ref-appendix-a/admin-event-names)

### Example
This example uploads all recent admin changes to Google Drive.
```
gam report admin todrive
```

This example shows the admin activities of joe@schmo.com for 6/9/13 through 6/12/13 (GMT).
```
gam report admin todrive user joe@schmo.com start 2013-06-09T00:00:00.000Z end 2013-06-12T11:59:59.999Z
```

## Calendar Actions Report
### Syntax
```
gam report calendar [todrive] [user <user email>] [ip <ip address>] [start <start time>] [end <end time>] [event <event name>]
```
Display or upload to Google Drive a CSV report of calendar activities for the G Suite domain. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to admin activities performed by the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period. The optional event parameter narrows the results down to the given calendar event type.

[Details.](https://developers.google.com/admin-sdk/reports/v1/reference/activity-ref-appendix-a/calendar-event-names)

This example shows the calendar activities of joe@schmo.com for 6/9/13 through 6/12/13 (GMT).
```
gam report calendar user joe@schmo.com start 2013-06-09T00:00:00.000Z end 2013-06-12T11:59:59.999Z
```

## Group Actions Report
### Syntax
```
gam report groups [todrive] [user <user email>] [ip <ip address>] [start <start time>] [end <end time>] [event <event name>]
```
Display or upload to Google Drive a CSV report of group actions for the G Suite domain. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to group actions performed by the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period. The optional event parameter narrows the results down to the given group event type.

[Details.](https://developers.google.com/admin-sdk/reports/v1/reference/activity-ref-appendix-a/groups-event-names)

### Example
This example uploads all recent group changes to Google Drive.
```
gam report groups todrive
```

This example shows the group actions of joe@schmo.com for 6/9/13 through 6/12/13 (GMT).
```
gam report groups user joe@schmo.com start 2013-06-09T00:00:00.000Z end 2013-06-12T11:59:59.999Z
```

## Login Audit Report
### Syntax
```
gam report login [todrive] [user <user email>] [ip <ip address>] [start YYYY-MM-DDThh:mm:ss.000Z] [end YYYY-MM-DDThh:mm:ss.000Z] [event <event name>]
```
Display or upload to Google Drive a CSV report of user login activities for the G Suite domain. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to login activities performed by the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period. The optional event parameter narrows the results down to the given login event type.

[Details.](https://developers.google.com/admin-sdk/reports/v1/reference/activity-ref-appendix-a/login-event-names)

### Example
This example uploads all recent admin changes to Google Drive.
```
gam report login todrive
```

This example shows the login activities of joe@schmo.com.
```
gam report login todrive user joe@schmo.com
```

## Mobile Audit Report
### Syntax
```
gam report mobile [todrive] [user <user email>] [ip <ip address>] [start YYYY-MM-DDThh:mm:ss.000Z] [end YYYY-MM-DDThh:mm:ss.000Z] [event <event name>]
```
Display or upload to Google Drive a CSV report of mobile device activities for the G Suite domain. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to mobile device activities associated with the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period. The optional event parameter narrows the results down to the given mobile event type.

[Details.](https://developers.google.com/admin-sdk/reports/v1/appendix/activity/mobile)

### Example
This example uploads all recent mobile device activities to Google Drive.
```
gam report mobile todrive
```
## OAuth Token Activities Report
### Syntax
```
gam report token [todrive] [user <user email>] [ip <ip address>] [start YYYY-MM-DDThh:mm:ss.000Z] [end YYYY-MM-DDThh:mm:ss.000Z] [event <event name>]
```
Display or upload to Google Drive a CSV report of OAuth token activities for the G Suite domain. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. The optional user parameter narrows the results down to OAuth Token activities associated with the given user. The optional ip address parameter narrows results down to activities performed from the given IPv4 or IPv6 address. The optional start and end parameters narrow the results down to actions performed during the given period. The optional event parameter narrows the results down to the given token event type.

[Details.](https://developers.google.com/admin-sdk/reports/v1/reference/activity-ref-appendix-a/token-event-names)

### Example
This example uploads all recent OAuth Token activities to Google Drive.
```
gam report token todrive
```
