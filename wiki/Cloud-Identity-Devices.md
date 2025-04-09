# Cloud Identity Devices
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [Create a company device](#create-a-company-device)
- [Delete devices](#delete-devices)
- [Wipe devices](#wipe-devices)
- [Perform device actions](#perform-device-actions)
- [Synchronize devices](#synchronize-devices)
- [Display devices](#display-devices)
- [Print devices](#print-devices)
- [Display device counts](#display-device-counts)
- [Approve or block device users](#approve-or-block-device-users)
- [Delete device users](#delete-device-users)
- [Wipe device users](#wipe-device-users)
- [Perform device user actions](#perform-device-user-actions)
- [Display device users](#display-device-users)
- [Display device user counts](#display-device-user-counts)
- [Print device users](#print-device-users)
- [Display device user client state](#display-device-user-client-state)
- [Update device user client state](#update-device-user-client-state)

## API documentation
* [Cloud Identity API - Devices](https://cloud.google.com/identity/docs/reference/rest/v1/devices)
* [Cloud Identity API - Device Users](https://cloud.google.com/identity/docs/reference/rest/v1/devices.deviceUsers)
* [Cloud Identity API - Device User Client States](https://cloud.google.com/identity/docs/reference/rest/v1/devices.deviceUsers.clientStates)
* [Endpoint Verification](https://cloud.google.com/endpoint-verification/docs/overview)

## Query documentation
* [Filters](https://support.google.com/a/answer/7549103)
* [Device Search Fields](https://developers.google.com/admin-sdk/directory/v1/search-operators)

## Definitions
```
<AssetTag> ::= <String>
<AssetTagList> ::= "<AssetTag>(,<AssetTag>)*"
<QueryDevice> ::= <String>
        See: https://support.google.com/a/answer/7549103
<QueryDeviceList> ::= "<QueryDevice>(,<QueryDevice>)*"
<DeviceID> ::= devices/<String>
<DeviceIDList> ::= "<DeviceID>(,<DeviceID>)*"
<DeviceEntity> ::=
        <DeviceIDList> | devicesn <String> |
        (query:<QueryDevice>)|(query <QueryDevice>)
<DeviceType> ::= android|chrome_os|google_sync|linux|mac_os|windows
<DeviceUserID> ::= devices/<String>/deviceUsers/<String>
<DeviceUserEntity> ::=
        <DeviceUserIDList> |
        (query:<QueryDevice>)|(query <QueryDevice>)

<DeviceFieldName> ::=
        androidspecificattributes|
        assettag|
        basebandversion|
        bootloaderversion|
        brand|
        buildnumber|
        compromisedstate|
        createtime|
        deviceid|
        devicetype|
        enableddeveloperoptions|
        enabledusbdebugging|
        endpointverificationspecificattributes|
        encryptionstate|
        hostname|
        imei|
        kernelversion|
        lastsynctime|
        managementstate|
        manufacturer|
        meid|
        model|
        name|
        networkoperator|
        osversion|
        otheraccounts|
        ownertype|
        releaseversion|
        securitypatchtime|
        serialnumber|
        unifieddeviceid|
        wifimacaddresses
<DeviceFieldNameList> ::= "<DeviceFieldName>(,<DeviceFieldName>)*"

<DeviceAction> ::=
        cancelwipe|
        wipe

<DeviceUserFieldName> ::=
        compromisedstate|
        createtime|
        firstsynctime|
        languagecode|
        lastsynctime|
        managementstate|
        name|
        passwordstate|
        useragent|
        useremail
<DeviceUserFieldNameList> ::= "<DeviceUserFieldName>(,<DeviceUserFieldName>)*"

<DeviceOrderbyFieldName> ::= 
        createtime|devicetype|lastsynctime|model|osversion|serialnumber

<DeviceUserAction> ::=
        approve|
        block|
        cancelwipe|
        wipe

```
## Create a company device
Adds a new device to the Google company-owned inventory. Once a user is assigned and enrolled on the device the device will be considered company-owned for management purposes.
The device will also register as company-owned with Google services like [Context-Aware Access (CAA)](https://support.google.com/a/answer/9275380).
```
gam create device serialnumber <String> devicetype <DeviceType> [assettag <String>]
```
Arguments `serialnumber <String>` and `devicetype <DeviceType>` are required; you can optionally specify `assettag <String>`.

## Delete devices
Delete a device from appearing in the Admin console, stop syncing for the device user.
No user data should be removed.
```
gam delete device <DeviceEntity> [doit]
```
If `<DeviceEntity>` uses a query, the `doit` option must be used to enable execution.

## Wipe devices
Wiping a device performs a factory reset, all device data is removed.
```
gam cancelwipe device <DeviceEntity> [doit]
gam wipe device <DeviceEntity> [removeresetlock] [doit]
```
If `<DeviceEntity>` uses a query, the `doit` option must be used to enable execution.

Specifying `removeresetlock` will remove the account lock on the Android or iOS device.
This lock is enabled by default and requires the existing device user to log in after the wipe in order to unlock the device.
* See: https://support.google.com/android/answer/9459346

## Perform device actions
This is an alternative form of the above commands
```
gam update device <DeviceEntity> action <DeviceAction> [removeresetlock] [doit]
```
If `<DeviceEntity>` uses a query, the `doit` option must be used to enable execution.

Specifying `removeresetlock` when `<DeviceAction>` is `wipe` will remove the account lock on the Android or iOS device.
This lock is enabled by default and requires the existing device user to log in after the wipe in order to unlock the device.
* See: https://support.google.com/android/answer/9459346

## Synchronize devices
This command generates a list of your current company devices, either a complete list
or a subset based on a query. A CSV file is read to generate another list of devices.

At a minimum, two values are required for devices in the CSV file list; a device type and a serial number.
For the device type, you can either specify a static device type or specify the column in the CSV file that contains a device type.
* `static_devicetype <DeviceType>` - A fixed device type
* `devicetype_column <String>` - The name of the column containing device types; if not specified, `deviceType` is used

For the serial number, you must specify the column in the CSV file that contains a serial number.
* `serialnumber_column <String>` - The name of the column containing serial numbers; if not specified, `serialNumber` is used

You can optionally specify the column in the CSV file that contains an asset tag.
* `assettag_column <String>` - The name of the column containing asset tags; the typical value is `assetTag`

These two/three columns are used to match current company devices against the CSV file devices.
* Devices in the CSV device list will be created if they are not the the current company device list.
* Devices in the current company device list that are not in the CSV device list will have an optional operation performed on them.
  * `unassigned_missing_action delete|wipe|none` - Perform this operation if the company device has never been assigned; default action is `delete`
  * `assigned_missing_action delete|wipe|none` - Perform this operation if the company device has been assigned; default action is `none`

If `preview` is specified, the operations that would be performed are previewed but are not performed; use this to test.
```
gam sync devices
        [(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
        csvfile <FileName>
        (devicetype_column <String>)|(static_devicetype <DeviceType>)
        (serialnumber_column <String>)
        [assettag_column <String>]
        [unassigned_missing_action delete|wipe|none]
        [assigned_missing_action delete|wipe|none]
        [preview]
```

## Display devices
```
gam info device <DeviceEntity>
        <DeviceFieldName>* [fields <DeviceFieldNameList>] [userfields <DeviceUserFieldNameList>]
        [nodeviceusers]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Print devices
```
gam print devices [todrive <ToDriveAttribute>*]
        [(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
        <DeviceFieldName>* [fields <DeviceFieldNameList>] [userfields <DeviceUserFieldNameList>]
        [orderby <DeviceOrderByFieldName> [ascending|descending]]
        [all|company|personal|nocompanydevices|nopersonaldevices]
        [nodeviceusers]
        [formatjson [quotechar <Character>]]
```
By default, all devices are displayed; use the query options to limit the display.

To AND query terms, put all of your terms in one query:
```
gam print devices query "manufacturer:Meizu os:Android 7.0.0"
```
To OR query terms, put the terms im multiple queries:
```
gam print devices queries "'model:iPhone 6','model:samsung'"
```
Select the view of devices to display:
* `all` - Company and personal devices; this is the default
* `company|nopersonaldevices` - Company devices
* `personal|nocompanydevices` - Personal devices

By default, Gam makes additional API calls to display the device users for the devices;
use `nodeviceuser` to suppress making the additional calls.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display device counts
Display the number of devices.
```
gam print devices
        [(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
        [all|company|personal|nocompanydevices|nopersonaldevices]
        showitemcountonly
```
Example
```
$ gam print devices queries "'model:Mac'" showitemcountonly
Getting all Devices that match query (model:Mac), may take some time on a large Google Workspace Account...
Got 100 Devices...
Got 200 Devices...
Got 300 Devices...
...
Got 900 Devices...
Got 995 Devices...
Got 995 Devices...
995
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print devices queries "'model:Mac'" showitemcountonly)
Windows PowerShell
count = & gam print devices queries "'model:Mac'" showitemcountonly
```

## Approve or block device users
Approve or block user profiles on a device.
```
gam approve deviceuser <DeviceUserEntity> [doit]
gam block deviceuser <DeviceUserEntity> [doit]
```
If `<DeviceUserEntity>` uses a query, the `doit` option must be used to enable execution.

## Delete device users
Delete a device user from appearing in the Admin console, stop syncing for the device user.
No user data should be removed.
```
gam delete deviceuser <DeviceUserEntity> [doit]
```
If `<DeviceUserEntity>` uses a query, the `doit` option must be used to enable execution.

## Wipe device users
Wipe a device user profile from a device.
In the case of Android for Work, the work profile will be removed but the personal profile left alone.
```
gam wipe deviceuser <DeviceUserEntity> [doit]
gam cancelwipe deviceuser <DeviceUserEntity> [doit]
```
If `<DeviceUserEntity>` uses a query, the `doit` option must be used to enable execution.

## Perform device user actions
This is an alternative form of the above commands.
```
gam update deviceuser <DeviceUserEntity> action <DeviceUserAction> [doit]
```
If `<DeviceUserEntity>` uses a query, the `doit` option must be used to enable execution.

## Display device users
```
gam info deviceuser <DeviceUserEntity>
        <DeviceUserFieldName>* [fields <DeviceUserFieldNameList>]
        [formatjson]
```
## Print device users
```
gam print deviceusers [todrive <ToDriveAttribute>*]
        [select <DeviceID>]
        [(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
        <DeviceUserFieldName>* [fields <DeviceUserFieldNameList>]
        [orderby <DeviceOrderByFieldName> [ascending|descending]]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays device users for all devices;
* `select <DeviceID>` - Display users for a specific device
* `(query <QueryDevice>)|(queries <QueryDeviceList>)` - Display users that match queries.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display device user counts
Display the number of device users.
```
gam print deviceusers [todrive <ToDriveAttribute>*]
        [select <DeviceID>]
        [(query <QueryDevice>)|(queries <QueryDeviceList>) (querytime<String> <Time>)*]
        showitemcountonly
```
Example
```
$ gam print deviceusers queries "'model:Mac'" showitemcountonly
Getting all Device Users that match query (model:Mac), may take some time on a large Google Workspace Account...
Got 20 Device Users...
Got 40 Device Users...
Got 60 Device Users...
...
Got 980 Device Users...
Got 995 Device Users...
Got 995 Device Users...
995
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print deviceusers queries "'model:Mac'" showitemcountonly)
Windows PowerShell
count = & gam print deviceusers queries "'model:Mac'" showitemcountonly
```


## Display device user client state
```
gam info deviceuserstate <DeviceUserEntity> [clientid <String>] 
```

## Update device user client state
The API that supports this command is in beta mode. In particular, setting `assettags` and `customvalues`
works if you set the values once; each additional time you set values they are added to the existing values
and they is no way at the moment to clear values.
```
gam update deviceuserstate <DeviceUserEntity> [clientid <String>] 
        [customid <String>] [assettags clear|<AssetTagList>]
        [compliantstate|compliancestate compliant|noncompliant] [managedstate clear|managed|unmanaged]
        [healthscore very_poor|poor|neutral|good|very_good] [scorereason clear|<String>]
        (customvalue (bool|boolean <Boolean>)|(number <Integer>)|(string <String>))*
```
