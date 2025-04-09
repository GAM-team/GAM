# Chrome Profile Management
- [API documentation](#api-documentation)
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Delete Chrome profiles](#delete-chrome-profiles)
- [Display Chrome profiles](#display-chrome-profiles)
- [Profile Query Searchable Fields](#profile-query-searchable-fields)

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
* [Turn on Chrome Browser and Profile Reporting](https://support.google.com/chrome/a/answer/9301421)

## Definitions
```
<CustomerID> ::= <String>
<ChromeProfilePermanentID> ::= <String>
<ChromeProfileName> ::= customers/<CustomerID>/profiles/<ChromeProfilePermanentID>

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
- `formatjson` - Display the fields in JSON format.

```
gam show chromeprofiles
        [filtertime.* <Time>] [filter <String>]
        [orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
        <ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
        [formatjson]
```

Use these options to select Chrome profiles; if none are chosen, all Chrome profiles in the account are selected:
* `filter <String>` - Limit profiles to those that match a query

Select the fields to be displayed:
* `<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]` - Display a selected list of fields

Use the `filtertime<String> <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The `filtertime<String> <Time>` value replaces the string `#fiktertime<String>#` in the `filter <String>`.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

```
gam print chromeprofiles [todrive <ToDriveAttribute>*]
        [filtertime.* <Time>] [filter <String>]
        [orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
        <ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
        [[formatjson [quotechar <Character>]]
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