# Chrome Browser Cloud Management
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [Raw Fields](#raw-fields)
- [Manage Chrome browsers](#manage-chrome-browsers)
  - [Update Chrome browsers](#update-chrome-browsers)
    - [Example: Add a new note to existing notes](#example-add-a-new-note-to-existing-notes)
  - [Move Chrome browsers from one OU to another](#move-chrome-browsers-from-one-ou-to-another)
  - [Delete Chrome browsers](#delete-chrome-browsers)
- [Display Chrome browsers](#display-chrome-browsers)
  - [Examples](#examples)
- [Browser Query Searchable Fields](#browser-query-searchable-fields)
- [Manage Chrome browser enrollment tokens](#manage-chrome-browser-enrollment-tokens)
- [Display Chrome browser enrollment tokens](#display-chrome-browser-enrollment-tokens)

## API documentation
* [Chrome Enterprise Core API](https://support.google.com/chrome/a/answer/9681204)
* [Chrome Browser Enrollment Token API](https://support.google.com/chrome/a/answer/9949706)

## Query documentation
* [Search Chrome Browser Devices](https://support.google.com/chrome/a/answer/9681204#retrieve_all_chrome_devices_for_an_account)

## Definitions
* [`<CrOSTypeEntity>`](Collections-of-ChromeOS-Devices)

```
<BrowserTokenPermanentID> ::= <String>
<OrgUnitPath> ::= /|(/<String)+
<QueryBrowser> ::= <String> See: https://support.google.com/chrome/a/answer/9681204#retrieve_all_chrome_devices_for_an_account
<QueryBrowserList> ::= "<QueryBrowser>(,<QueryBrowser>)*"
<QueryBrowserToken> ::= <String> https://support.google.com/chrome/a/answer/9949706, scroll down to Filter Query Language
<QueryBrowserTokenList> ::= "<QueryBrowserToken>(,<QueryBrowserToken>)*"
<DeviceID> ::= <String>
<DeviceIDList> ::= "<DeviceID>(,<DeviceID>)*"

<BrowserEntity> ::=
        <DeviceIDList> | 
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
        annotatedassetid|asset|assetid|
        annotatedlocation|location|
        annotatednotes|notes|
        annotateduser|user|
        browsers|
        browserversions|
        deviceid|
        deviceidentifiershistory|
        extensioncount|
        lastactivitytime|
        lastdeviceuser|
        lastdeviceusers|
        lastpolicyfetchtime|
        lastregistrationtime|
        laststatusreporttime|
        machinename|
        machinepolicies|
        orgunitpath|org|orgunit|ou|
        osarchitecture|
        osplatform|
        osplatformversion|
        osversion|
        policycount|
        safebrowsingclickthroughcount|
        serialnumber|
        virtualdeviceid
<BrowserFieldNameList> ::= "<BrowseFieldName>(,<BrowserFieldName>)*"

<BrowserOrderByFieldName> ::=
        annotatedassetid|assetassetid|
        annotatedlocation|location|
        annotatednotes|notes|
        annotateduser|user|
        browserversionchannel|
        browserversionsortable|
        deviceid|id|
        enrollmentdate|
        extensioncount|
        lastactivity|
        lastsignedinuser|
        lastsync|
        machinename|
        orgunit|ou|org|
        osversion|
        osversionsortable|
        platformmajorversion|
        policycount
```
```
<BrowserTokenFieldName> ::=
        createtime|
        creatorid|
        customerid|
        expiretime|
        org|
        orgunit|
        orgunitpath|
        revoketime|
        revokerid|
        state|
        token|
        tokenpermanentid
<BrowserTokenFieldNameList> ::= "<BrowseTokenFieldName>(,<BrowserTokenFieldName>)*"
```
## Raw Fields

This is the list of Browser fields showing their subfields.
You enter `rawfields` like this: the field names must be entered exactly as shown.
```
rawfields "deviceId,browsers(profiles(id,name,extensions(appType,name))),lastDeviceUsers(userName),osPlatform,osVersion"
```
```
annotatedAssetId
annotatedLocation
annotatedNotes
annotatedUser
deviceId
browserVersions
browsers
  browserVersion
  channel
  executablePath
  lastStatusReportTime
  pendingInstallVersion
  profiles
    id
    chromeSignedInUserEmail
    lastPolicyFetchTime
    lastStatusReportTime
    name
    extensions
      appType
      description
      extensionId
      homepageUrl
      installType
      manifestVersion
      name
      permissions
      version
deviceIdentifiersHistory
  records
    firstRecordTime
    identifiers
      machineName
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
machineName
machinePolicies
  error
  name
  source
  value
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

## Manage Chrome browsers
## Update Chrome browsers
There are four attributes that can be set for a browser.
```
gam update browser <BrowserDeviceEntity> <BrowserAttibute>+
```

### Example: Add a new note to existing notes

If you specify the `updatenotes <String>` option and it contains the string `#notes#`, the existing notes value will replace `#notes#`.
This requires an additional API to get the existing value.

If you have a CSV file, UpdateBrowsers.csv with two columns: deviceId,notes
this command will add a new line of notes to the front of the existing notes:

```
gam csv UpdateBrowsers.csv gam update browser "~deviceId" updatenotes "~~notes~~\n#notes#"
```

## Move Chrome browsers from one OU to another
```
gam move browsers ou|org|orgunit <OrgUnitPath>
        ((ids <DeviceIDList>) |
         (queries <QueryBrowserList> [querytime<String> <Time>]) |
         (browserou <OrgUnitItem>) | (browserous <OrgUnitList>) |
         <FileSelector> | <CSVFileSelector>)
        [batchsize <Integer>]
```

Batches of devices are processed to minimize the number of API calls; `batch_size` controls the number of deviceIds handled in each batch
`batch_size` defaults to the value from `gam.cfg`, its maximum value is 600.

Google performs  error checking of the browser  deviceIDs, if any deviceID in a batch is invalid, none of the browsers in the batch are moved.

### Example: Move Chrome browsers from one OU to another

```
gam move browsers ou /Students/2021 browserou /Students/2020
```

## Delete Chrome browsers
Deletes a browser; the browser will be removed from Google's admin console and no longer sync policy or reporting. However, existing policies will still be applied until the device registration and dm tokens are removed.
```
gam delete browser <BrowserDeviceEntity>
```

## Display Chrome browsers
```
gam info browser <BrowserEntity>
        (basic|full|annotated | 
         (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
         (rawfields "<BrowserFieldNameList>"))
        [formatjson]
```
Select the fields to be displayed:
* `annotated` - Display these fields: deviceId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser
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
        (basic|full|annotated | 
         (<BrowserFieldName>* [fields <BrowserFieldNameList>]) |
         (rawfields "<BrowserFieldNameList>"))
        [formatjson]
```

Use these options to select Chrome browsers; if none are chosen, all Chrome browsers in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowser>)|(queries <QueryBrowserList>)` - Limit browsers to those that match a query
* `select <BrowserEntity>` - Select a specific set of browsers to display

Select the fields to be displayed:
* `annotated` - Display these fields: deviceId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser
* `basic` - Display all fields except: browsers, lastDeviceUsers, lastStatusReportTime, machinePloicies; this is the default
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
        (basic|full|annotated | 
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
querytime1year -1y query "sync:..#querytime1year#"
```

The first column will always be deviceId; the remaining field names will be sorted if `allfields`, `basic`, `full` or `sortheders` is specified;
otherwise, the remaining field names will appear in the order specified.

Select the fields to be displayed:
* `annotated` - Display these fields: deviceId,annotatedAssetId,annotatedLocation,annotatedNotes,annotatedUser
* `basic` - Display all fields except: browsers, lastDeviceUsers, lastStatusReportTime, machinePloicies; this is the default
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

### Examples

Print information about Chrome browsers synced more than 30 days ago:

```
gam print browsers query "sync:..#querytime1#" querytime1 -30d
```

Print information about Chrome browsers synced in the last 30 days:

```
gam print browsers query "sync:#querytime1#.." querytime1 -30d
```

Print information about Chrome browsers synced between 45 days ago and 30 days ago:

```
gam print browsers query "sync:#querytime1#..#querytime2#" querytime1 -45d querytime2 -30d
```

## Browser Query Searchable Fields

These are the fields that can be used in a query:
```
Field             Description
arch              The CPU architecture for the Chrome browser device. (e.g. x86_64)
asset_id          The annotated asset ID for the Chrome browser device.
browser_version   A reported Chrome browser installed on the Chrome browser device (e.g. 73)
enrollment_token  The enrollment token used to register the Chrome browser device.
last_activity     The last time the Chrome browser device has shown activity (policy fetch or reporting).
location          The annotated location for the Chrome browser device.
machine_name      The machine name for the Chrome browser device.
machine_user      The last reported user of the Chrome browser device.
note              The annotated note for the Chrome browser device.
num_extensions    The number of extensions reported by the Chrome browser device.
num_policies      The number of policies reported by the Chrome browser device.
os                The combine OS platform and major OS version for the Chrome browser device (e.g. "Windows 10")
os_platform       The OS platform for the Chrome browser device. (e.g. Windows)
os_version        The OS version for the chrome browser device. (e.g. 10.0.16299.904)
register          The registration time for the Chrome browser device.
report            The last report time for the Chrome browser device
sync              The last policy sync time for the Chrome browser device.
user              The annotated user for the Chrome browser device.
```

For fields that accept time (register, report, sync, last_activity) the time format is YYYY-MM-DDThh:mm:ss (e.g. 2020-01-01T12:00:00). You may also specify open or closed ranges for the time:
```
datetime           exactly on the given date or time, e.g., 2011-03-23 2011-04-26T14:23:05

datetime..datetime within (inclusive) the given interval of date or time, e.g., 2011-03-23..2011-04-26

datetime..         on or after the given date or time; e.g., 2011-04-26T14:23:05..

..datetime         on or before the given date or time; e.g., ..2011-04-26T14:23:05
```
To search within a specific field only (for example, to search for a specific user), you can enter an operator followed by an argument -- for example, `user:jsmith`. You can use single words or quoted lists of words as an argument when running an operator query.

To run an operator query, follow these guidelines for each field:

### User
Enter user: as the operator. For example, to match the name Joe, but not Joey, enter the following:

`gam print browsers query "user:joe"`

To match the name Tom Sawyer or A. Tom Sawyer, but not Tom A. Sawyer, enter with quotation marks:

`gam print browsers query "user:'tom sawyer'"`

### Location
Enter location: as the operator. For example, to match Seattle, enter the following:

`gam print browsers query "location:seattle"`

Notes
Enter note: as the operator. For example, to match loaned from John, enter the following with quotation marks:

`gam print browsers query "note:'loaned from john'"`

### Register
This field is not displayed on the Chrome OS settings page. However, you can search for devices that were registered on a given date, or within a given time range.

Enter register: as the operator, and enter a date and time (or time range) as the argument. For example, to search for all devices registered on April 15, 2020, enter the following:

`gam print browsers query "register:2020-04-15"`

For additional examples using dates, times, and ranges, see "Format for date searches" below.

### Last Sync
Enter sync: as the operator and a date or time range as the argument. For example, to search for all devices that were last synced with policy settings on April 15, 2020, enter the following:

`gam print browsers query "sync:2020-04-15"`

For additional examples using dates, times, and ranges, see "Format for date searches" below.

### Format for date searches
* `YYYY-MM-DD` - A single date
* `YYYY-MM-DD..YYYY-MM-DD` - A date range
* `..YYYY-MM-DD` - All dates on or before a date
* `YYYY-MM-DD..` - All dates on or after a date

### Asset ID
Enter asset_id: as the operator. For example, to match the partial Asset ID 1234, enter the following:

`gam print browsers query "asset_id:1234"`

## Manage Chrome browser enrollment tokens
Create a browser enrollment token. The Google API that supports this call always returns an error.
```
gam create browsertoken
        [ou|org|orgunit|browserou <OrgUnitPath>] [expire|expires <Time>]
        [formatjson]
```
By default, the enrollment token is created for the root OU; use `ou|org|orgunit|browserou <OrgUnitPath>`
to create the token for a specific OU.

By default, Gam displays the created token as an indented list of keys and values:
- `formatjson` - Display the token in JSON format.

Revoke a browser enrollment token.
An enrollment token is revoked by referencing its `tokenPermanentId` which can be obtained
from `gam show|print browsertokens`.
```
gam revoke browsertoken <BrowserTokenPermanentID>

```
## Display Chrome browser enrollment tokens
```
gam show browsertokens
        ([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
        [querytime<String> <Time>]
        [orderby <BrowserTokenFieldName> [ascending|descending]]
        [allfields] <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
        [formatjson]
```
Use these options to select Chrome browsers; if none are chosen, all Chrome browsers in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowserToken>)|(queries <QueryBrowserTokenList>)` - Limit browsers  to those that match a query

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryBrowserToken>` and `queries <QueryBrowserTokenList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

Select the fields to be displayed:
* `allfields` - Display all fields; this is the default
* `<BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]` - Displaya selected list of fields

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

```
gam print browsertokens [todrive <ToDriveAttribute>*]
        ([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
        [querytime<String> <Time>]
        [orderby <BrowserTokenFieldName> [ascending|descending]]
        [allfields] <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
        [sortheaders] [formatjson [quotechar <Character>]]
```
Use these options to select Chrome browsers; if none are chosen, all Chrome browsers in the account are selected:
* `ou|org|orgunit|browserou <OrgUnitPath>` - Limit browsers to those in the specified OU; this option can be used in conjunction with query
* `(query <QueryBrowserToken>)|(queries <QueryBrowserTokenList>)` - Limit browser s to those that match a query

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryBrowserToken>` and `queries <QueryBrowserTokenList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

The first column will always be deviceId; the remaining field names will be sorted if `allfields`, `basic`, `full` or `sortheders` is specified;
otherwise, the remaining field names will appear in the order specified.

Select the fields to be displayed:
* `allfields` - Display all fields; this is the default
* `<BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]` - Displaya selected list of fields

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
