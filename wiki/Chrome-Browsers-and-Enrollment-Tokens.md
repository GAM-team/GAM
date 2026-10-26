# Chrome Browsers and Enrollment Tokens
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Raw Fields](#raw-fields)
- [Update Chrome browsers](#update-chrome-browsers)
  - [Example: Add a new note to existing notes](#example-add-a-new-note-to-existing-notes)
- [Move Chrome browsers from one OU to another](#move-chrome-browsers-from-one-ou-to-another)
- [Delete Chrome browsers](#delete-chrome-browsers)
- [Display Chrome browsers](#display-chrome-browsers)
  - [Examples](#examples)
- [Browser Query Searchable Fields](#browser-query-searchable-fields)
- [Create Chrome browser enrollment tokens](#create-chrome-browser-enrollment-tokens)
- [Revoke Chrome browser enrollment tokens](#revoke-chrome-browser-enrollment-tokens)
- [Display Chrome browser enrollment tokens](#display-chrome-browser-enrollment-tokens)
- [Token Query Searchable Fields](#token-query-searchable-fields)

## Notes

GAM 7.49.00 and higher use the `Chrome Management API` to manage/display Chrome Browers and Chrome Browser Enrollment Tokens
rather then the `Chrome Enterprise Core API` and the `Chrome Browser Token Enrollment API`.

To use these commands you should do the following.
```

gam oauth update.

This scope:

[*]  1)  Chrome Browser Cloud Management API (supports readonly)

has been replaced by these scopes:

[*]  2)  Chrome Management API - Browsers (supports readonly)
[*]  3)  Chrome Management API - Enrollment Tokens (supports readonly)
```

## API documentation
* [Chrome Browsers](https://developers.google.com/chrome/management/reference/rest/v1/customers.chromeBrowsers)
* [Chrome Browser Enrollment Tokens](https://developers.google.com/chrome/management/reference/rest/v1/customers.enrollmentTokens)

## Definitions
* [`<CrOSTypeEntity>`](Collections-of-ChromeOS-Devices)

```
<BrowserPermanentID> ::= <String>
<BrowserPermanmentIDList> ::= "<BrowserPermanmentID>(,<BrowserPermanmentID>)*"
<OrgUnitPath> ::= /|(/<String)+
<QueryBrowser> ::= <String> See: https://developers.google.com/chrome/management/reference/rest/v1/customers.chromeBrowsers/list, scroll down to filter
<QueryBrowserList> ::= "<QueryBrowser>(,<QueryBrowser>)*"
<QueryBrowserToken> ::= <String> See: https://developers.google.com/chrome/management/reference/rest/v1/customers.enrollmentTokens/list, scroll down to Filter 
<QueryBrowserTokenList> ::= "<QueryBrowserToken>(,<QueryBrowserToken>)*"
<TokenPermanentID> ::= <String>
<TokenPermanmentIDList> ::= "<TokenPermanmentID>(,<TokenPermanmentID>)*"

<BrowserEntity> ::=
        <BrowserPermanmentIDList> | 
        (query:<QueryBrowser>)|(query:orgunitpath:<OrgUnitPath>)|(query <QueryBrowser>) |
        (browserou <OrgUnitItem>) | (browserous <OrgUnitList>) |
        <FileSelector> | <CSVFileSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<BrowserAttribute> ::=
        (annotatedassetid|asset|assetid <String>)|
        (annotatedlocation|location <String>)|
        (annotatednotes|notes <String>)|(updatenotes <String>)|
        (annotateduser|user <String>

<BrowserFieldName> ::=
        annotatedassetid | asset |assetid |
        annotatedlocation | location |
        annotatednotes | notes |
        annotateduser | user |
        attestationcredential |
        browserpermanentid | deviceid |
        browsers |
        browserversions |
        deviceidentifiershistory |
        extensioncount |
        lastactivitytime |
        lastdeviceuser |
        lastdeviceusers |
        lastpolicyfetchtime |
        lastregistrationtime |
        laststatusreporttime |
        machinename |
        machinepolicies |
        machineextensionpolicies |
        omaharecentfetchtime |
        orgunitid | orgunitpath | org | orgunit |ou |
        osarchitecture |
        osplatform |
        osplatformversion |
        osversion |
        policycount |
        serialnumber |
        virtualdeviceid
<BrowserFieldNameList> ::= "<BrowseFieldName>(,<BrowserFieldName>)*"

<BrowserOrderByFieldName> ::=
        annotatedassetid | asset | assetid |
        annotatedlocation | location |
        annotatednotes | notes |
        annotateduser | user |
        browserpermanentid | deviceid | id |
        browserversionchannel |
        browserversionsortable |
        enrollmentdate |
        extensioncount |
        lastactivitytime | lastactivity |
        lastpolicyfetchtime | lastsync |
        lastregistrationtime | enrollmentdate |
        lastdeviceuser | lastsignedinuser |
        lastsync |
        machinename |
        orgunit | org | ou |
        osversion |
        osversionsortable |
        platformmajorversion |
        policycount
```
```
<BrowserTokenFieldName> ::=
        createtime |
        creatorid |
        customerid |
        expiretime |
        name |
        orgunitid | orgunitpath | org | orgunit | ou |
        revokerid |
        revoketime |
        state |
        token |
        tokenpermanentid |
        tokentype
<BrowserTokenFieldNameList> ::= "<BrowserTokenFieldName>(,<BrowserTokenFieldName>)*"
```
## Raw Fields

This is the list of Browser fields showing their subfields.
You enter `rawfields` like this: the field names must be entered exactly as shown.
```
rawfields "browserPermanwnrId,browsers(profiles(id,name,extensions(appType,name))),lastDeviceUsers(userName),osPlatform,osVersion"
```
```
annotatedAssetId
annotatedLocation
annotatedNotes
annotatedUser
attestationCredential
  keyRotationTime
  keyTrustLevel
  keyType
  publicKey
browserPermanentId
browserVersions
browsers
  browserVersion
  channel
  executablePath
  lastStatusReportTime
  lastPOlicyFetchTime
  pendingInstallVersion
  plugins
    pluginName
    description
    filename
  profiles
    profileName
    id
    lastStatusReportTime
    lastPolicyFetchTime
    safeBrowsingWarnings
    safeBrowsingWarningsClickThroughs
    safeBrowsingWarningsResetTime
    chromeSignedInUserEmail
    extensions
      appType
      configuredAppPolicy
      description
      disabled
      extensionId
      extensionName
      homepageUri
      icons
        size
	uri
      installType
      manifestVersion
      permissions
      version
    extensionPolicies
      extensionId
      extensionName
      policies
        policyName
        source
        value
        error
    userPolicies
      policyName
      source
      value
      error
deviceIdentifiersHistory
  deviceIdCollision
  lastDeviceIdCollisionDetectionTime
  records
    firstRecordTime
    identifiers
      hostName
      machineName
      serialNumber
    lastActivityTime
extensionCount
lastActivityTime
lastDeviceUser
lastDeviceUsers
  lastStatusReportTime
  userName
lastPolicyFetchTime
lastRegistrationTime
lastStatusReportTime
machineExtensionPolicies
  extensionId
  extensionName
  policies
    policyName
    source
    value
    error
machineName
machinePolicies
  error
  name
  source
  value
omahaRecentFetchTime
orgUnitPath
osArchitecture
osPlatform
osPlatformVersion
osVersion
policyCount
safeBrowsingClickThroughCount
serialNumber
virtualDeviceId
```

## Update Chrome browsers
There are four attributes that can be set for a browser.
```
gam update browser <BrowserDeviceEntity> <BrowserAttibute>+
```

### Example: Add a new note to existing notes

If you specify the `updatenotes <String>` option and it contains the string `#notes#`, the existing notes value will replace `#notes#`.
This requires an additional API to get the existing value.

If you have a CSV file, UpdateBrowsers.csv with two columns: browserPermanentId,notes
this command will add a new line of notes to the front of the existing notes:

```
gam csv UpdateBrowsers.csv gam update browser "~browserPermanentId" updatenotes "~~notes~~\n#notes#"
```

## Move Chrome browsers from one OU to another
```
gam move browsers ou|org|orgunit <OrgUnitPath>
        ((ids <BrowserPermanentIDList>) |
         (queries <QueryBrowserList> [querytime<String> <Time>]) |
         (browserou <OrgUnitItem>) | (browserous <OrgUnitList>) |
         <FileSelector> | <CSVFileSelector>)
        [batchsize <Integer>]
```

Batches of devices are processed to minimize the number of API calls; `batch_size` controls the number of browserPermanentIds handled in each batch
`batch_size` defaults to the value from `gam.cfg`, its maximum value is 600.

Google performs  error checking of the browserPermanentIDs, if any browserPermanentID in a batch is invalid, none of the browsers in the batch are moved.

### Example: Move Chrome browsers from one OU to another

```
gam move browsers ou /Students/2021 browserou /Students/2020
```

## Delete Chrome browsers
Deletes the data collected from a Chrome browser profile.
```
gam delete browser <BrowserPermanentID>
```

## Display Chrome browsers
```
gam info browser <BrowserPermanentID>
        (basic|full|annotated | 
         (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
         (rawfields "<BrowserFieldNameList>"))
        [formatjson]
```
Select the fields to be displayed:
* `annotated` - Display these fields: browserPermanentId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser
* `basic` - Display all fields except: browsers, lastDeviceUsers, lastStatusReportTime, machinePolicies; this is the default
* `allfields/full` - Display all fields
* `<BrowserFieldName>* [fields <BrowserFieldNameList>]` - Display a selected list of fields
* `rawfields "<BrowserFieldNameList>"` - Display a selected list of fields

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

```
gam show browsers
        ([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowser>)|(queries <QueryBrowserList>))|(select <BrowserEntity>))
        [querytime<String> <Time>]
        [orderby <BrowserOrderByFieldName> [ascending|descending]]
        (basic|allfields|full|annotated | 
         (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
         (rawfields "<BrowserFieldNameList>"))
        [formatjson]
```

Use these options to select Chrome browsers; if none are chosen, all Chrome browsers in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowser>)|(queries <QueryBrowserList>)` - Limit browsers to those that match a query
* `select <BrowserEntity>` - Select a specific set of browsers to display

Select the fields to be displayed:
* `annotated` - Display these fields: browserPermanentId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser
* `basic` - Display all fields except: browsers, lastDeviceUsers, machinePloicies; this is the default
* `allfields/full` - Display all fields
* `<BrowserFieldName>* [fields <BrowserFieldNameList>]` - Display a selected list of fields
  * Note that `ou, org and orgunit` are both command line options and field names; use `fields` to include them in the selected list of fields
* `rawfields "<BrowserFieldNameList>"` - Display a selected list of fields

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryBrowser>` and `queries <QueryBrowserList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

```
gam print browsers [todrive <ToDriveAttribute>*]
        ([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowser>)|(queries <QueryBrowserList>))|(select <BrowserEntity>))
        [querytime<String> <Time>]
        [orderby <BrowserOrderByFieldName> [ascending|descending]]
        (basic|full|allfields|annotated | 
         (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
         (rawfields "<BrowserFieldNameList>"))
        [sortheaders] [formatjson [quotechar <Character>]]
```

Use these options to select Chrome browsers; if none are chosen, all Chrome browsers in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowser>)|(queries <QueryBrowserList>)` - Limit browsers to those that match a query
* `select <BrowserEntity>` - Select a specific set of browsers to display

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryBrowser>` and `queries <QueryBrowserList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

For example, query for Chrome browsers last synced more than a year ago:
```
querytime1year -1y query 'last_policy_fetch_time<="#querytime1year#"'
```

The first column will always be browserPermanentId; the remaining field names will be sorted if `allfields`, `basic`, `full` or `sortheders` is specified;
otherwise, the remaining field names will appear in the order specified.

Select the fields to be displayed:
* `annotated` - Display these fields: browserPermanentIdId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser
* `basic` - Display all fields except: browsers, lastDeviceUsers, machinePolicies; this is the default
* `allfields/full` - Display all fields
* `<BrowserFieldName>* [fields <BrowserFieldNameList>]` - Display a selected list of fields
  * Note that `ou, org and orgunit` are both command line options and field names; use `fields` to include them in the selected list of fields
* `rawfields "<BrowserFieldNameList>"` - Display a selected list of fields

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Browser Query Searchable Fields

These are the fields that can be used in a query:
```
    annotated_asset_id
    annotated_location
    annotated_note
    annotated_user
    browser_permanent_id
    browser_version
    device_id_collision
    extension_count
    last_activity_time
    last_device_user
    last_policy_fetch_time
    last_registration_time
    last_status_report_time
    machine_name
    org_unit_id
    org_unit_path
    os_architecture
    os_platform
    os_platform_version
    os_version
    policy_count

The following functions can be used in the filter:

in_group(string): Filters browsers that belong to the specified Cloud Identity group resource name
(e.g. in_group("groups/{groupId}")).

Any of the above fields or functions can be used to specify a filter, and filtering by multiple fields
or functions is supported with AND operator.

String type, Integer type fields and enum type fields support = and : operators.

The timestamp type fields support =, <= and >= operators. Timestamps expect an RFC-3339 formatted string
enclosed in double quotes (e.g., "2012-04-21T11:30:00-04:00").

Wildcard * is only supported for machine_name, annotated_asset_id, and browser_version.

In addition, global string literal filtering without a field name is supported: a single term
(e.g., ABC) matches if any indexed string field contains ABC.
Multiple terms joined by AND or whitespace (e.g., machine AND 73 or machine 73) match browsers
where every term appears in at least one indexed string field (whereas a single quoted phrase
like "machine 73" matches the contiguous phrase within a single field).
```

### Asset ID
Enter annotated_asset_id: as the operator. For example, to match the partial Asset ID 1234, enter the following:

`gam print browsers query "annotated_asset_id:1234*"`

### Location
Enter annotated_location: as the operator. For example, to match browsers with Seattle in the location:

`gam print browsers query "annotated_location:Seattle"`

### Notes
Enter annotated_note: as the operator. For example, to match browsers with John in the notes:

`gam print browsers query "annotated_note:John"`

### Times
```
<Time> ::=
        <Year>-<Month>-<Day>T<Hour>:<Minute>:<Second>(Z|(+|-(<Hour>:<Minute>)))
* `field = "<Time>"` - A single time
* `field >= "<Time>" and field <= "<Time>"` - A date range
* `field <= "<Time>"` - All dates on or before a date
* `field >= "<Time>"` - All dates on or after a date
```
Print information about Chrome browsers synced more than 1 year  ago:

```
gam print browsers querytime1year -1y query 'last_policy_fetch_time<="#querytime1year#"'
```

Print information about Chrome browsers synced in the last 30 days:

```
gam print browsers querytime30d -30d query 'last_policy_fetch_time>="#querytime30d#"'
```

Print information about Chrome browsers synced between 45 days ago and 30 days ago:

```
gam print browsers querytime45d -45d querytime30d -30d query 'last_policy_fetch_time>="#querytime45d#" and last_policy_fetch_time<="querytime30d#"'
```

## Create Chrome browser enrollment tokens
Create a browser enrollment token.
```
gam create browsertoken
        [ou|org|orgunit|browserou <OrgUnitPath>]
        [enrollmenttokenid <String>]
        [formatjson]
```
By default, the enrollment token is created for the root OU; use `ou|org|orgunit|browserou <OrgUnitPath>`
to create the token for a specific OU.

By default, Gam displays the created token as an indented list of keys and values:
- `formatjson` - Display the token in JSON format.

## Revoke Chrome browser enrollment tokens
An enrollment token is revoked by referencing its `tokenPermanentId` which can be obtained
from `gam show|print browsertokens`.
```
gam revoke browsertoken <TokenPermanentID>

```
## Display Chrome browser enrollment tokens
```
gam info browsertoken <TokenPermanentID>
        <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
        [formatjson]
```
Select the fields to be displayed:
* Display all fields; this is the default
* `<BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]` - Display a selected list of fields

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

```
gam show browsertokens
        ([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
        [querytime<String> <Time>]
        <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
        [formatjson]
```
Use these options to select Chrome browsers; if none are chosen, all Chrome browser tokens in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowserToken>)|(queries <QueryBrowserTokenList>)` - Limit browser tokens to those that match a query

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryBrowserToken>` and `queries <QueryBrowserTokenList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

Select the fields to be displayed:
* Display all fields; this is the default
* `<BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]` - Display a selected list of fields

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

```
gam print browsertokens [todrive <ToDriveAttribute>*]
        ([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
        [querytime<String> <Time>]
        <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
        [formatjson [quotechar <Character>]]
```
Use these options to select Chrome browsers; if none are chosen, all Chrome browser tokens in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowserToken>)|(queries <QueryBrowserTokenList>)` - Limit browser tokens to those that match a query

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryBrowserToken>` and `queries <QueryBrowserTokenList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

Select the fields to be displayed:
* Display all fields; this is the default
* `<BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]` - Display a selected list of fields

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Token Query Searchable Fields

```
device_type:<String> - Currently only CHROME_BROWSER is supported

token_state:<String> - Supported values: ACTIVE, EXPIRED, REVOKED

org_unit_path:<String> - The full path of the org unit, such as /Montreal/Sales

org_unit_id:<String> - The obfuscated id of the org unit, not the full path.
```