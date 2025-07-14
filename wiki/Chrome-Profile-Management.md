# Chrome Profile Management
- [API documentation](#api-documentation)
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Delete Chrome Profiles](#delete-chrome-profiles)
- [Display Chrome Profiles](#display-chrome-profiles)
- [Profile Query Searchable Fields](#profile-query-searchable-fields)
- [Collections of Chrome Profile names for commands](#collections-of-chrome-profile-names-for-commands)
- [Create a Chrome Profile command](#create-a-chrome-profile-command)
- [Display Chrome Profile commands](#display-chrome-profile-commands)

## Introduction
These features were added in version 7.01.00.

To use these commands you must update your client authorization.
```
gam oauth create

[*]  3)  Chrome Management API - Profiles (supports readonly)
```

You must enable managed profile reporting, see: https://support.google.com/chrome/a/answer/9301421
Follow instructions at: Turn on managed profile reporting

## API documentation
* [Chrome Management API - Profiles](https://developers.google.com/chrome/management/reference/rest/v1/customers.profiles)
* [Chrome Management API - Profile Commands](https://developers.google.com/chrome/management/reference/rest/v1/customers.profiles.commands)
* [Turn on Chrome Browser and Profile Reporting](https://support.google.com/chrome/a/answer/9301421)

## Definitions
* [`<FileSelector> | <CSVFileSelector>`](Collections-of-Items)

```
<CustomerID> ::= <String>
<ChromeProfilePermanentID> ::= <String>
<ChromeProfileName> ::= customers/<CustomerID>/profiles/<ChromeProfilePermanentID> | <ChromeProfilePermanentID>
<ChromeProfileNameList> ::= "<ChromeProfileName>(,<ChromeProfileName>)*"
<ChromeProfileCommandName> ::= <ChomeProfileName>/commands/<String>
<ChromeProfileCommandNameList> ::= "<ChromeProfileCommandName>(,<ChromeProfileCommandName>)*"
<ChromeProfileNameEntity> ::=
        <ChromeProfileNameList> |
        (select <FileSelector>|<CSVFileSelector>) |
        (filter <String> (filtertime<String> <Time>)* [orderby <ChromeProfileOrderByFieldName> [ascending|descending]]) |
        (commands <ChromeProfileCommandNameList>|<FileSelector>|<CSVFileSelector>)

<ChromeProfileFieldName> ::=
        affiliationstate|
        annotatedlocation|
        annotateduser|
        attestationcredential|
        profilechannel|
        profileversion|
        deviceinfo|
        displayname|
        extensioncount|
        firstenrollmenttime|
        identityprovider|
        lastactivitytime|
        lastpolicyfetchtime|
        lastpolicysynctime|
        laststatusreporttime|
        name|
        osplatformtype|
        osplatformversion|
        osversion|
        policycount|
        profileid|
        profilepermanentid|
        reportingdata|
        useremail|
        userid
<ChromeProfileFieldNameList> ::= "<ChromeProfileFieldName>(,<ChromeProfileFieldName>)*"

<ChromeProfileOrderByFieldName> ::=
        affiliationstate|
        profilechannel|
        profileversion|
        displayname|
        extensioncount|
        firstenrollmenttime|
        identityprovider|
        lastactivitytime|
        lastpolicysynctime|
        laststatusreporttime|
        osplatformtype|
        osversion|
        policycount|
        profileid|
        useremail
```
## Delete Chrome profiles
```
gam delete chromeprofile <ChromeProfileName>
```

## Display Chrome profiles
```
gam info chromeprofile <ChromeProfileName>
        <ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
        [formatjson]
```
Select the fields to be displayed:
* `<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]` - Display a selected list of fields

By default, Gam displays the information as an indented list of keys and values:
* `formatjson` - Display the fields in JSON format.

```
gam show chromeprofiles
        [filter <String> (filtertime<String> <Time>)*]
        [orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
        <ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
        [formatjson]
```

Use these options to select Chrome profiles; if none are chosen, all Chrome profiles in the account are selected:
* `filter <String>` - Limit profiles to those that match a query

Select the fields to be displayed:
* `<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]` - Display a selected list of fields

Use the `filtertime<String> <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The `filtertime<String> <Time>` value replaces the string `#filtertime<String>#` in the `filter <String>`.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

By default, Gam displays the information as an indented list of keys and values:
* `formatjson` - Display the fields in JSON format.

```
gam print chromeprofiles [todrive <ToDriveAttribute>*]
        [filter <String> (filtertime<String> <Time>)*]
        [orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
        <ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
        [formatjson [quotechar <Character>]]
```

Use these options to select Chrome profiles; if none are chosen, all Chrome profiles in the account are selected:
* `filter <String>` - Limit profiles to those that match a query

The first two columns will always `name,profileId`; the remaining field names will be sorted if `sortheaders` is specified;
otherwise, the remaining field names will appear in the order specified.

Select the fields to be displayed:
* `<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]` - Display a selected list of fields

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Profile Query Searchable Fields

These are the fields that can be used in a filter:
```
affiliationState
browserChannel
browserVersion
displayName
extensionCount
firstEnrollmentTime
identityProvider
lastActivityTime
lastPolicySyncTime
lastStatusReportTime
osPlatformType
osVersion
ouId
policyCount
profileId
userEmail
```
Any of the above fields can be used to specify a filter, and filtering by multiple fields is supported with AND operator.
String type fields and enum type fields support '=' and '!=' operators. Wildcard '*' can be used with a string type field filter.
The integer type and the timestamp type fields support '=', '!=', '<', '>', '<=' and '>=' operators.
Timestamps expect an RFC-3339 formatted string (e.g. 2012-04-21T11:30:00-04:00).
In addition, string literal filtering is also supported, for example, 'ABC' as a filter maps to a filter that checks if any of the filterable string type fields contains 'ABC'.

Organization unit number can be used as a filtering criteria here by specifying 'ouId = <String>', please note that only single OU ID matching is supported.

### Examples

For Windows PowerShell, replace `\"` with ``` `" ```.

Print information about Chrome profiles synced more than 30 days ago:

```
gam print chromeprofiles filter "lastPolicySyncTime < \"#filtertime1#\"" filtertime1 -30d
```

Print information about Chrome profiles synced in the last 30 days:

```
gam print chromeprofiles filter "lastPolicySyncTime >= \"#filtertime1#\"" filtertime1 -30d
```

Print information about Chrome profiles synced between 45 days ago and 30 days ago:

```
gam print chromeprofiles filter "lastPolicySyncTime >= \"#filtertime1#\" lastPolicySyncTime <= \"#filtertime2#\"" filtertime1 -45d filtertime2 -30d
```

Print information about Chrome profiles on Windows.
```
gam print chromeprofiles filter "osPlatformType=WINDOWS"
```
## Collections of Chrome Profile names for commands
```
<ChromeProfileNameEntity> ::=
        <ChromeProfileNameList> |
        (select <ChromeProfileNameList>|<FileSelector>|<CSVFileSelector>) |
        (filter <String> (filtertime<String> <Time>)* [orderby <ChromeProfileOrderByFieldName> [ascending|descending]]) |
        (commands <ChromeProfileCommandNameList>|<FileSelector>|<CSVFileSelector>)
```
* `<ChromeProfileNameList>` - A list of Chrome profile names
* `select <ChromeProfileNameList>` - A list of Chrome profile names
* `select <FileSelector>|<CSVFileSelector>` - A flat or CSV file containing Chrome profile names
* `filter <String> (filtertime<String> <Time>)*` - A filter to select Chrome profiles
* `commands  <ChromeProfileCommandNameList>` - A list of  Chrome profile command names
* `commands  <FileSelector>|<CSVFileSelector>` - A flat or CSV file containing Chrome profile command names

Use the `filtertime<String> <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The `filtertime<String> <Time>` value replaces the string `#filtertime<String>#` in the `filter <String>`.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

## Create a Chrome Profile command
Clear a Chrome Browser profile cache and/or cookies.
```
gam create chromeprofilecommand <ChromeProfileNameEntity>
        [clearcache [<Boolean>]] [clearcookies [<Boolean>]]
        [csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
```
By default, when a Chrome profile command is created, GAM outputs details of the command as indented keywords and values.
* `formatjson` - Display the details in JSON format.
* `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` - Output the details in CSV format.

## Display Chrome Profile commands
Display the status of a specific Chrome Browser profile command.
```
gam info chromeprofilecommand <ChromeProfileCommandName>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values:
* `formatjson` - Display the fields in JSON format.

Display the status of selected Chrome Browser profile commands.
```
gam show chromeprofilecommands <ChromeProfileNameEntity>
        [formatjson]
```

By default, Gam displays the information as an indented list of keys and values:
* `formatjson` - Display the fields in JSON format.
```
gam print chromeprofilecommands <ChromeProfileNameEntity> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Examples

For Windows PowerShell, replace `\"` with ``` `" ```.

Clear cache and cookies for two specific Chrome profiles:
```
gam create chromeprofilecommand 4c6c0a9f-de78-4285-be86-713fca8cffff,aa03151c-7c1d-41fe-b793-5753e167ffff clearcache clearcookies
```

Display the command status for those Chrome profiles:
```
gam show chromeprofilecommand 4c6c0a9f-de78-4285-be86-713fca8cffff,aa03151c-7c1d-41fe-b793-5753e167ffff
gam print chromeprofilecommand 4c6c0a9f-de78-4285-be86-713fca8cffff,aa03151c-7c1d-41fe-b793-5753e167ffff
```

Clear cache and cookies for Chrome profiles in a CSV file named `ChromeProfiles.csv` with a column `name`:
```
gam create chromeprofilecommand select csvfile ChromeProfiles.csv:name clearcache clearcookies
```

Display the command status for those Chrome profiles:
```
gam show chromeprofilecommand select csvfile ChromeProfiles.csv:name
gam print chromeprofilecommand select csvfile ChromeProfiles.csv:name
```

Clear cache and cookies for Chrome profiles with last activity more that 60 days ago:
```
gam create chromeprofilecommand filter "lastActivityTime < \"#filtertime1#\"" filtertime1 -60d clearcache clearcookies
```

Display the command status for those Chrome profiles:
```
gam show chromeprofilecommand filter "lastActivityTime < \"#filtertime1#\"" filtertime1 -60d
gam print chromeprofilecommand filter "lastActivityTime < \"#filtertime1#\"" filtertime1 -60d
```

Clear cache and cookies for Chrome profiles with last activity more that 60 days ago:
```
gam redirect csv ./ChromeProfileCmds.csv create chromeprofilecommand filter "lastActivityTime < \"#filtertime1#\"" filtertime1 -60d clearcache clearcookies csv
```

Display the command status for those Chrome profile commands
```
gam show chromeprofilecommand commands ChromeProfileCmds.csv:name
gam print chromeprofilecommand commands ChromeProfileCmds.csv:name
```
