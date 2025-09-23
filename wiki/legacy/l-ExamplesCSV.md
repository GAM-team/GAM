<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Printing All Users](#printing-all-users)
    - [Syntax](#syntax)
    - [Example](#example)
  - [users.csv contains:](#userscsv-contains)
  - [Smith, wsmith@example.com, William,](#smith-wsmith@examplecom-william)
  - [](#)
- [Printing All Groups](#printing-all-groups)
    - [Syntax](#syntax-1)
    - [Examples](#examples)
  - [](#-1)
- [Print All Aliases](#print-all-aliases)
    - [Syntax](#syntax-2)
    - [Example](#example-1)
  - [](#-2)
- [Print All Organizational Units](#print-all-organizational-units)
    - [Syntax](#syntax-3)
    - [Example](#example-2)
  - [](#-3)
- [Print All Resource Calendars](#print-all-resource-calendars)
    - [Syntax](#syntax-4)
    - [Example](#example-3)
  - [](#-4)
- [Print Reports](#print-reports)
    - [Syntax](#syntax-5)
    - [Example](#example-4)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

(TODO: Add table of contents.)

_**Comments have been turned off for these help pages, please post your questions and comments to the [Mailing List](http://groups.google.com/group/google-apps-manager)**_

# Printing All Users

### Syntax
```
gam print users [firstname] [lastname] [username] [ou] [suspended] [changepassword] [agreed2terms] [admin] [aliases] [groups]
```
prints a CSV file of all users in the Google Apps Organization. The CSV output can be redirected to a file using the operating system's pipe command (such as "> users.csv") see examples below. By default, the only column printed is the user's full email address. The optional arguments firstname, lastname, username, ou (organization unit), suspended, changepassword, agreed2terms, admin, nicknames and groups add the respective additonal column to the CSV output. Note that adding one or more of firstname, lastname, suspended, changepassword, agreed2terms or admin will require an additional call to Google's servers and will increase the length of time for the command to complete. Adding aliases will also require an additional call to Google's servers. Note also that adding  groups will require 1 additional call to Google's servers <b>per user</b> which will significantly increase the length of time for the command to complete.

### Example
This example will generate the csv file users.csv showing with columns for Email, Firstname and Lastname
```
gam print users firstname lastname > users.csv
Getting all users in the organization (may take some time on a large Google Apps
 account)...
Getting detailed info for users in example.com domain (may take some time on a large
 domain)...

users.csv contains:
--
Lastname, Email, Firstname,
User, admin@example.com, Super,
Jones, pjones@example, Paul,
Smith, wsmith@example.com, William,
--
```

---


# Printing All Groups
### Syntax
```
gam print groups [name] [description] [members] [managers] [owners] [settings] [domain <domainname>] [admincreated] [id] [aliases] [todrive]
```
prints a CSV file of all groups in the Google Apps domain. The CSV output can be redirected to a file using the operating system's pipe command (such as "> groups.csv") see examples below. By default, the only column printed is the email address. The optional arguments name and description add the respective additional column to the CSV output. The optional arguments members, managers, owners and settings each perform additional API calls per group which may greatly increase the time it takes the command to complete. members, managers and owners will include a column for the respective role. settings will add multiple columns for the groups advanced settings. domain will limit the results to groups that have a primary address in the supplied domain. admincreated will include a True/False column in the results, False being user-created groups. aliases will add 2 columns to the output, Aliases and nonEditableAliases. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

### Examples
this example will output basic details for all groups and upload the results to Google Drive.
```
gam print groups name description todrive
```

---


# Print All Aliases
### Syntax
```
gam print aliases [todrive]
```
prints a CSV file of all user and group aliases in the Google Apps domain. The CSV output can be redirected to a file using the operating system's pipe command (such as "> nicknames.csv") see examples below. The optional todrive parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

### Example
this example will output all aliases to Google Drive
```
gam print nicknames todrive
```

---


# Print All Organizational Units
### Syntax
```
gam print orgs [name] [description] [parent] [inherit]
```
prints a CSV file of all organizational units in the Google Apps account. The CSV output can be redirected to a file using the operating system's pipe command (such as "> orgs.csv") see examples below. By default, the only column output is "Path" (OUs full path). The optional arguments name, description, parent and inherit add the respective additonal column to the CSV output. Only 1 call to Google's servers is done no matter which arguments are specified so the optional arguments should not significantly increase the time it takes for the command to complete.

### Example
this example will output all organizations to the file orgs.csv including all optional columns
```
gam print orgs name description parent inherit > orgs.csv
```

---


# Print All Resource Calendars
### Syntax
```
gam print resources [id] [description] [email]
```
prints a CSV file of all resource calendars in the Google Apps account. The CSV output can be redirected to a file using the operating system's pipe command (such as "> resources.csv") see examples below. By default, the only column output is "Name"The optional arguments id, description and email add the respective additonal column to the CSV output. Only 1 call to Google's servers is done no matter which arguments are specified so the optional arguments should not significantly increase the time it takes for the command to complete.

### Example
this example will output all resource calendars to the file resources.csv including all optional columns
```
gam print resources id description email > resources.csv
```

---


# Print Reports
### Syntax
```
gam report accounts|activity|disk_space|email_clients|summary [YYYY-MM-DD]
```
Prints one of 5 Google Apps reports:
  * The **accounts** report contains a list of all of the hosted accounts that exist in your domain on a particular day. The report includes both active accounts and suspended accounts. The status column will indicate whether each account is active or suspended. The field definitions for the accounts report can be found [here](http://code.google.com/googleapps/domain/reporting/google_apps_reporting_api.html#Accounts_Report).
  * The **activity** report identifies the total number of accounts in your domain as well as the number of active and idle accounts over several different time periods. In this report, activity encompasses user interaction with his email, such as reading or sending email. The activity statistics includes web mail as well as POP activity. The field definitions for the activity report can be found [here](http://code.google.com/googleapps/domain/reporting/google_apps_reporting_api.html#Activity_Report).
  * The **disk\_space** report shows the amount of disk space occupied by users' mailboxes. The report identifies the total number of accounts in your domain as well as the number of accounts that fall into several different size groupings. Mailboxes that occupy less than 1GB of disk space are grouped in increments of 100MB, and mailboxes that occupy between 1GB and 10GB of disk space are grouped in increments of 500MB. The field definitions for the disk\_space report can be found [here](http://code.google.com/googleapps/domain/reporting/google_apps_reporting_api.html#Disk_Space_Report).
  * The **email\_clients** report explains how users in your domain access their hosted accounts on a day-by-day basis. For each day, the report lists the total number of accounts in your domain as well as the number and percentage of users who accessed their accounts using WebMail. This report does not include suspended accounts in the account total. The field definitions for the email\_clients report can be found [here](http://code.google.com/googleapps/domain/reporting/google_apps_reporting_api.html#Email_Clients_Report).
  * The **summary** report contains the total number of accounts, total mailbox usage in bytes and total mailbox quota in megabytes for your domain. Each row in the report contains data for one day. This report does not include information for suspended accounts. The field definitions for the summary report can be found [here](http://code.google.com/googleapps/domain/reporting/google_apps_reporting_api.html#Summary_Report).

optionally, a date can be specified in YYY-MM-DD format. The report for the given day will be pulled. If not specified, the report for the most recent day that has passed 12pm Pacific time will be pulled (e.g. today or yesterday if it's not yet noon Pacific time).

**Note:** unlike the "gam print" commands, the report commands offer a snapshot of activity on a Google Apps domain for the given day, they are not realtime. For example, if you create a new user and then pull the accounts report, that user will not be included. It will take 24-48 hours before the user is included in the most recent accounts report.

### Example
This command will pull the most recently available accounts report.
```
gam report accounts
```

This example will pull the summary report from last month.
```
gam report summary 2011-11-30
```