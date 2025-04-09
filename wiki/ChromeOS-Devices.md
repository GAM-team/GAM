# ChromeOS Devices
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [CrOS Query Searchable Fields](#cros-query-searchable-fields)
- [ChromeOS device update OU error handling](#chromeos-device-update-ou-error-handling)
- [Manage ChromeOS devices](#manage-chromeos-devices)
  - [Example: Move CrOS devices from one OU to another](#example-move-cros-devices-from-one-ou-to-another)
  - [Example: Add a new note to existing notes](#example-add-a-new-note-to-existing-notes)
- [Add ChromeOS devices to an organizational unit](#add-chromeos-devices-to-an-organizational-unit)
  - [Example: Add ChromeOS devices to a single OU](#example-add-chromeos-devices-to-a-single-ou)
  - [Example: Add ChromeOS devices to multiple OUs](#example-add-chromeos-devices-to-multiple-ous)
- [Action ChromeOS devices](#action-chromeos-devices)
- [Send remote commands to ChromeOS devices](#send-remote-commands-to-chromeos-devices)
  - [Action Examples](#action-examples)
- [ChromeOS device lists](#chromeos-device-lists)
- [Display information about ChromeOS devices](#display-information-about-chromeos-devices)
- [Print ChromeOS devices](#print-chromeos-devices)
  - [Print no header row and deviceId for specified CrOS devices](#print-no-header-row-and-deviceid-for-specified-cros-devices)
  - [Print a header row and fields for selected CrOS devices](#print-a-header-row-and-fields-for-selected-cros-devices)
  - [Print a header row and fields for specified CrOS devices](#print-a-header-row-and-fields-for-specified-cros-devices)
  - [Display Examples](#display-examples)
  - [Display CrOS device counts](#display-cros-device-counts)
- [Print ChromeOS device activity](#print-chromeos-device-activity)
  - [Print a header row and activity for selected CrOS devices](#print-a-header-row-and-activity-for-selected-cros-devices)
  - [Print a header row and activity for specified CrOS devices](#print-a-header-row-and-activity-for-specified-cros-devices)
- [Download a ChromeOS device file](#download-a-chromeos-device-file)
  - [Download Examples](#download-examples)
- [Display ChromeOS telemetry data](#display-chromeos-telemetry-data)
- [Check ChromeOS device serial number validity](#check-chromeos-device-serial-number-validity)

## API documentation
* [Directory API ChromeOS Devices](https://developers.google.com/admin-sdk/directory/reference/rest/v1/chromeosdevices)
* [Chrome Management API - Device Telemetry](https://developers.google.com/chrome/management/reference/rest/v1/customers.telemetry.devices)

## Query documentation
* [Search ChromeOS Devices](https://developers.google.com/admin-sdk/directory/v1/list-query-operators)
* [View ChromeOS Device List and Details](https://support.google.com/chrome/a/answer/1698333)

Undocumented API query terms.
```
<QueryDate> ::=
        YYYY-MM-DD    # Specific date
        ..YYYY-MM-DD  # Before a date
        YYYY-MM-DD..  # After a date
        YYYY-MM-DD..YYYY-MM-DD  # Range of dates
        
aue:<QueryDate>
compliance:compliant|pending_update|not_compliant
last_user_activity:<QueryDate>
policy_status:true|false
public_model_name:<String>
update_status:default_os_up_to_date|pending_update|os_image_download_not_started|os_image_download_in_progress|os_update_need_reboot
```
## Notes

To use the `crostelemetry` commands you must authorize an additional scope:

* `Chrome Management API - Telemetry read only`
```
gam oauth create
```

Many commands come in two forms:
```
gam <CrOSTypeEntity> <Command> ...
gam <Command> cros <CrOSEntity> ...
```
The first form allows more powerful selection of devices with `<CrOSTypeEntity>`.

The second form is backwards compatible with Legacy GAM and selection with `<CrOSEntity>` is limited.

## Definitions
* [`<CrOSTypeEntity>`](Collections-of-ChromeOS-Devices)
 
```
<OrgUnitPath> ::= /|(/<String)+
<QueryCrOS> ::= <String> See: https://support.google.com/chrome/a/answer/1698333
<CommandID> ::= <String>
<CrOSID> ::= <String>
<CrOSIDList> ::= "<CrOSID>(,<CrOSID>)*"
<SerialNumber> ::= <String>
<SerialNumberList> ::= "<SerialNumber>(,<SerialNumber>)*"
<SerialNumberEntity> ::=
        <SerialNumberList> | <FileSelector> | <CSVFileSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<CrOSEntity> ::=
        <CrOSIDList> | (cros_sn <SerialNumberList>) |
        (query:<QueryCrOS>)|(query:orgunitpath:<OrgUnitPath>)|(query <QueryCrOS>)

<CrOSAttribute> ::=
        (asset|assetid|tag <String>)|
        (location <String>)|
        (notes <String>)|(updatenotes <String>)|
        (org|ou <OrgUnitPath>)|
        (user <Name>)

<CrOSFieldName> ::=
        activetimeranges|timeranges|
        annotatedassetid|assetid|asset|
        annotatedlocation|location|
        annotateduser|user|
        autoupdateexpiration|
        autoupdatethrough|
        backlightinfo|
        bootmode|
        cpuinfo|
        cpustatusreports|
        deprovisionreason|
        devicefiles|
        deviceid|
        devicelicensetype|
        diskvolumereports|
        dockmacaddress|
        ethernetmacaddress|
        ethernetmacaddress0|
        extendedsupporteligible|
        extendedsupportstart|
        extendedsupportenabled|
        firmwareversion|
        firstenrollmenttime|
        lastdeprovisiontimestamp|
        lastenrollmenttime|
        lastknownnetwork|
        lastsync|
        macaddress|
        manufacturedate|
        meid|
        model|
        notes|
        ordernumber|
        orgunitid|
        orgunitpath|org|ou|
        osupdatestatus|
        osversion|
        platformversion|
        recentusers|
        screenshotfiles|
        serialnumber|
        status|
        supportenddate|
        systemramfreereports|
        systemramtotal|
        tpmversioninfo|
        willautorenew
<CrOSFieldNameList> ::= "<CrOSFieldName>(,<CrOSFieldName>)*"

<CrOSListFieldName> ::=
        activetimeranges|timeranges|times|
        cpustatusreports|
        devicefiles|files|
        diskvolumereports|
        lastknownnetwork|
        recentusers|users|
        screenshotfiles|
        systemramfreereports
<CrOSListFieldNameList> ::= "<CrOSListFieldName>(,<CrOSListFieldName>)*"

<CrOSOrderByFieldName> ::=
        lastsync|location|notes|serialnumber|status|supportenddate|user
```
```
<CrOSAction> ::=
        deprovision_different_model_replace|
        deprovision_different_model_replacement|
        deprovision_retiring_device|
        deprovision_same_model_replace|
        deprovision_same_model_replacement|
        deprovision_upgrade_transfer|
        disable|
        reenable|
        pre_provisioned_disable|
        pre_provisioned_reenable

<CrOSCommand>
        reboot|
        remote_powerwash|
        set_volume <0-100>|
        wipe_users|
        take_a_screenshot
```
```
<CrOSActivityListFieldName> ::=
        activetimeranges|timeranges|times|
        devicefiles|files|
        recentusers|users
<CrOSActivityListFieldNameList> ::= "<CrOSActivityListFieldName>(,<CrOSActivityListFieldName>)*"

<CrOSTelemetryFieldName> ::=
        audiostatusreport|
        batteryinfo|
        batterystatusreport|
        bootPerformancereport|
        cpuinfo|
        cpustatusreport|
        customer|
        deviceid|
        graphicsinfo|
        graphicsstatusreport|
        memoryinfo|
        memorystatusreport|
        name|
        networkdiagnosticsreport|
        networkinfo|
        networkstatusreport|
        orgunitid|
        osupdatestatus|
        peripheralsreport|
        serialnumber|
        storageinfo|
        storagestatusreport|
        thunderboltinfo
<CrOSTelemetryFieldNameList> ::= "<CrOSTelemetryFieldName>(,<CrOSTelemetryFieldName>)*"

<CrOSTelemetryListFieldName> ::=
        audiostatusreport|
        batteryinfo|
        batterystatusreport|
        bootperformancereport|
        cpuinfo|
        cpustatusreport|
        graphicsstatusreport|
        memorystatusreport|
        networkdiagnosticsreport|
        networkstatusreport|
        osupdatestatus|
        peripheralsreport|
        storagestatusreport|
        thunderboltinfo
<CrOSTelemetryListFieldNameList> ::= "<CrOSTelemetryListFieldName>(,<CrOSTelemetryLIstFieldName>)*"
```

For `<OrgUnitEntity>`, see: [Collections of Items](Collections-of-Items)

For `<UserTypeEntity>`, see: [Collections of Users](Collections-Of-Users)

For `<CrOSTypeEntity>`, see: [Collections of ChromeOS Devices](Collections-of-ChromeOS-Devices)

## CrOS Query Searchable Fields

To search within a specific field only (for example, to search for a specific user), you can enter an operator followed by an argument -- for example, `user:jsmith`. You can use single words or quoted lists of words as an argument when running an operator query.

To run an operator query, follow these guidelines for each field:

### Serial Number
Enter `id:` as the operator. For example, if you are searching for the serial number 12345abcdefg, enter the following:

`gam print cros query "id:12345abcdefg"`

Partial serial number searches are supported, as long as you enter at least three characters in the serial number.

All serial number searches are partial, be careful that you don't enter a partial serial number by mistake
when actioning/modifying devices as you will affect multiple devices rather than the single desired device.

### Status
To view all provisioned or deprovisioned devices, select the status from the left drop-down, and all of the devices that fit this criterion will appear in the view. Alternatively, you can do the following searches from the All devices view:

`gam print cros query "status:[provisioned|disabled|deprovisioned]"`

### User
Enter user: as the operator. For example, to match the name Joe, but not Joey, enter the following:

`gam print cros query "user:joe"`

To match the name Tom Sawyer or A. Tom Sawyer, but not Tom A. Sawyer, enter with quotation marks:

`gam print cros query "user:'tom sawyer'"`

### Location
Enter location: as the operator. For example, to match Seattle, enter the following:

`gam print cros query "location:seattle"`

Notes
Enter note: as the operator. For example, to match loaned from John, enter the following with quotation marks:

`gam print cros query "note:'loaned from john'"`

### Register
This field is not displayed on the Chrome OS settings page. However, you can search for devices that were registered on a given date, or within a given time range.

Enter register: as the operator, and enter a date and time (or time range) as the argument. For example, to search for all devices registered on April 15, 2020, enter the following:

`gam print cros query "register:2020-04-15"`

For additional examples using dates, times, and ranges, see "Format for date searches" below.

### Last Sync
Enter sync: as the operator and a date or time range as the argument. For example, to search for all devices that were last synced with policy settings on April 15, 2020, enter the following:

`gam print cros query "sync:2020-04-15"`

For additional examples using dates, times, and ranges, see "Format for date searches" below.

### Format for date searches
* `YYYY-MM-DD` - A single date
* `YYYY-MM-DD..YYYY-MM-DD` - A date range
* `..YYYY-MM-DD` - All dates on or before a date
* `YYYY-MM-DD..` - All dates on or after a date

### Asset ID
Enter asset_id: as the operator. For example, to match the partial Asset ID 1234, enter the following:

`gam print cros query "asset_id:1234"`

### WiFi MAC Address
Enter wifi_mac: as the operator. Address should be entered without spaces or colons. Partial address matching is not supported. Be aware that multiple devices may report the same address to the Admin console, and more than one result may be returned. For example, to search for the device(s) with WiFi MAC 6C:29:95:72:4C:50, enter the following:

`gam print cros query "wifi_mac:6c2995724c50"`

### Ethernet MAC Address
Enter ethernet_mac: as the operator. Address should be entered without spaces or colons. Partial address matching is not supported. Be aware that multiple devices may report the same address to the Admin console, and more than one result may be returned. For example, to search for the device(s) with ethernet MAC E8:EA:6A:15:79:81, enter the following:

`gam print cros query "ethernet_mac:e8ea6a157981"`

## ChromeOS device update OU error handling
If you get the following error when trying to update the OU of a ChromeOS device:
```
400: invalidInput - Invalid Input: Inconsistent Orgunit id and path in request
```
issue the following command to work around the Google problem causing the wrror:
```
gam select default config update_cros_ou_with_id true save
```

## Manage ChromeOS devices

```
gam <CrOSTypeEntity> update <CrOSAttribute>+ [quickcrosmove [<Boolean>]] [nobatchupdate]
gam update cros <CrOSEntity> <CrOSAttribute>+ [quickcrosmove [<Boolean>]] [nobatchupdate]
```

Google has introduced a new, faster method for moving CrOS devices to a new OU. The `quickcrosmove` option controls which method Gam uses.
* `quickcrosmove not specified` - use value from `quick_cros_move` in `gam.cfg` to select previous/new batch method
* `quickcrosmove False` - use individual method
* `quickcrosmove True` - use new method
* `quickcrosmove` - use new method

If `quickcrosmove` is False or the OU is not being updated, the individual method is used to update all attributes.
If `quickcrosmove` is True and the OU is the only `<CrOSAttribute>` being updated, the new method is used.
If `quickcrosmove` is True and other `<CrOSAttribute>` are being updated in addition to the OU, the new method is used
to update the OU and the individual method is used to update the other `<CrOSAttribute>`.

With either the individual or new method, batches of devices are processed to minimize the number of API calls.
The `batch_size` value from gam.cfg controls the number of deviceIds handled in each batch by either method.
Use the `nobatchupdate` option to suppress batch processing.

In the new method, Google doesn't seem to do any error checking of the CrOS deviceIds, there is no error message
given if invalid CrOS deviceIds are specified.

### Example: Move CrOS devices from one OU to another

```
gam cros_ou /Students/2021 update ou /Students/2022 quickcrosmove
```

### Example: Add a new note to existing notes

If you specify the `updatenotes <String>` option and it contains the string `#notes#`, the existing notes value will replace `#notes#`.
This requires an additional API to get the existing value.

If you have a CSV file, UpdateCrOS.csv with two columns: deviceId,notes
this command will add a new line of notes to the front of the existing notes:

```
gam csv UpdateCrOS.csv gam update cros "~deviceId" updatenotes "~~notes~~\n#notes#"
```

## Add ChromeOS devices to an organizational unit
When adding ChromeOS devices to an OU, Gam uses a batch method to speed up processing. 

For `<CrOSTypeEntity>`, see: [Collections of ChromeOS Devices](Collections-of-ChromeOS-Devices)
```
gam update org|ou <OrgUnitPath> add|move <CrOSTypeEntity>
        [quickcrosmove [<Boolean>]]
gam update orgs|ous <OrgUnitEntity> add|move <CrOSTypeEntity>
        [quickcrosmove [<Boolean>]]
```
Google has introduced a new, faster batch method for moving CrOS devices to a new OU. The `quickcrosmove` option controls which method Gam uses.
* `quickcrosmove not specified` - use value from `quick_cros_move` in `gam.cfg` to select previous/new batch method
* `quickcrosmove False` - use previous batch method
* `quickcrosmove True` - use new batch method
* `quickcrosmove` - use new batch method

The `batch_size` value from gam.cfg controls the number of deviceIds handled in each batch by either method.

In the new method, Google doesn't seem to do any error checking of the CrOS deviceIds, there is no error message
given if invalid CrOS deviceIds are specified.

### Example: Add ChromeOS devices to a single OU
Suppose you have a CSV file cros.csv with a single column: deviceId
```
gam update ou /Students/2022 add croscsvfile cros.csv:deviceId quickcrosmove
```

### Example: Add ChromeOS devices to multiple OUs
Suppose you have a CSV file cros.csv with a two columns: deviceId,OU

All OUs will be updated with their associated devices.
```
gam update ou csvkmd cros.csv keyfield OU datafield deviceId add croscsvdata deviceId
```

## Action ChromeOS devices

```
<CrOSAction> ::=
        deprovision_different_model_replace|
        deprovision_retiring_device|
        deprovision_same_model_replace|
        deprovision_upgrade_transfer|
        disable|
        reenable

gam <CrOSTypeEntity> update action <CrOSAction> [acknowledge_device_touch_requirement]
        [actionbatchsize <Integer>]
gam update cros <CrOSEntity> action <CrOSAction> [acknowledge_device_touch_requirement]
        [actionbatchsize <Integer>]
```
As of GAM version `6.67.00`, the new API function `batchChangeStatus` replaces the old API function `action`; ChromeOS devices are now processed in batches.
The batch size defaults to 10, the `actionbatchsize <Integer>` option can be used to set a batch size between 10 and 250.

As deprovisioning ChromeOS devices is not reversible, you must enter `acknowledge_device_touch_requirement`
when `<CrOSAction>` is `deprovision_same_model_replace`, `deprovision_different_model_replace`,
`deprovision_retiring_device` or `deprovision_upgrade_transfer`.

Deprovisioning a device means the device will have to be physically wiped and re-enrolled to be managed by
your domain again. This requires physical access to the device and is very time consuming to perform for
each device. Please also be aware that deprovisioning can have an effect on your device license count.

See https://support.google.com/chrome/a/answer/3523633 for full details.

## Send remote commands to ChromeOS devices
Thanks to Jay for most of the following.

Send a remote command to the managed Chrome OS device. It's important to note that the device must be in a proper state to accept the command or an error may be returned.
For example, the `reboot`, `set_volume` and `take_a_screenshot` commands only work if the device is configured in auto-start kiosk app mode.

The `wipe_users` and `remote_powerwash` commands will erase all user data on the device and the `remote_powerwash` command will require that the device is physically reconnected to the
WiFi network and re-enrolled before it can be managed again. These commands require the `doit` argument so that the admin confirms the potential loss of user data and management.

Commands may take some time to execute on the remote device depending on the device state and connectivity to the Internet.
It's strongly recommended that devices be forced to auto-reenroll before performing `remote_powerwash` to prevent the device from falling out of a managed state permanently.

By default, GAM will wait 2 seconds and then check the status of the command before exiting. How many times GAM performs this status check can be configured with the `times_to_check_status` argument and
is configurable from 0 to some large number. If the status reaches `EXPIRED`, `CANCELLED` or `EXECUTED_BY_CLIENT` then the command has finished and no more checks will be performed.
```
<CrOSCommand>
        reboot|
        remote_powerwash|
        set_volume <0-100>|
        wipe_users|
        take_a_screenshot

gam cros <CrOSTypeEntity> issuecommand command <CrOSCommand> [times_to_check_status <Integer>] [doit]
gam issuecommand cros <CrOSEntity> command <CrOSCommand> [times_to_check_status <Integer>] [doit]
```
If the final status is not reached before GAM exits, you can issue the following commands to continue checking the status.
```
gam cros <CrOSTypeEntity> getcommand commandid <CommandID> [times_to_check_status <Integer>]
gam getcommand cros <CrOSEntity> commandid <CommandID> [times_to_check_status <Integer>]
```

### Action Examples
Remove user profile data from the device; the device will remain enrolled and connected.
User data not synced to the Cloud including Downloads, Android app data and Crostini Linux VMs will be permanently lost.
Commands with issuecommand directly after gam will work with Legacy GAM & GAM7, whereas commands where the issuecommand is after the cros <CrOSTypeEntity> will work only with GAM7. 
```
gam issuecommand cros dd1d659a-0ea4-4e94-905e-4726c7a5f1e9 command wipe_users doit
```
Remove profiles using the annotatedAssetID, which is a user editable field, in this example the device has an asset ID of CB1234.
```
gam cros_query "asset_id:CB1234" issuecommand command wipe_users doit
```
For multiple devices you can separate each asset ID with a comma 
```
gam cros_queries "asset_id:CB1234,asset_id:CB5678" issuecommand command wipe_users doit
```
Powerwash the device with serial number 143040348.
```
gam issuecommand cros query:id:143040348 command remote_powerwash times_to_check_status 10 doit
gam cros_sn 143040348 issuecommand command remote_powerwash times_to_check_status 10 doit
```

Powerwash all devices in the /StudentCarts OrgUnit. Devices will need to be manually reconnected to WiFi which may mean entering a PSK.
Use `wipe_users` if that's going to create too much work for you.
```
gam issuecommand cros "query:orgunitpath:/StudentCarts" command remote_powerwash times_to_check_status 0 doit
gam cros_ou /StudentCarts issuecommand command remote_powerwash times_to_check_status 0 doit
```
## ChromeOS device lists
ChromeOS devices have lists of data: `<CrOSListFieldName>`, `<CrOSActivityListFieldName>`, `<CrOSTelemetryListFieldName>`.
All lists except `recentusers` are in ascending order (oldest to newest). As these lists can contain many entries,
you can use the `listlimit <Number>` option to limit the amount of data, but you'll get the oldest `<Number>` entries
(except for `recentusers`) which may not be what you want. The `reverselists` option changes the order to descending (newest to oldest);
the `listlimit <Number>` now gets the newest `<Number>` entries.

The `activetimeranges` and `recentusers` lists are independent, they are not aligned. The only alignment that
you can achieve is `activetimeranges recentusers reverselists activetimeranges listlimit 1`; this yields the
most recent user's activity time.

List field name synonyms:
- `activetimeranges` - `timeranges` and `times`
- `devicefiles` - `files`
- `recentusers` - `users`

## Display information about ChromeOS devices

```
gam <CrOSTypeEntity> info
        [basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
        [nolists]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSListFieldNameList>]
        [timerangeorder ascending|descending] [showdvrsfp]
        [downloadfile latest|<Time>] [targetfolder <FilePath>]
        [formatjson]

gam info cros <CrOSEntity>
        [basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
        [nolists]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSListFieldNameList>]
        [timerangeorder ascending|descending] [showdvrsfp]
        [downloadfile latest|<Time>] [targetfolder <FilePath>]
        [formatjson]
```

By default, Gam displays the information as an indented list of keys and values:

- `reverselists <CrOSListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists activetimeranges`
- `timerangeorder descending` - Change the `activetimeranges` order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `timeranges listlimit N timerangeorder descending`
- `showdvrsfp` - Display a field `diskVolumeReports.volumeInfo.storageFreePercentage` which is calculated as: `(diskVolumeReports.volumeInfo.storageFree/diskVolumeReports.volumeInfo.storageTotal)*100`

- `formatjson` - Display the fields in JSON format.

## Print ChromeOS devices

### Print no header row and deviceId for specified CrOS devices

```
gam <CrOSTypeEntity> print
gam <CrOSTypeEntity> print cros
```

### Print a header row and fields for selected CrOS devices

```
gam print cros [todrive <ToDriveAttribute>*]
        [(query <QueryCrOS>)|(queries <QueryCrOSList>) [querytime<String> <Time>]
         [(limittoou|cros_ou <OrgUnitItem>)|(cros_ou_and_children <OrgUnitItem>)|
          (cros_ous <OrgUnitList>)|(cros_ous_and_children <OrgUnitList>)]]
        [orderby <CrOSOrderByFieldName> [ascending|descending]]
        [basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
        [nolists|(<CrOSListFieldName>* [onerow])]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSListFieldNameList>]
        [timerangeorder ascending|descending] [showdvrsfp]
        (addcsvdata <FieldName> <String>)*
        [sortheaders]
        [formatjson [quotechar <Character>]]
```

Use these options to select CrOS devices; if none are chosen, all CrOS devices in the account are selected.

If only `(query <QueryCrOS>)|(queries <QueryCrOSList>)` is specified, the query applies to all devices. If one of the `cros_ou` options
is also specified, the query applies to devices within the OUs.

- `(query <QueryCrOS>)|(queries <QueryCrOSList>)` - Select CrOS devices that match a query
- `limittoou|cros_ou <OrgUnitItem>` - Select CrOS devices directly in the OU `<OrgUnitItem>`
  - You can predefine this item with the `print_cros_ous` variable in `gam.cfg`.
- `cros_ou_and_children <OrgUnitItem>` - Select CrOS devices in the OU `<OrgUnitItem>` and its sub OUs
  - You can predefine this item with the `print_cros_ous_and_children` variable in `gam.cfg`.
- `cros_ous <OrgUnitList>` - Select CrOS devices directly in the OUs `<OrgUnitList>`
  - You can predefine this list with the `print_cros_ous` variable in `gam.cfg`.
- `cros_ous_and_children <OrgUnitList>` - Select CrOS devices in the OUs `<OrgUnitList>` and their sub OUs
  - You can predefine this list with the `print_cros_ous_and_children` variable in `gam.cfg`.

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryCrOS>` and `queries <QueryCrOSList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

For example, query for CrOS devices last synced more than a year ago:
```
querytime1year -1y query "sync:..#querytime1year#"
```

The first column will always be deviceId; the remaining field names will be sorted if `allfields`, `basic`, `full` or `sortheaders` is specified;
otherwise, the remaining field names will appear in the order specified.

- `basic` - Output these column headers: deviceId,annotatedAssetId,annotatedLocation,annotatedUser,lastSync,notes,serialNumber,status
- `allfields/full` - Output all column headers including eight list headers: activeTimeRanges, cpuStatusReports, deviceFiles, diskVolumeReports, lastKnownNetwork, recentUsers, screenshotFiles and systemRamFreeReports that repeat with multiple subvalues each, yielding a large number of columns that make the output hard to process.
- `nolists` -  Suppresses these six headers; if you want these headers in a more manageable form use the following arguments.
- `<CrOSListFieldName>` - By default, one set of values for all `<CrOSListFieldName>` fields specified will be output on a separate row with all of the other headers.
- `onerow` - Output all of the `<CrOSListFieldName>` on a single row
- `listlimit <Number>` - Limits the number of repetitions to `<Number>`; if not specified or `<Number>` equals zero, there is no limit.
- `start <Date>` and `end <Date>` - Constrain activeTimeRanges, cpuStatusReports, deviceFiles and systemRamFreeReports to fall within the specified `<Dates>`. If a `<Date>` isn't specified, there is no filtering in that range.
- `reverselists <CrOSListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists timeranges`
- `timerangeorder descending` - Change the `activetimeranges` order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `timeranges listlimit N timerangeorder descending`.
- `showdvrsfp` - Display a field `diskVolumeReports.volumeInfo.storageFreePercentage` which is calculated as: `(diskVolumeReports.volumeInfo.storageFree/diskVolumeReports.volumeInfo.storageTotal)*100`

Add additional columns of data from the command line to the output
* `addcsvdata <FieldName> <String>`

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:

- `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Print a header row and fields for specified CrOS devices

Use [Print a header row and fields for selected CrOS devices](#print-a-header-row-and-fields-for-selected-cros-devices) if
you are specifying devices by OU; it will be much faster.
```
gam <CrOSTypeEntity> print cros [todrive <ToDriveAttribute>*]
        [orderby <CrOSOrderByFieldName> [ascending|descending]]
        [basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
        [nolists|(<CrOSListFieldName>* [onerow])]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSListFieldNameList>]
        [timerangeorder ascending|descending] [showdvrsfp]
        (addcsvdata <FieldName> <String>)*
        [sortheaders]
        [formatjson [quotechar <Character>]]

gam print cros [todrive <ToDriveAttribute>*] select <CrOSTypeEntity>
        [orderby <CrOSOrderByFieldName> [ascending|descending]]
        [basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
        [nolists|(<CrOSListFieldName>* [onerow])]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSListFieldNameList>]
        [timerangeorder ascending|descending] [showdvrsfp]
        [sortheaders]
        [formatjson [quotechar <Character>]]
```

The first column will always be deviceId; the remaining field names will be sorted if `allfields`, `basic`, `full` or `sortheaders` is specified;
otherwise, the remaining field names will appear in the order specified.

- `basic` - Output these column headers: deviceId,annotatedAssetId,annotatedLocation,annotatedUser,lastSync,notes,serialNumber,status
- `allfields/full` - Output all column headers including eight list headers: activeTimeRanges, cpuStatusReports, deviceFiles, diskVolumeReports, lastKnownNetwork, recentUsers, screenshotFiles and systemRamFreeReports that repeat with multiple subvalues each, yielding a large number of columns that make the output hard to process.
- `nolists` -  Suppresses these six headers; if you want these headers in a more manageable form use the following arguments.
- `<CrOSListFieldName>` - By default, one set of values for all `<CrOSListFieldName>` fields specified will be output on a separate row with all of the other headers.
- `onerow` - Output all of the `<CrOSListFieldName>` on a single row
- `listlimit <Number>` - Limits the number of repetitions to `<Number>`; if not specified or `<Number>` equals zero, there is no limit.
- `start <Date>` and `end <Date>` - Constrain activeTimeRanges, cpuStatusReports, deviceFiles and systemRamFreeReports to fall within the specified `<Dates>`. If a `<Date>` isn't specified, there is no filtering in that range.
- `reverselists <CrOSListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists timeranges`
- `timerangeorder descending` - Change the `activetimeranges` order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `timeranges listlimit N timerangeorder descending`.
- `showdvrsfp` - Display a field `diskVolumeReports.volumeInfo.storageFreePercentage` which is calculated as: `(diskVolumeReports.volumeInfo.storageFree/diskVolumeReports.volumeInfo.storageTotal)*100`

Add additional columns of data from the command line to the output
* `addcsvdata <FieldName> <String>`

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:

- `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Display Examples

Print CrOS devices with limited free space:
```
gam config csv_output_row_filter "diskVolumeReports.volumeInfo.0.storageFreePercentage:countrange=1/30" redirect csv ./crosdiskusage.csv print cros fields serialnumber,ou,diskvolumereports showdvrsfp
```
Use `countrange=1/15` instead of `count<15` as the latter will display ChromeOS devices with no
diskVolumeReports; a blank entry is treated as a zero. Sustitue for `15` as desired.

ChromeOS devices can have multiple diskVolumeReports; some experimentation may be required to
get the desired results.

Print information about CrOS devices synced more than 30 days ago:

```
gam print cros query "sync:..#querytime1#" querytime1 -30d
```

Print information about CrOS devices synced in the last 30 days:

```
gam print cros query "sync:#querytime1#.." querytime1 -30d
```

Print information about CrOS devices synced between 45 days ago and 30 days ago:

```
gam print cros query "sync:#querytime1#..#querytime2#" querytime1 -45d querytime2 -30d
```

## Display CrOS device counts
Display the number of CrOS devices in an entity.
```
gam <CrOSTypeEntity> show count
gam <CrOSTypeEntity> print cros showitemcountonly
gam print cros select <CrOSTypeEntity> showitemcountonly
gam print cros
        [(query <QueryCrOS>)|(queries <QueryCrOSList>) [querytime<String> <Time>]
         [(limittoou|cros_ou <OrgUnitItem>)|(cros_ou_and_children <OrgUnitItem>)|
          (cros_ous <OrgUnitList>)|(cros_ous_and_children <OrgUnitList>)]]
        showitemcountonly
```
Example
```
$ gam print cros query "sync:..2020-01-01" showitemcountonly
Getting all CrOS Devices that match query (sync:..2020-01-01) for /, may take some time on a large Organizational Unit...
Got 77 CrOS Devices that matched query (sync:..2020-01-01) for /...
Got 77 CrOS Devices that matched query (sync:..2020-01-01)
77
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print cros query "sync:..2020-01-01" showitemcountonly)
Windows PowerShell
count = & gam print cros query "sync:..2020-01-01" showitemcountonly
```

## Print ChromeOS device activity

### Print a header row and activity for selected CrOS devices

```
gam print crosactivity [todrive <ToDriveAttribute>*]
        [(query <QueryCrOS>)|(queries <QueryCrOSList>) [querytime<String> <Time>]
         [(limittoou|cros_ou <OrgUnitItem>)|(cros_ou_and_children <OrgUnitItem>)|
          (cros_ous <OrgUnitList>)|(cros_ous_and_children <OrgUnitList>)]]
        [orderby <CrOSOrderByFieldName> [ascending|descending]]
        [recentusers] [timeranges] [both] [devicefiles] [all] [oneuserperrow]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSActivityListFieldNameList>]
        [timerangeorder ascending|descending]
        [delimiter <Character>]
        [formatjson [quotechar <Character>]]
```

Use these options to select CrOS devices; if none are chosen, all CrOS devices in the account are selected.

If only `(query <QueryCrOS>)|(queries <QueryCrOSList>)` is specified, the query applies to all devices. If one of the `cros_ou` options
is also specified, the query applies to devices within the OUs.

- `(query <QueryCrOS>)|(queries <QueryCrOSList>)` - Select CrOS devices that match a query
- `limittoou|cros_ou <OrgUnitItem>` - Select CrOS devices directly in the OU `<OrgUnitItem>`
  - You can predefine this item with the `print_cros_ous` variable in `gam.cfg`.
- `cros_ou_and_children <OrgUnitItem>` - Select CrOS devices in the OU `<OrgUnitItem>` and its sub OUs
  - You can predefine this item with the `print_cros_ous_and_children` variable in `gam.cfg`.
- `cros_ous <OrgUnitList>` - Select CrOS devices directly in the OUs `<OrgUnitList>`
  - You can predefine this list with the `print_cros_ous` variable in `gam.cfg`.
- `cros_ous_and_children <OrgUnitList>` - Select CrOS devices in the OUs `<OrgUnitList>` and their sub OUs
  - You can predefine this list with the `print_cros_ous_and_children` variable in `gam.cfg`.

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryCrOS>` and `queries <QueryCrOSList>` options.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers.

For example, query for CrOS devices last synced more than a year ago:
```
querytime1year -1y query "sync:..#querytime1year#"
```
- `reverselists <CrOSListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists timeranges`
- `timerangeorder descending` - Change the `activetimeranges` order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `timeranges listlimit N timerangeorder descending`.

### Print a header row and activity for specified CrOS devices

Use [Print a header row and activity for selected CrOS devices](#print-a-header-row-and-activity-for-selected-cros-devices)
you are specifying devices by OU; it will be much faster.
```
gam <CrOSTypeEntity> print crosactivity [todrive <ToDriveAttribute>*]
        [orderby <CrOSOrderByFieldName> [ascending|descending]]
        [recentusers] [timeranges] [both] [devicefiles] [all] [oneuserperrow]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSActivityListFieldNameList>]
        [timerangeorder ascending|descending]
        [delimiter <Character>]
        [formatjson [quotechar <Character>]]

gam print crosactivity [todrive <ToDriveAttribute>*] select <CrOSTypeEntity>
        [orderby <CrOSOrderByFieldName> [ascending|descending]]
        [recentusers] [timeranges] [both] [devicefiles] [all] [oneuserperrow]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSActivityListFieldNameList>]
        [timerangeorder ascending|descending]
        [delimiter <Character>]
        [formatjson [quotechar <Character>]]
```

- The basic column headers are: deviceId,annotatedAssetId,annotatedLocation,serialNumber,orgUnitPath.
- `recentusers` - All of the recent users email addresses, separated by the delimiter `<Character>`, with header recentUsers.email, are output with the basic headers.
  - The delimiter defaults to `gam.cfg/csv_output_field_delimiter`.
  - If `oneuserperrow` is specified, each recent user is output on a separate row with header recentUsers.email and the basic headers.
- `activetimeranges` - For each time range entry, activeTimeRanges.date, activeTimeRanges.duration and activeTimeRanges.minutes are output on a separate row with the basic headers.
- `devicefiles` - For each device file, the columns deviceFiles.type and deviceFiles.createTime are output on a separate row with the basic headers.

- `both` - Specifies `recentusers` and `activetimeranges`.
- `all` - Specifies `recentusers`, `activetimeranges` and `devicefiles`.
- The default is to include both `recentusers` and `activetimeranges`.

- `listlimit <Number>` - Limits the number of repetitions to `<Number>`; if not specified or `<Number>` equals zero, there is no limit.
- `start <Date>` and `end <Date>` - Filter the time ranges and device files to fall with in the specified `<Dates>`. If a `<Date>` isn't specified, there is no filtering in that range.
- `reverselists <CrOSListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists timeranges`
- `timerangeorder descending` - Change the `activetimeranges` order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `timeranges listlimit N timerangeorder descending`.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:

- `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Download a ChromeOS device file

```
gam <CrOSTypeEntity> info downloadfile latest|<Time> [targetfolder <FilePath>]
gam info cros <CrOSEntity> downloadfile latest|<Time> [targetfolder <FilePath>]
```

Select the device file to download by its timestamp.

- `downloadfile latest` - Download the device file with the most recent timestamp.
- `downloadfile <Time>` - Download the device file with the `<`Time>` timestamp.

By default, when getting a device file, it is downloaded to the directory specified in `gam.cfg/drive_dir`.

- `targetfolder <FilePath>` - Specify an alternate location for the downloaded file.

### Download Examples

Suppose that you have an OU "/Kiosk Chromebooks" that contains ChromeOS devices running in kiosk mode and you want to download their device files.

Get the list of device files.

```
gam redirect csv ./CrOSDeviceFiles.csv print cros cros_ou "/Kiosk ChromeBooks" fields deviceId,devicefiles
```

Download the device files serially.

```
gam redirect stdout ./CrOSDeviceFiles.out redirect stderr stdout csvkmd cros ./CrOSDeviceFiles.csv keyfield deviceId matchfield deviceFiles.type LOG_FILE datafield deviceFiles.createTime get devicefile select csvdata deviceFiles.createTime
```

Download the device files in parallel.

```
gam redirect stdout ./CrOSDeviceFiles.out multiprocess redirect stderr stdout csv ./CrOSDeviceFiles.csv matchfield deviceFiles.type LOG_FILE gam cros "~deviceId" get devicefile select "~deviceFiles".createTime
```

Suppose you want only the last device file for each Chromebook.

Download the device files serially.

```
gam redirect stdout ./CrOSDeviceFiles.out redirect stderr stdout cros_ou "/Kiosk ChromeBooks" get devicefile select last 1
```

Download the device files in parallel

```
gam config auto_batch_min 1 redirect stdout ./CrOSDeviceFiles.out multiprocess redirect stderr stdout cros_ou "/Kiosk ChromeBooks" get devicefile select last 1
```
## Display ChromeOS telemetry data
### Display data about a specific device.
```
gam info crostelemetry <SerialNumber>
        <CrOSTelemetryFieldName>* [fields <CrOSTelemetryFieldNameList>]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSTelemetryListFieldNameList>]
        [formatjson]
```
### Display data about all or selected devices.
```
gam show crostelemetry
        [(ou|org|orgunit|ou_and_children <OrgUnitItem>)|(cros_sn <SerialNumber>)|(filter <String>)]
        <CrOSTelemetryFieldName>* [fields <CrOSTelemetryFieldNameList>]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [reverselists <CrOSTelemetryListFieldNameList>]
        [formatjson]
```
Use these options to select CrOS devices; if none are chosen, all CrOS devices in the account are selected.

- `ou|org|orgunit <OrgUnitItem>` - Select CrOS devices directly in the OU `<OrgUnitItem>`
- `ou_and_children <OrgUnitItem>` - Select CrOS devices in the OU `<OrgUnitItem>` and its sub OUs
- `cros_sn <SerialNumber>` - Select the CrOS device with serial number `<SerialNumber>`.
- `filter <String>` - Select the CrOS device with a filter.
- `listlimit <Number>` - Limits the number of repetitions to `<Number>`; if not specified or `<Number>` equals zero, there is no limit.
- `start <Date>` and `end <Date>` - Constrain list `reportTime` to fall within the specified `<Dates>`. If a `<Date>` isn't specified, there is no filtering in that range.
- `reverselists <CrOSTelemetryListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists cpustatusreport,memorystatusreport`

By default, all telemetry data is displayed, use the following to select specific fields:
- `<CrOSTelemetryFieldName>*` - Specify fields individually
- `fields <CrOSTelemetryFieldNameList>` - Specify a list of fields

By default, Gam displays the information as an indented list of keys and values:
- `formatjson` - Display the fields in JSON format.

### Print data about all or selected devices.
```
gam print crostelemetry [todrive <ToDriveAttribute>*]
        [(ou|org|orgunit|ou_and_children <OrgUnitItem>)|(cros_sn <SerialNumber>)|(filter <String>)]
        <CrOSTelemetryFieldName>* [fields <CrOSTelemetryFieldNameList>]
        [reverselists <CrOSTelemetryListFieldNameList>]
        [start <Date>] [end <Date>] [listlimit <Number>]
        [formatjson [quotechar <Character>]]
```
Use these options to select CrOS devices; if none are chosen, all CrOS devices in the account are selected.

- `ou|org|orgunit <OrgUnitItem>` - Select CrOS devices directly in the OU `<OrgUnitItem>`
- `ou_and_children <OrgUnitItem>` - Select CrOS devices in the OU `<OrgUnitItem>` and its sub OUs
- `cros_sn <SerialNumber>` - Select the CrOS device with serial number `<SerialNumber>`.
- `filter <String>` - Select the CrOS device with a filter.
- `listlimit <Number>` - Limits the number of repetitions to `<Number>`; if not specified or `<Number>` equals zero, there is no limit.
- `start <Date>` and `end <Date>` - Constrain list `reportTime` to fall within the specified `<Dates>`. If a `<Date>` isn't specified, there is no filtering in that range.
- `reverselists <CrOSTelemetryListFieldNameList>` - For each list, change order from ascending (oldest to newest) to descending (newest to oldest); this makes it easy to get the `N` most recent values with `listlimit N reverselists cpustatusreport,memorystatusreport`

By default, all telemetry data is displayed, use the following to select specific fields:
- `<CrOSTelemetryFieldName>*` - Specify fields individually
- `fields <CrOSTelemetryFieldNameList>` - Specify a list of fields

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
- `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Check ChromeOS device serial number validity
Use this command to check the validity of ChromeOS device serial numbers.
```
gam print chromesnvalidity [todrive <ToDriveAttribute>*]
        cros_sn <SerialNumberEntity> [listlimit <Number>]
        [delimiter <Character>]
```
You specify serial numbers and GAM performs a query to see how many devices match; serial number matches are case-insensitive.

There are are two types of matches:
- Exact - A device has the exact serial number
- Prefix - A device has a serial number that has the specified value as a prefix

The column headers are: serialNumber,exactMatches,exactMatchDeviceIds,prefixMatches,prefixMatchDeviceIds.
- serialNumber - The serial number specified
- exactMatches - The number of exact matches
- exactMatchDeviceIds - The list of device IDs with exact match serial numbers
- prefixMatches - The number of prefix matches
- prefixMatchDeviceIds - The list of device IDs with prefix match serial numbers

The device IDs are separated by the delimiter `<Character>` that defaults to `gam.cfg/csv_output_field_delimiter`.

By default, all matching device IDs are displayed:
- `listlimit <Number>` - Limits the number of device IDs in a list to `<Number>`; if not specified or `<Number>` equals zero, there is no limit. `exactMatches` and `prefixmatches`
display the total number of matches.

### Examples
Specify serial numbers in the command.
```
$ gam print chromesnvalidity crossn DPCVLB3X,5CD9326FW0,5CD92055W  listlimit 2 delimiter "|"
Getting all CrOS Devices that match query (id:DPCVLB3X), may take some time on a large Google Workspace Account...
Got 0 CrOS Devices...
Getting all CrOS Devices that match query (id:5CD9326FW0), may take some time on a large Google Workspace Account...
Got 1 CrOS Device...
Getting all CrOS Devices that match query (id:5CD92055W), may take some time on a large Google Workspace Account...
Got 5 CrOS Devices...
serialNumber,exactMatches,exactMatchDeviceIds,prefixMatches,prefixMatchDeviceIds
DPCVLB3X,0,,0,
5CD9326FW0,1,bfaef389-a1d5-4e7b-b9af-bfc6cdbdb5b2,0,
5CD92055W,0,,5,0123a16d-3884-4829-9324-df92d8fc1ad4|899d2b95-7914-4b6b-8428-d416ef900728
```

Specify serial numbers in a flat file.
```
$ more CrosSN.txt
DPCVLB3X
5CD9326FW0
5CD92055W

$ gam print chromesnvalidity crossn file CrosSN.txt listlimit 2 delimiter "|"
Getting all CrOS Devices that match query (id:DPCVLB3X), may take some time on a large Google Workspace Account...
Got 0 CrOS Devices...
Getting all CrOS Devices that match query (id:5CD9326FW0), may take some time on a large Google Workspace Account...
Got 1 CrOS Device...
Getting all CrOS Devices that match query (id:5CD92055W), may take some time on a large Google Workspace Account...
Got 5 CrOS Devices...
serialNumber,exactMatches,exactMatchDeviceIds,prefixMatches,prefixMatchDeviceIds
DPCVLB3X,0,,0,
5CD9326FW0,1,bfaef389-a1d5-4e7b-b9af-bfc6cdbdb5b2,0,
5CD92055W,0,,5,0123a16d-3884-4829-9324-df92d8fc1ad4|899d2b95-7914-4b6b-8428-d416ef900728```
```

Specify serial numbers in a CSV file.
```
$ more CrosSN.csv
serialNumber
DPCVLB3X
5CD9326FW0
5CD92055W

$ gam print chromesnvalidity crossn csvfile CrosSN.csv:serialNumber  listlimit 2 delimiter "|"
Getting all CrOS Devices that match query (id:DPCVLB3X), may take some time on a large Google Workspace Account...
Got 0 CrOS Devices...
Getting all CrOS Devices that match query (id:5CD9326FW0), may take some time on a large Google Workspace Account...
Got 1 CrOS Device...
Getting all CrOS Devices that match query (id:5CD92055W), may take some time on a large Google Workspace Account...
Got 5 CrOS Devices...
serialNumber,exactMatches,exactMatchDeviceIds,prefixMatches,prefixMatchDeviceIds
DPCVLB3X,0,,0,
5CD9326FW0,1,bfaef389-a1d5-4e7b-b9af-bfc6cdbdb5b2,0,
5CD92055W,0,,5,0123a16d-3884-4829-9324-df92d8fc1ad4|899d2b95-7914-4b6b-8428-d416ef900728
```