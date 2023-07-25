# Organizational Units
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Special quoting](#special-quoting)
- [Manage organizational units](#manage-organizational-units)
- [Add users to an organizational unit](#add-users-to-an-organizational-unit)
- [Synchronize users with an organizational unit](#synchronize-users-with-an-organizational-unit)
- [ChromeOS device update OU error handling](#chromeos-device-update-ou-error-handling)
- [Add ChromeOS devices to an organizational unit](#add-chromeos-devices-to-an-organizational-unit)
  - [Example: Move CrOS devices from one OU to another](#example-move-cros-devices-from-one-ou-to-another)
  - [Example: Add ChromeOS devices to a single OU](#example-add-chromeos-devices-to-a-single-ou)
  - [Example: Add ChromeOS devices to multiple OUs](#example-add-chromeos-devices-to-multiple-ous)
- [Synchronize ChromeOS devices with an organizational unit](#synchronize-chromeos-devices-with-an-organizational-unit)
- [Display organizational units](#display-organizational-units)
- [Print organizational units](#print-organizational-units)
- [Display indented organizational unit tree](#display-indented-organizational-unit-tree)
- [Special case handling for large number of organizational units](#special-case-handling-for-large-number-of-organizational-units)

## API documentation
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/orgunits

## Definitions
```
<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>
<OrgUnitList> ::= "<OrgUnitItem>(,<OrgUnitItem>)*"

<OrgUnitFieldName> ::=
        description|
        id|orgunitid|
        inherit|blockinheritance|
        name|
        parentid|parentorgunitid|
        parent|parentorgunitpath|
        path|orgunitpath
<OrgUnitFieldNameList> ::= "<OrgUnitFieldName>(,<OrgUnitFieldName>)*"

<OrgUnitSelector> ::=
        cros_ou | cros_ou_and_children|
        ou | ou_ns | ou_susp|
        ou_and_children | ou_and_children_ns | ou_and_children_susp

```
For `<OrgUnitEntity>`, see: [Collections of Items](Collections-of-Items)

For `<UserTypeEntity>`, see: [Collections of Users](Collections-Of-Users)

For `<CrOSTypeEntity>`, see: [Collections of ChromeOS Devices](Collections-of-ChromeOS-Devices)

## Special quoting
You specify a single organizational unit with `org <OrgUnitPath>` and a list of organizationsl units with `orgs <OrgUnitList>`.
As organizational unit paths can contain spaces, some care must be used when entering `<OrgUnitPath>` and `<OrgUnitList>`.

Suppose you have an organizational unit `/Foo Bar`. To get information about it you enter the command: `gam info org "/Foo Bar"`

The shell strips the `"` leaving a single argument `/Foo Bar`; gam correctly processes the argument.

Suppose you enter the command: `gam info orgs "/Foo Bar"`

The shell strips the `"` leaving a single argument `/Foo Bar`; gam splits the argument on space leaving two items and then tries to process `/Foo` and `Bar`, not what you want.

You must enter: `gam info orgs "'/Foo Bar'"`

The shell strips the `"` leaving a single argument `'/Foo Bar'`; gam splits the argument on space while honoring the `'` leaving one item `/Foo Bar` and correctly processes the item.

See: [List Items](List-Items)

## Manage organizational units
Create, update and delete organization units.
```
gam create org|ou <OrgUnitPath> [description <String>]
        [parent <OrgUnitItem>] [inherit|noinherit|(blockinheritance <Boolean>)]
        [buildpath]
gam update org|ou <OrgUnitPath> [name <String>] [description <String>]
        [parent <OrgUnitItem>] [inherit|noinherit|(blockinheritance <Boolean>)]
gam delete org|ou <OrgUnitPath>
gam update orgs|ous <OrgUnitEntity> [name <String>] [description <String>]
        [parent <OrgUnitItem>] [inherit|noinherit|(blockinheritance <Boolean>)]
gam delete orgs|ous <OrgUnitEntity>
```

## Add users to an organizational unit
When adding users to an OU, Gam uses a batch method to speed up processing. 

For `<UserTypeEntity>`, see: [Collections of Users](Collections-Of-Users)
```
gam update org|ou <OrgUnitPath> add|move <UserTypeEntity>
gam update orgs|ous <OrgUnitEntity> add|move <UserTypeEntity>
```
The `batch_size` value from gam.cfg controls the number of users handled in each batch.

## Synchronize users with an organizational unit
When adding users to an OU, Gam uses a batch method to speed up processing. 

For `<UserTypeEntity>`, see: [Collections of Users](Collections-Of-Users)
```
gam update org|ou <OrgUnitItem> sync <UserTypeEntity> [removetoou <OrgUnitItem>]
gam update orgs|ous <OrgUnitEntity> sync <UserTypeEntity> [removetoou <OrgUnitItem>]
```
* Users in the `OU` but not in `<UserTypeEntity>` will be moved to `OU` / or the `OU` specified in `removetoou <OrgUnitItem>`
* Users in `<UserTypeEntity>` but not in the `OU` are moved to the `OU`
* Users in the `OU` and in `<UserTypeEntity>` are unaffected

The `batch_size` value from gam.cfg controls the number of users handled in each batch.

## ChromeOS device update OU error handling
If you get the following error when trying to update the OU of a ChromeOS device:
```
400: invalidInput - Invalid Input: Inconsistent Orgunit id and path in request
```
issue the following command to work around the Google problem causing the wrror:
```
gam select default config update_cros_ou_with_id true save
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

### Example: Move CrOS devices from one OU to another
```
gam update ou /Students/2022 add cros_ou /Students/2021 quickcrosmove
```

### Example: Add ChromeOS devices to a single OU
Suppose you have a CSV file cros.csv with a single column: deviceId
```
gam update ou /Students/2022 add croscsvfile cros.csv:deviceId quickcrosmove
```

### Example: Add ChromeOS devices to multiple OUs
Suppose you have a CSV file cros.csv with a two columns: deviceId,OU

All OUs will be updated with their associated devices.
```
gam update ou csvkmd cros.csv keyfield OU datafield deviceId add croscsvdata deviceId quickcrosmove
```

## Synchronize ChromeOS devices with an organizational unit
When adding ChromeOS devices to an OU, Gam uses a batch method to speed up processing. 

For `<CrOSTypeEntity>`, see: [Collections of ChromeOS Devices](Collections-of-ChromeOS-Devices)
```
gam update org|ou <OrgUnitItem> sync <CrOSTypeEntity> [removetoou <OrgUnitItem>]
        [quickcrosmove [<Boolean>]]
gam update orgs|ous <OrgUnitEntity> sync <CrOSTypeEntity> [removetoou <OrgUnitItem>]
        [quickcrosmove [<Boolean>]]
```
* Cros devices in the `OU` but not in `<CrOSTypeEntity>` will be moved to `OU` / or the `OU` specified in removetoou <OrgUnitItem>
* CrOS devices in `<CrOSTypeEntity>` but not in the `OU` are moved to the `OU`
* CrOS devices in the `OU` and in `<CrOSTypeEntity>` are unaffected

Google has introduced a new, faster batch method for moving CrOS devices to a new OU. The `quickcrosmove` option controls which method Gam uses.
* `quickcrosmove not specified` - use value from `quick_cros_move` in `gam.cfg` to select previous/new batch method
* `quickcrosmove False` - use previous batch method
* `quickcrosmove True` - use new batch method
* `quickcrosmove` - use new batch method

The `batch_size` value from gam.cfg controls the number of deviceIds handled in each batch by either method.

In the new method, Google doesn't seem to do any error checking of the CrOS deviceIds, there is no error message
given if invalid CrOS deviceIds are specified.

## Display organizational units
These commands display information as an indented list of keys and values.
```
gam info org|ou <OrgUnitPath> [nousers|notsuspended|suspended] [children|child]
gam info orgs|ous <OrgUnitEntity> [nousers|notsuspended|suspended] [children|child]
```
By default, all users of the org units are displayed:
* `nousers` - Don't display users of the org units
* `notsuspended` - Display non-suspended users of the org units
* `suspended` - Display suspended users of the org units

## Print organizational units
This command displays information in CSV format.
```
gam print orgs|ous [todrive <ToDriveAttribute>*]
        [fromparent <OrgUnitItem>] [showparent [Boolean>]] [toplevelonly]
        [parentselector <OrgUnitSelector> childselector <OrgUnitSelector>]
        [allfields|<OrgUnitFieldName>*|(fields <OrgUnitFieldNameList>)]
        [convertcrnl] [batchsuborgs [<Boolean>]]
        [mincroscount <Number>] [maxcroscount <Number>]
        [minusercount <Number>] [maxusercount <Number>]
```
By default, Gam prints all child org units of /.
* `fromparent <OrgUnitItem>` - Print all child org units of `<OrgUnitItem>`.
* `showparent` - Print the parent org unit, either / or `fromparent <OrgUnitItem>`.
* `toplevelonly` - Do not print any sub org units.
* `convertcrnl` - In the description field, convert carriage return to \r and new line to \n.

Options `parentselector <OrgUnitSelector>` and `childselector <OrgUnitSelector>`  add an additional column `orgUnitSelector` to the output.
This column value can be used in subsequent `gam csv` commands to appropriateley select members without duplication.

By default, all OUs are displayed. You can limit the display of OUs to those where the number
of ChromeOS devices/users falls within a range. Gathering this data requires additional API calls
to download information about all ChromeOS devices and users.

Additional columns are generated to display the number and status of ChromeOS devices and users in each OU.

* `mincroscount <Number>` - Display the OU if it has at leaset `<Number>` ChromeOS devices
* `maxcroscount <Number>` - Display the OU if it has no more than `<Number>` ChromeOS devices
* `minusercount <Number>` - Display the OU if it has at leaset `<Number>` users
* `maxusercount <Number>` - Display the OU if it has no more than `<Number>` users

### Examples:
Show all OUs with at least one user.
```
gam print orgs minusercount 1
```
Show all OUs with no users.
```
gam print orgs maxusercount 0
```
Get file count summaries by OU; top level selector is ou, sub level selectors are ou_and_children
```
gam redirect csv ./TopLevelOUs.csv print ous showparent toplevelonly parentselector ou childselector ou_and_children fields orgunitpath
gam redirect csv ./FileCounts.csv multiprocess csv ./TopLevelOUs.csv gam "~orgUnitSelector" "~orgUnitPath" print filecounts excludetrashed summary only summaryuser "~orgUnitPath"
```
## Display indented organizational unit tree
```
gam show orgtree [fromparent <OrgUnitItem>] [batchsuborgs [<Boolean>]]
```
By default, Gam displays the organizational unit tree starting at /.
* `fromparent <OrgUnitItem>` - Display the organizational unit tree starting at `<OrgUnitItem>`.

## Special case handling for large number of organizational units

By default, the `print orgs` and `show orgtree`  commands issue a single API call to get the
list of organizational units. If the number is large, greater than 5000 in an observed case, the API call may fail.
When `batchsuborgs` is specified, Gam gets all of the top level org units with one API call; then Gam uses batch processing
in subsequent API calls to get the sub org units. There is no benefit to using this option unless the commands fail
without it. The number of sub org units processed in each batch is controlled by `batch_size` in `gam.cfg`.
