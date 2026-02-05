# Chrome Policies
- [Chrome Version History](Chrome-Version-History)
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display a specific Chrome policy schema](#display-a-specific-chrome-policy-schema)
- [Display all or filtered Chrome policy schemas](#display-all-or-filtered-chrome-policy-schemas)
- [Display Chrome policy schemas in same format as Legacy GAM](#display-chrome-policy-schemas-in-same-format-as-legacy-gam)
- [Create a Chrome policy image](#create-a-chrome-policy-image)
- [Update Chrome policy](#update-chrome-policy)
- [Delete Chrome policy](#delete-chrome-policy)
- [Delete Chrome app](#delete-chrome-app)
- [Display Chrome policies](#display-chrome-policies)
- [Copy simple policies set directly in one OU to another OU](#copy-simple-policies-set-directly-in-one-ou-to-another-ou)
- [Copy simple and complex policies set directly in one OU to another OU](#copy-simple-and-complex-policies-set-directly-in-one-ou-to-another-ou)
- [Copy simple and complex policies set directly in one OU to multiple other OUs](#copy-simple-and-complex-policies-set-directly-in-one-ou-to-multiple-other-ous)
- [Copy simple policies in one Group to another Group](#copy-simple-policies-in-one-group-to-another-group)
- [Copy simple and complex policies in one Group to another Group](#copy-simple-and-complex-policies-in-one-group-to-another-group)
- [Copy simple and complex policies in one Group to multiple other Groups](#copy-simple-and-complex-policies-in-one-group-to-multiple-other-groups)
- [Create Chrome network](#create-chrome-network)
- [Delete Chrome network](#delete-chrome-network)
- [Chrome Policy Schema Table](#chrome-policy-schema-table)

## API documentation
* [Chrome Policy API - Overview](https://developers.google.com/chrome/policy/guides/policy-api)
* [Chrome Policy API - Schemas](https://developers.google.com/chrome/policy/guides/policy-schemas)
* [Set Chrome Policies for Users or Browsers](https://support.google.com/chrome/a/answer/2657289)

## Notes
To use these features you must add the `Chrome Policy API` to your project and authorize
the appropriate scope: `Chrome Policy API (supports readonly)`.
```
gam update project
gam oauth create
```

## Definitions
```
<AppID> ::= <String>
<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |
<Namespace> ::= <String>
<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String>)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>
<PrinterID> ::= <String>
<SchemaName> ::= <String>
<NamespaceList> ::= "<Namespace>(,<Namespace>)*"

<ChromePolicySchemaFieldName> ::=
        accessrestrictions|
        additionaltargetkeynames|
        categorytitle|
        definition|
        fielddescriptions|
        name|
        notices|
        policyapilifecycle|
        policydescription|
        schemaname|
        supporturi|
        validtargetresources
<ChromePolicySchemaFieldNameList> ::= "<ChromePolicySchemaFieldName>(,<ChromePolicySchemaFieldName>)*"
```
## Display a specific Chrome policy schema
```
gam info chromeschema <SchemaName>
        <ChromePolicySchemaFieldName>* [fields <ChromePolicySchemaFieldNameList>]
        [formatjson]
```
By default, all schema fields are displayed.
* `<ChromePolicySchemaFieldName>*` - Specify individual fields
* `fields <ChromePolicySchemaFieldNameList>` - Specify a list of fields

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display all or filtered Chrome policy schemas
### Display as an indented list of keys and values.
```
gam show chromeschemas
        [filter <String>]
        <ChromePolicySchemaFieldName>* [fields <ChromePolicySchemaFieldNameList>]
        [formatjson]
```
By default, all Chrome policy schemas are displayed.
* `filter <String>` - Display schemas based on fields like its resource name, description and additionalTargetKeyNames.

By default, all schema fields are displayed.
* `<ChromePolicySchemaFieldName>*` - Specify individual fields
* `fields <ChromePolicySchemaFieldNameList>` - Specify a list of fields

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam print chromeschemas [todrive <ToDriveAttribute>*]
        [filter <String>]
        <ChromePolicySchemaFieldName>* [fields <ChromePolicySchemaFieldNameList>]
        [[formatjson [quotechar <Character>]]

```
By default, all Chrome policy schemas are displayed.
* `filter <String>` - Display schemas based on fields like its resource name, description and additionalTargetKeyNames.

By default, all schema fields are displayed.
* `<ChromePolicySchemaFieldName>*` - Specify individual fields
* `fields <ChromePolicySchemaFieldNameList>` - Specify a list of fields

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Chrome policy schemas in same format as Legacy GAM
```
gam info chromeschema std <SchemaName>
```
Chrome policy schema `<SchemaName>` is displayed.
```
gam show chromeschemas std
        [filter <String>]
```
By default, all Chrome policy schemas are displayed; use `filter <String>` to display a particular schema based on fields like its resource name, description and additionalTargetKeyNames.

Schemas are formatted based on their field types; a schema may have multiple fields.
```
SchemaName: description
  Field: TYPE_ENUM
    Value1: description
    Value2: description
    ...
  Field: TYPE_BOOL
    true: description
    false: description
  Field: TYPE_STRING
    description
  Field: TYPE_LIST
    description
```

## Create a Chrome policy image
You must upload an image file in order to use it in Chrome policies.
* The file must be MIME type image/jpeg and the file size cannot exceed 16384kb bytes.

The data returned by the command can be used in subsequent `gam update chromepolicy` commands.
```
<ChromePolicyImageSchemaName> ::=
        chrome.devices.managedguest.avatar |
        chrome.devices.managedguest.wallpaper |
        chrome.devices.signinwallpaperimage |
        chrome.users.avatar |
        chrome.users.wallpaper

gam create chromepolicyimage <ChromePolicyImageSchemaName> <FileName>
```

## Update Chrome policy
You can update a policy for all devices/users within an OU, users with a group or for a specific printer or application within an OU.
```
gam update chromepolicy [convertcrnl]
        (<SchemaName> ((<Field> <Value>)+ | <JSONData>))+
        ((ou|orgunit <OrgUnitItem>)|(group <GroupItem>))
        [(printerid <PrinterID>)|(appid <AppID>)]
```
You update a schema by specifying its name and one or more fields and values or by using
JSON data to specify the field values. 

### TYPE_ENUM fields
Here is a schema with an TYPE_ENUM field.
```
  Chrome Policy Schema: customers/C03kt1m66/policySchemas/chrome.users.DefaultPrintColor (143/279)
    definition:
      enumType:
        name: DefaultPrintColorEnum
          value:
            name: DEFAULT_PRINT_COLOR_ENUM_UNSPECIFIED
              number: 0
            name: DEFAULT_PRINT_COLOR_ENUM_COLOR
              number: 1
            name: DEFAULT_PRINT_COLOR_ENUM_MONOCHROME
              number: 2
      messageType:
        field:
          label: LABEL_OPTIONAL
            name: printingColorDefault
            number: 1
            type: TYPE_ENUM
            typeName: DefaultPrintColorEnum
          name: DefaultPrintColor
```
When specifying a value for this field you can enter the value in one of two ways:
* `DEFAULT_PRINT_COLOR_ENUM_MONOCHROME` - The full value
* `MONOCHROME` - The text following `..._ENUM_`

### TYPE_STRING fields with carriage returns (\r) and line feeds (\n)
Use the `convertcrnl` option to properly handle these characters
in value strings entered on the command line in the `<Field> <Value>` form. 
```
gam update chromepolicy convertcrnl chrome.devices.DisabledDeviceReturnInstructions
    deviceDisabledMessage "Please return device to:\nSchool\n123 Main Street\nAnytown US" ou /Path/to/OU
```

### Examples
Restrict use of Chromebooks in an OU to a specific list of users.
```
gam update chromepolicy chrome.devices.SignInRestriction deviceAllowNewUsers RESTRICTED_LIST userAllowlist "user1@domain.com,user2@domain.com" ou "<Path/To/Ou>"
```

Restrict use of Chromebooks in an OU to users in a specific domain.
```
gam update chromepolicy chrome.devices.SignInRestriction deviceAllowNewUsers RESTRICTED_LIST userAllowlist "*@domain.com" ou "<Path/To/Ou>"
```

Restrict student users from adding additional printers and set default printing to black and white.
```
gam update chromepolicy chrome.users.UserPrintersAllowed userPrintersAllowed false chrome.users.DefaultPrintColor printingColorDefault MONOCHROME orgunit "/Students" 
gam update chromepolicy chrome.users.UserPrintersAllowed userPrintersAllowed false chrome.users.DefaultPrintColor printingColorDefault DEFAULT_PRINT_COLOR_ENUM_MONOCHROME orgunit "/Students" 
```
For student users, specify that Chrome browsers should be updated to the latest stable Chrome browser version.
```
gam update chromepolicy chrome.users.chromeBrowserUpdates targetVersionPrefixSetting stable-0  orgunit "/Students" 
```
Restrict students from accessing Blocked URLs.
```
gam update chromepolicy chrome.users.UrlBlocking urlBlocklist "https://socialmedia.com,https://videowebsite.com" orgunit "/Students"
```
The Policy API and GAM have no ability to edit lists, you have to supply the complete list.
```
# Get the current policy
gam redirect stdout ./urlBlockList.json show chromepolicies filter chrome.users.UrlBlocking orgunit "/Students" formatjson

# Edit urlBlockList.json to add the new URL(s)
{"additionalTargetKeys": [], "direct": true, "fields": [{"name": "urlBlocklist", "value": "https://socialmedia.com,https://videowebsite.com,https://nogo.com"}, {"name": "chromeInternalUrlsBlocked", "value": false}], "name": "chrome.users.UrlBlocking", "orgUnitPath": "/Students", "parentOrgUnitPath": "/"}

# Update the policy
gam update chromepolicies chrome.users.UrlBlocking json file urlBlockList.json orgunit "/Students"
```
For managed browsers, specify that users can only sign into managed accounts belonging to company/school domains.
```
gam update chromepolicy chrome.users.SecondaryGoogleAccountSignin allowedDomainsForApps company.com,company.net orgunit "/Managed Browsers"
```
Set bookmarks for student users; use JSON data.
```
bookmarks.json
{"fields": [{"name": "managedBookmarks", "value": {"bookmarks": [{"link": {"name": "GMAIL", "url": "https://gmail.com"}}, {"link": {"name": "DRIVE", "url": "https://drive.google.com"}}, {"folder": {"entries": [{"link": {"name": "DOMAIN1", "url": "https://domain1.com"}}, {"folder": {"entries": [{"link": {"name": "DOMAIN2", "url": "https://domain2.com"}}], "name": "Sub Folder"}}], "name": "Top Folder"}}]}}]}

gam update chromepolicy chrome.users.ManagedBookmarksSetting  json file bookmarks.json orgunit "/Students/
```
Allowlist the Google Translate extension for the Students OrgUnit
```
gam update chromepolicy chrome.users.apps.InstallType appInstallType ALLOWED app_id chrome:aapbdbdomjkkjkaonfhkkikfgjllcleb ou "/Students"
```
## Delete Chrome policy
You can delete a policy for all devices/users within an OU, users with a group or for a specific printer or application within an OU.

For policies within an OU, you can only delete direct policies where the same policy exists in the parent OU;
the direct policy in the sub OU is replaced with the inherited policy from the parent OU.
```
gam delete chromepolicy
        (<SchemaName> [<JSONData>])+
        ((ou|orgunit <OrgUnitItem>)|(group <GroupItem>))
        [(printerid <PrinterID>)|(appid <AppID>)]
```

## Delete Chrome app
You can  delete an app, i.e., explicitly remove it from management. `<OrgUnitItem>` must specify where the app was added for management.
```
gam delete chromepolicy chrome.users.apps.InstallType ou|orgunit <OrgUnitItem> appid <AppID>
```

## Display Chrome policies
You can display policies for all devices/users within an OU, users with a group or for a specific printer or application within an OU.

### Display as an indented list of keys and values.
```
gam show chromepolicies
        ((ou|orgunit <OrgUnitItem> [show all|direct|inherited])|(group <GroupItem>))
        [(printerid <PrinterID>)|(appid <AppID>)]
        [filter <StringList>] [namespace <NamespaceList>]
        [show all|direct|inherited]
        [formatjson]
```
By default, all Chrome policies for the OU or group are displayed.
* `filter <StringList>` - Display policies based on fields like its resource name, description and additionalTargetKeyNames.
* `show all` - For OUs, display policies regardless of where set; this is the default
* `show direct` - For OUs, display policies set directly in the OU
* `show inherited` - For OUs, display policies set in a parent OU

These are the default namespaces; use `namespace <NamespaceList>` to override.
* `default` - When OU specified
  * chrome.users
  * chrome.users.apps
  * chrome.users.appsconfig
  * chrome.devices
  * chrome.devices.kiosk
  * chrome.devices.kiosk.apps
  * chrome.devices.managedguest
  * chrome.devices.managedguest.apps
  * chrome.networks.cellular
  * chrome.networks.certificates
  * chrome.networks.ethernet
  * chrome.networks.globalsettings
  * chrome.networks.vpn
  * chrome.networks.wifi
  * chrome.printers
  * chrome.printservers
* `default` - When group specified
  * chrome.users
  * chrome.users.apps
  * chrome.users.appsconfig
  * chrome.printers
  * chrome.printservers
* `appid <AppID>`
  * chrome.users.apps
  * chrome.devices.kiosk.apps
  * chrome.devices.managedGuest.apps
* `printerid <PrinterID>`
  * chrome.printers
                    
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam print chromepolicies [todrive <ToDriveAttribute>*]
        ((ou|orgunit <OrgUnitItem> [show all|direct|inherited])|(group <GroupItem>))
        [(printerid <PrinterID>)|(appid <AppID>)]
        [filter <StringList>] [namespace <NamespaceList>]
        [show all|direct|inherited] [shownopolicy]
        [[formatjson [quotechar <Character>]]
```
By default, all Chrome policies for the OU or group are displayed.
* `filter <StringList>` - Display policies based on fields like its resource name, description and additionalTargetKeyNames.
* `show all` - For OUs, display policies regardless of where set; this is the default
* `show direct` - For OUs, display policies set directly in the OU
* `show inherited` - For OUs, display policies set in a parent OU

Use option `shownopolicy` to display output like the following if no policies apply to the OU or group.
```
gam print chromepolicies ou /Test appid chrome:emidddocikgklceeeifefomdnbkldhng namespace chrome.users.apps shownopolicy 
Getting all Chrome Policies that match query (chrome.users.apps.*) for /Test
Got 0 Chrome Policies that matched query (chrome.users.apps.*) for /Test...
name,orgUnitPath,parentOrgUnitPath,direct,appId
noPolicy,/Test,/,False,chrome:emidddocikgklceeeifefomdnbkldhng
```

These are the default namespaces; use `namespace <NamespaceList>` to override.
* `default`
  * chrome.users
  * chrome.users.apps
  * chrome.devices
  * chrome.devices.kiosk
  * chrome.devices.managedGuest
* `appid <AppID>`
  * chrome.users.apps
  * chrome.devices.kiosk.apps
  * chrome.devices.managedGuest.apps
* `printerid <PrinterID>`
  * chrome.printers
                    
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Copy simple policies set directly in one OU to another OU
Display direct policies, update all
```
gam redirect csv ./ChromePolicies.csv print chromepolicies ou "/Path/To/OU1" show direct
gam config num_threads 1 csv ChromePolicies.csv gam update chromepolicy "~name" "~fields.0.name" "~fields.0.value" "~fields.1.name" "~fields.1.value" ou "/Path/To/OU2"
```
Display all policies, select direct on update
```
gam redirect csv ./ChromePolicies.csv print chromepolicies ou "/Path/To/OU1"
gam config num_threads 1 csv_input_row_filter "direct:boolean:true" csv ChromePolicies.csv gam update chromepolicy "~name" "~fields.0.name" "~fields.0.value" "~fields.1.name" "~fields.1.value" ou "/Path/To/OU2"
```
## Copy simple and complex policies set directly in one OU to another OU
Display direct policies, update all
```
gam redirect csv ./ChromePolicies.csv print chromepolicies ou "/Path/To/OU1" show direct formatjson quotechar "'"
gam config num_threads 1 csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" ou "/Path/To/OU2"
```
Display all policies, select direct on update
```
gam redirect csv ./ChromePolicies.csv print chromepolicies ou "/Path/To/OU1" formatjson quotechar "'"
gam config num_threads 1 csv_input_row_filter "direct:boolean:true" csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" ou "/Path/To/OU2"
```

## Copy simple and complex policies set directly in one OU to multiple other OUs
Display direct policies, update all
```
gam redirect csv ./ChromePolicies.csv print chromepolicies ou "/Path/To/OU1" show direct formatjson quotechar "'"
```
Make a batch file (SetPolicies.bat) with a line for each target OU
```
gam config num_threads 1 csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" ou "/Path/To/OU2"
gam config num_threads 1 csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" ou "/Path/To/OU3"
...
```
Execute batch
```
gam redirect stdout ./SetPolicies.log multiprocess redirect stderr stdout tbatch SetPolicies.bat
```

## Copy simple policies in one Group to another Group
Display all policies, update all
```
gam redirect csv ./ChromePolicies.csv print chromepolicies group group1@domain.com
gam config num_threads 1 csv ChromePolicies.csv gam update chromepolicy "~name" "~fields.0.name" "~fields.0.value" "~fields.1.name" "~fields.1.value" group group2@domain.com
```
## Copy simple and complex policies in one Group to another Group
Display all policies, update all
```
gam redirect csv ./ChromePolicies.csv print chromepolicies group group1@domain.com formatjson quotechar "'"
gam config num_threads 1 csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" group group2@domain.com
```

## Copy simple and complex policies in one Group to multiple other Groups
Display all policies, update all
```
gam redirect csv ./ChromePolicies.csv print chromepolicies group group1@domain.com formatjson quotechar "'"
```
Make a batch file (SetPolicies.bat) with a line for each target group
```
gam config num_threads 1 csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" group group2@domain.com
gam config num_threads 1 csv ChromePolicies.csv quotechar "'" gam update chromepolicy "~name" json "~JSON" group group3@domain.com
...
```
Execute batch
```
gam redirect stdout ./SetPolicies.log multiprocess redirect stderr stdout tbatch SetPolicies.bat
```

## Create Chrome network
See: [Chrome Policy Schema Table](#chrome-policy-schema-table) for the allowed network settings.
* chrome.networks.ethernet.Details: Ethernet network configuration details.
* chrome.networks.vpn.Details: Vpn network configuration details.
* chrome.networks.wifi.Details: Wifi network configuration details.

```
gam create chromenetwork
        <OrgUnitItem> <String> <JSONData>
```
### Create a Chrome network from a JSON data file
```
$ more network.json
{"settings": [
  {"policy_schema": "chrome.networks.wifi.AllowForChromeUsers",
   "value": {"allowForChromeUsers": true}},
  {"policy_schema": "chrome.networks.wifi.AllowForChromeDevices",
   "value": {"allowForChromeDevices": true}},
  {"policy_schema": "chrome.networks.wifi.Details",
   "value": {"details": {"allowIpConfiguration": false,
                         "allowNameServersConfiguration": false,
			 "automaticallyConnect": false,
			 "hiddenSsid": false,
			 "nameServerSelection": "NAME_SERVERS_ENUM_AUTOMATIC",
			 "passphrase": "pw1234",
			 "proxySettings": {"type": "Direct"},
			 "security": "WPA-PSK",
			 "ssid": "Test Wifi"}}}
  ]
}

$ gam create chromenetwork /Test Test file network.json
```
### Create a Chrome network(s) from a local CSV file
The JSON data is in a single column surrounded by single quotes.
```
network.csv
orgUnitPath,name,JSON
/Staff,Staff,'{"settings": [{"policy_schema": "chrome.networks.wifi.AllowForChromeUsers", "value": {"allowForChromeUsers": true}},{"policy_schema": "chrome.networks.wifi.AllowForChromeDevices", "value": {"allowForChromeDevices": true}}, {"policy_schema": "chrome.networks.wifi.Details", "value": {"details": {"allowIpConfiguration": false, "allowNameServersConfiguration": false, "automaticallyConnect": false, "hiddenSsid": false, "nameServerSelection": "NAME_SERVERS_ENUM_AUTOMATIC", "passphrase": "pw1234", "proxySettings": {"type": "Direct"}, "security": "WPA-PSK", "ssid": "Staff Wifi"}}}]}'
/Students,Students,'{"settings": [{"policy_schema": "chrome.networks.wifi.AllowForChromeUsers", "value": {"allowForChromeUsers": true}},{"policy_schema": "chrome.networks.wifi.AllowForChromeDevices", "value": {"allowForChromeDevices": true}}, {"policy_schema": "chrome.networks.wifi.Details", "value": {"details": {"allowIpConfiguration": false, "allowNameServersConfiguration": false, "automaticallyConnect": false, "hiddenSsid": false, "nameServerSelection": "NAME_SERVERS_ENUM_AUTOMATIC", "passphrase": "pw1234", "proxySettings": {"type": "Direct"}, "security": "WPA-PSK", "ssid": "Student Wifi"}}}]}'

$ gam csv network.csv quote_char "'" gam create chromenetwork "~orgUnitPath" "~name" "~JSON"
```

### Create a Chrome network(s) from a Google sheet
The JSON data is in a single column; there are not surrounding single quotes.
```
Google sheet
orgUnitPath,name,JSON
/Staff,Staff,{"settings": [{"policy_schema": "chrome.networks.wifi.AllowForChromeUsers", "value": {"allowForChromeUsers": true}},{"policy_schema": "chrome.networks.wifi.AllowForChromeDevices", "value": {"allowForChromeDevices": true}}, {"policy_schema": "chrome.networks.wifi.Details", "value": {"details": {"allowIpConfiguration": false, "allowNameServersConfiguration": false, "automaticallyConnect": false, "hiddenSsid": false, "nameServerSelection": "NAME_SERVERS_ENUM_AUTOMATIC", "passphrase": "pw1234", "proxySettings": {"type": "Direct"}, "security": "WPA-PSK", "ssid": "Staff Wifi"}}}]}
/Stndents,Students,{"settings": [{"policy_schema": "chrome.networks.wifi.AllowForChromeUsers", "value": {"allowForChromeUsers": true}},{"policy_schema": "chrome.networks.wifi.AllowForChromeDevices", "value": {"allowForChromeDevices": true}}, {"policy_schema": "chrome.networks.wifi.Details", "value": {"details": {"allowIpConfiguration": false, "allowNameServersConfiguration": false, "automaticallyConnect": false, "hiddenSsid": false, "nameServerSelection": "NAME_SERVERS_ENUM_AUTOMATIC", "passphrase": "pw1234", "proxySettings": {"type": "Direct"}, "security": "WPA-PSK", "ssid": "Student Wifi"}}}]}

$ gam csv gsheet user@domain.com <FileID> id:<SheetID> gam create chromenetwork "~orgUnitPath" "~name" "~JSON"
```
## Delete Chrome network
```
gam delete chromenetwork
         <OrgUnitItem> <NetworkID>
```

## Chrome Policy Schema Table
```
chrome.devices.AdvancedBatteryChargeMode: Advanced Charge battery mode.
  advancedBatteryChargeModeEnabled: TYPE_BOOL
    true
    false
  advancedBatteryChargeTimesOfDay
    dailyChargePeriods
      key: TYPE_STRING
      value
        startTime: TYPE_INT32
        endTime: TYPE_INT32

chrome.devices.AllowedBluetoothServices: Bluetooth services allowed.
  deviceAllowedBluetoothServices: TYPE_LIST
    Only allow connection to Bluetooth services in the list. Any services represented by the UUIDs in this list will be allowed. UUIDs can be in short form ('abcd' or '0xabcd') or long form 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'. A list of standard service UUIDs is available at the https://www.bluetooth.com/specifications/assigned-numbers/service-discovery/ Bluetooth SIG Assigned Numbers site. When the list is empty, all services are allowed.

chrome.devices.AllowRedeemChromeOsRegistrationOffers: Redeem offers through ChromeOS registration.
  allowRedeemChromeOsRegistrationOffers: TYPE_BOOL
    true: Allow users to redeem offers through ChromeOS registration.
    false: Prevent users from redeeming offers through ChromeOS Registration.

chrome.devices.AnonymousMetricReporting: Metrics reporting.
  metricsEnabled: TYPE_BOOL
    true: Always send metrics to Google.
    false: Never send metrics to Google.

chrome.devices.AppToPinOsVersion: App-controlled updates.
  appToPinOsVersion: TYPE_STRING
    Allows the admin to control auto update version by choosing an app whose manifest will govern update behavior.

chrome.devices.AutoUpdateSettings: Auto-update settings.
  updateDisabled: TYPE_BOOL
    true: Block updates.
    false: Allow updates.
  rebootAfterUpdate: TYPE_BOOL
    true: Allow auto-reboots.
    false: Disallow auto-reboots.
  autoUpdateAllowedConnectionType: TYPE_ENUM
    WIFI_AND_ETHERNET: Allow automatic updates over Wi-Fi and Ethernet only.
    ALL_CONNECTIONS: Allow automatic updates on all connections, including cellular.
  deviceRollbackToTargetVersion: TYPE_ENUM
    ROLLBACK_DISABLED: Do not roll back OS.
    ROLLBACK_AND_RESTORE_IF_POSSIBLE: Roll back OS.
  autoUpdateRolloutPlan
    plan: TYPE_ENUM
      DEFAULT_UPDATES:
      SCATTER_UPDATES:
      SCHEDULE_UPDATES:
    stages
      days: TYPE_INT32
      percentage: TYPE_INT32
    scatter: TYPE_ENUM
      NO_SCATTER_FACTOR:
      ONE_DAY:
      TWO_DAYS:
      THREE_DAYS:
      FOUR_DAYS:
      FIVE_DAYS:
      SIX_DAYS:
      SEVEN_DAYS:
      EIGHT_DAYS:
      NINE_DAYS:
      TEN_DAYS:
      ELEVEN_DAYS:
      TWELVE_DAYS:
      THIRTEEN_DAYS:
      FOURTEEN_DAYS:
  autoUpdateTimeRestrictions
    timeRestriction
      start
        dayOfWeek: TYPE_ENUM
          MONDAY:
          TUESDAY:
          WEDNESDAY:
          THURSDAY:
          FRIDAY:
          SATURDAY:
          SUNDAY:
        hours: TYPE_INT32
        minutes: TYPE_INT32
      end
        dayOfWeek: TYPE_ENUM
          MONDAY:
          TUESDAY:
          WEDNESDAY:
          THURSDAY:
          FRIDAY:
          SATURDAY:
          SUNDAY:
        hours: TYPE_INT32
        minutes: TYPE_INT32
  autoUpdateTargetVersionLts
    selectedVersion
      displayName: TYPE_STRING
  deviceMinimumVersionAueMessage: TYPE_STRING
    Final automatic update alert message. When a device reaches its last automatic update(https://support.google.com/chrome/a/answer/6220366)automatic , an alert is sent to the user. This text overrides the default message that will be shown on the device.
  deviceMinimumVersion
    chromeosVersion: TYPE_STRING
    aueWarningPeriodDays: TYPE_INT64
    warningPeriodDays: TYPE_INT64
  autoUpdateHttpDownloadsEnabled: TYPE_BOOL
    true: Use HTTP for update downloads.
    false: Use HTTPS for update downloads.
  releaseChannelWithLts: TYPE_ENUM
    ALLOW_USER_CHOICE: Allow user to configure.
    STABLE_CHANNEL: Stable channel.
    BETA_CHANNEL: Beta channel.
    LTS_CHANNEL: Long-term support channel.
    LTC_CHANNEL: Long-term support candidate channel.
    DEV_CHANNEL: Dev channel (may be unstable).
  deviceAutoUpdatePeerToPeerEnabled: TYPE_BOOL
    true: Allow peer to peer auto update downloads.
    false: Do not allow peer to peer auto update downloads.

chrome.devices.Bluetooth: Bluetooth.
  allowBluetooth: TYPE_BOOL
    true: Do not disable Bluetooth.
    false: Disable Bluetooth.

chrome.devices.BootOnAc: Boot on AC.
  bootOnAcEnabled: TYPE_BOOL
    true: Enable boot on AC.
    false: Disable boot on AC.

chrome.devices.ContentProtection: Allow web services to request proof that the device is running an unmodified version of ChromeOS that is policy compliant.
  contentProtectionEnabled: TYPE_BOOL
    true: Ensures ChromeOS devices in your organization will verify their identity to content providers.
    false: Does not ensure ChromeOS devices in your organization will verify their identity to content providers. Some premium content may be unavailable to your users.

chrome.devices.DeviceAllowEnterpriseRemoteAccessConnections: Enterprise remote access connections.
  deviceAllowEnterpriseRemoteAccessConnections: TYPE_BOOL
    true: Enable remote access connections from enterprise admins.
    false: Prevent remote access connections from enterprise admins.

chrome.devices.DeviceAuthenticationFlowAutoReloadInterval: Automatic online sign-in / lock screen refresh.
  deviceAuthenticationFlowAutoReloadInterval: TYPE_INT64

chrome.devices.DeviceAuthenticationUrlAllowlist: Blocked URL exceptions on the sign-in / lock screens.
  deviceAuthenticationUrlAllowlist: TYPE_LIST
    Blocked URL exceptions. Any URL that matches an entry in this exception list will be allowed, even if it matches a line in the blocked URLs. Wildcards ("*") are allowed when appended to a URL, but cannot be entered alone. Maximum of 1000 URLs.

chrome.devices.DeviceAuthenticationUrlBlocklist: Blocked URLs on the sign-in / lock screens.
  deviceAuthenticationUrlBlocklist: TYPE_LIST
    Blocked URLs. Any URL in this list will be blocked, unless it also appears in the list of exceptions in the corresponding allowlist.

chrome.devices.DeviceAutofillSamlUsername: Autofill username on SAML IdP login page.
  deviceAutofillSamlUsername: TYPE_STRING
    URL parameter name. Specify the URL parameter name which will be used on IdP login page to autofill the username field. See the help center article for some examples of fitting URL parameters. Warning: ChromeOS user's email will be used to autofill the username field, so do not use this policy if a different username should be used on IdP login page. This policy is only relevant if SAML SSO has been configured for Chrome Devices.

chrome.devices.DeviceBatteryCharge: Primary battery charge configuration.
  batteryChargeMode: TYPE_ENUM
    STANDARD: Standard.
    ADAPTIVE: Adaptive.
    EXPRESS_CHARGE: Express Charge.
    PRIMARILY_AC_USE: Primarily AC.
    CUSTOM: Custom.
  customBatteryChargeStart: TYPE_INT64
    min 50; max 95. Start charging when the battery drop below (% available charge).
  customBatteryChargeStop: TYPE_INT64
    min 55; max 100. Stop charging when the battery goes above (% available charge).

chrome.devices.DeviceChargingSoundsEnabled: Charging Sounds.
  deviceChargingSoundsEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable charging sounds.
    TRUE: Enable charging sounds.

chrome.devices.DeviceDebugPacketCaptureAllowed: Debug network packet captures.
  deviceDebugPacketCaptureAllowed: TYPE_BOOL
    true: Allow user to perform network packet captures.
    false: Do not allow user to perform network packet captures.

chrome.devices.DeviceDlcPredownloadList: Preload peripheral drivers.
  deviceDlcPredownloadList: TYPE_LIST
    scanner_drivers: Scanners.

chrome.devices.DeviceExtendedAutoUpdateEnabled: Extended auto-updates.
  deviceExtendedAutoUpdateEnabled: TYPE_BOOL
    true: Allow updates during extended auto-update period.
    false: Disallow updates during extended auto-update period.

chrome.devices.DeviceExtensionsSystemLogEnabled: Extensions system logging.
  deviceExtensionsSystemLogEnabled: TYPE_BOOL
    true: Enable enterprise extensions system logging.
    false: Disable enterprise extensions system logging.

chrome.devices.DeviceFlexHwDataForProductImprovementEnabled: Additional hardware data on ChromeOS Flex.
  deviceFlexHwDataForProductImprovementEnabled: TYPE_BOOL
    true: Send additional hardware data on ChromeOS Flex.
    false: Do not send additional hardware data on ChromeOS Flex.

chrome.devices.DeviceHardwareVideoDecodingEnabled: Hardware video acceleration.
  deviceHardwareVideoDecodingEnabled: TYPE_BOOL
    true: Enable hardware video decoding.
    false: Disable hardware video decoding.

chrome.devices.DeviceInternationalizationShortcutsEnabled: International keyboard shortcuts mapping.
  deviceInternationalizationShortcutsEnabled: TYPE_BOOL
    true: International keyboard shortcuts are mapped to the location of the keys on the keyboard.
    false: International keyboard shortcuts are mapped to the glyph of the keys.

chrome.devices.DeviceKeyboardBacklightColor: Default keyboard backlight color.
  deviceKeyboardBacklightColor: TYPE_ENUM
    BACKLIGHT_WHITE: White.
    BACKLIGHT_RED: Red.
    BACKLIGHT_YELLOW: Yellow.
    BACKLIGHT_GREEN: Green.
    BACKLIGHT_BLUE: Blue.
    BACKLIGHT_INDIGO: Indigo.
    BACKLIGHT_PURPLE: Purple.
    BACKLIGHT_RAINBOW: Rainbow.

chrome.devices.DeviceKeylockerForStorageEncryptionEnabled: Enable Key Locker.
  keylockerForStorageEncryptionEnabled: TYPE_BOOL
    true: Use Key Locker with the encryption algorithm for user storage encryption, if supported.
    false: Do not use Key Locker with the encryption algorithm for user storage encryption.

chrome.devices.DeviceLoginScreenAutocompleteDomainGroup: Autocomplete domain.
  loginScreenDomainAutoComplete: TYPE_BOOL
    true: Use the domain name set in the field 'loginScreenDomainAutoCompletePrefix' for autocomplete at sign-in.
    false: Do not display an autocomplete domain on the sign-in screen.
  loginScreenDomainAutoCompletePrefix: TYPE_STRING
    Autocomplete domain prefix. Specifies the domain name to autocomplete on a managed ChromeOS device.

chrome.devices.DeviceLoginScreenAutoSelectCertificateForUrls: Single sign-on client certificates.
  deviceLoginScreenAutoSelectCertificateForUrls: TYPE_LIST
    Automatically select client certificate for these single sign-on sites. Please refer to the support url for the format of this setting.

chrome.devices.DeviceLoginScreenExtensionManifestVTwoAvailability: Manifest v2 extension availability on sign-in screen.
  deviceLoginScreenExtensionManifestVTwoAvailability: TYPE_ENUM
    DEFAULT: Default device behavior.
    DISABLE: Disable manifest V2 extensions on the sign-in screen.
    ENABLE: Enable manifest V2 extensions on the sign-in screen.
    ENABLE_FOR_FORCED_EXTENSIONS: Enable force-installed manifest V2 extensions on the sign-in screen.

chrome.devices.DeviceLoginScreenPrivacyScreenEnabled: Privacy screen on sign-in screen.
  deviceLoginScreenPrivacyScreenEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Always disable the privacy screen on sign-in screen.
    TRUE: Always enable the privacy screen on sign-in screen.

chrome.devices.DeviceLoginScreenPromptOnMultipleMatchingCertificates: Prompt when multiple certificates match on the sign-in screen.
  deviceLoginScreenPromptOnMultipleMatchingCertificates: TYPE_BOOL
    true: Prompt the user to select the client certificate whenever the auto-selection policy matches multiple certificates on the sign-in screen.
    false: Do not prompt the user to select a client certificate on the sign-in screen.

chrome.devices.DeviceLoginScreenSystemInfoEnforced: System info on sign-in screen.
  deviceLoginScreenSystemInfoEnforced: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not allow users to display system information on the sign-in screen.
    TRUE: Always display system information on the sign-in screen.

chrome.devices.DeviceLoginScreenWebHidAllowDevicesForUrls: WebHID API allowed devices on sign-in screen.
  deviceLoginScreenWebHidAllowDevicesForUrls
    webOrigin
      url: TYPE_STRING
      device: TYPE_LIST

chrome.devices.DeviceLoginScreenWebUsbAllowDevicesForUrls: WebUSB API allowed devices on sign-in screen.
  deviceLoginScreenWebUsbAllowDevicesForUrls
    webApplications
      url: TYPE_STRING
      devices: TYPE_LIST

chrome.devices.DeviceLowBatterySoundEnabled: Low Battery Sound.
  deviceLowBatterySoundEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable low battery sound.
    TRUE: Enable low battery sound.

chrome.devices.DeviceNativeClientForceAllowed: Native Client (NaCl).
  deviceNativeClientForceAllowed: TYPE_BOOL
    true: Allow Native Client to run even if it is disabled by default.
    false: Use default behavior.

chrome.devices.DevicePciPeripheralDataAccessEnabled: Data access protection for peripherals.
  devicePciPeripheralDataAccessEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Enable data access protection.
    TRUE: Disable data access protection.

chrome.devices.DevicePostQuantumKeyAgreementEnabled: Post-quantum TLS.
  devicePostQuantumKeyAgreementEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow post-quantum key agreement in TLS connections.
    TRUE: Allow post-quantum key agreement in TLS connections.

chrome.devices.DevicePowerBatteryChargingOptimization: Battery charging optimization.
  devicePowerBatteryChargingOptimization: TYPE_ENUM
    UNSET: Allow the user to decide.
    STANDARD: Enforce standard charging.
    ADAPTIVE: Enforce adaptive charging.
    LIMITED: Enforce limited charging.

chrome.devices.DevicePowerwashAllowed: Powerwash.
  devicePowerwashAllowed: TYPE_BOOL
    true: Allow powerwash to be triggered.
    false: Do not allow powerwash to be triggered.

chrome.devices.DevicePrintingClientNameTemplate: Internet Printing Protocol client-name attribute.
  devicePrintingClientNameTemplate: TYPE_STRING
    Template for the client-name attribute. Set the 'client-name' value to be passed to IPP (Internet Printing Protocol) print destinations in print job creation requests.The following variables can be used: ${DEVICE_DIRECTORY_API_ID}, ${DEVICE_SERIAL_NUMBER} ${DEVICE_ASSET_ID} and ${DEVICE_ANNOTATED_LOCATION}.

chrome.devices.DeviceRebootOnUserSignout: Reboot on sign-out.
  deviceRebootOnUserSignout: TYPE_ENUM
    NEVER: Do not reboot on user sign-out.
    ARC_SESSION: Reboot on user sign-out if Android has started.
    ALWAYS: Always reboot on user sign-out.
    VM_STARTED_OR_ARC_SESSION: Reboot on user sign-out if Android or a VM has started.

chrome.devices.DeviceReportXdrEvents: Report extended detection and response (XDR) events.
  deviceReportXdrEvents: TYPE_BOOL
    true: Report information about extended detection and response (XDR) events.
    false: Do not report information about extended detection and response (XDR) events.

chrome.devices.DeviceRestrictedManagedGuestSessionEnabled: Shared kiosk mode.
  deviceRestrictedManagedGuestSessionEnabled: TYPE_BOOL
    true: Enable shared kiosk mode.
    false: Disable shared kiosk mode.

chrome.devices.DeviceRestrictionSchedule: Device restriction schedule.
  deviceRestrictionSchedule
    timeWindows
      start
        dayOfWeek: TYPE_ENUM
          MONDAY:
          TUESDAY:
          WEDNESDAY:
          THURSDAY:
          FRIDAY:
          SATURDAY:
          SUNDAY:
        hours: TYPE_INT32
        minutes: TYPE_INT32
      end
        dayOfWeek: TYPE_ENUM
          MONDAY:
          TUESDAY:
          WEDNESDAY:
          THURSDAY:
          FRIDAY:
          SATURDAY:
          SUNDAY:
        hours: TYPE_INT32
        minutes: TYPE_INT32

chrome.devices.DeviceScheduledReboot: Scheduled reboot.
  deviceScheduledRebootEnabled: TYPE_BOOL
    true: Enable scheduled reboots.
    false: Disable scheduled reboots.
  deviceScheduledRebootTimeOfDay
    timeOfDay
      hours: TYPE_INT32
      minutes: TYPE_INT32
      seconds: TYPE_INT32
      nanos: TYPE_INT32
  deviceScheduledRebootFrequency: TYPE_ENUM
    DAILY: Reboot daily.
    WEEKLY: Reboot weekly.
    MONTHLY: Reboot monthly.
  deviceScheduledRebootDayOfWeek: TYPE_ENUM
    MONDAY: Reboot on Mondays.
    TUESDAY: Reboot on Tuesdays.
    WEDNESDAY: Reboot on Wednesdays.
    THURSDAY: Reboot on Thursdays.
    FRIDAY: Reboot on Fridays.
    SATURDAY: Reboot on Saturdays.
    SUNDAY: Reboot on Sundays.
  deviceScheduledRebootDayOfMonth: TYPE_INT64
    Sets a day of the month for device scheduled reboots to occur.

chrome.devices.DeviceScreensaverLoginScreenEnabled: Screen saver.
  deviceScreensaverLoginScreenEnabled: TYPE_BOOL
    true: Display screen saver when idle.
    false: Don't display screen saver when idle.
  deviceScreensaverLoginScreenImages: TYPE_LIST
    Screen saver image URLs. Enter one URL per line. Images must be in JPG format(.jpg or .jpeg files.
  deviceScreensaverLoginScreenIdleTimeoutSeconds: TYPE_INT64
  deviceScreensaverLoginScreenImageDisplayIntervalSeconds: TYPE_INT64

chrome.devices.DeviceScreenSettings: Screen settings.
  allowUserDisplayChanges: TYPE_BOOL
    true: Allow users to overwrite predefined display settings (recommended).
    false: Do not allow user changes for predefined display settings.
  externalUseNativeResolution: TYPE_BOOL
    true: Always use native resolution.
    false: Use custom resolution.
  externalDisplayWidth: TYPE_INT64
    External display width (in pixels). Specifies the preferred width (in pixels) of any external monitor connected to a managed Chromebook.
  externalDisplayHeight: TYPE_INT64
    External display height (in pixels). Specifies the preferred height (in pixels) of any external monitor connected to a managed Chromebook.
  externalDisplayScale: TYPE_ENUM
    EXTERNAL_SCALE_NOT_SET: Not set.
    EXTERNAL_SCALE_50_PERCENT: 50%.
    EXTERNAL_SCALE_55_PERCENT: 55%.
    EXTERNAL_SCALE_60_PERCENT: 60%.
    EXTERNAL_SCALE_65_PERCENT: 65%.
    EXTERNAL_SCALE_70_PERCENT: 70%.
    EXTERNAL_SCALE_75_PERCENT: 75%.
    EXTERNAL_SCALE_80_PERCENT: 80%.
    EXTERNAL_SCALE_85_PERCENT: 85%.
    EXTERNAL_SCALE_90_PERCENT: 90%.
    EXTERNAL_SCALE_95_PERCENT: 95%.
    EXTERNAL_SCALE_100_PERCENT: 100%.
    EXTERNAL_SCALE_105_PERCENT: 105%.
    EXTERNAL_SCALE_110_PERCENT: 110%.
    EXTERNAL_SCALE_115_PERCENT: 115%.
    EXTERNAL_SCALE_120_PERCENT: 120%.
    EXTERNAL_SCALE_125_PERCENT: 125%.
    EXTERNAL_SCALE_130_PERCENT: 130%.
    EXTERNAL_SCALE_135_PERCENT: 135%.
    EXTERNAL_SCALE_140_PERCENT: 140%.
    EXTERNAL_SCALE_145_PERCENT: 145%.
    EXTERNAL_SCALE_150_PERCENT: 150%.
  internalDisplayScale: TYPE_ENUM
    INTERNAL_SCALE_NOT_SET: Not set.
    INTERNAL_SCALE_50_PERCENT: 50%.
    INTERNAL_SCALE_55_PERCENT: 55%.
    INTERNAL_SCALE_60_PERCENT: 60%.
    INTERNAL_SCALE_65_PERCENT: 65%.
    INTERNAL_SCALE_70_PERCENT: 70%.
    INTERNAL_SCALE_75_PERCENT: 75%.
    INTERNAL_SCALE_80_PERCENT: 80%.
    INTERNAL_SCALE_85_PERCENT: 85%.
    INTERNAL_SCALE_90_PERCENT: 90%.
    INTERNAL_SCALE_95_PERCENT: 95%.
    INTERNAL_SCALE_100_PERCENT: 100%.
    INTERNAL_SCALE_105_PERCENT: 105%.
    INTERNAL_SCALE_110_PERCENT: 110%.
    INTERNAL_SCALE_115_PERCENT: 115%.
    INTERNAL_SCALE_120_PERCENT: 120%.
    INTERNAL_SCALE_125_PERCENT: 125%.
    INTERNAL_SCALE_130_PERCENT: 130%.
    INTERNAL_SCALE_135_PERCENT: 135%.
    INTERNAL_SCALE_140_PERCENT: 140%.
    INTERNAL_SCALE_145_PERCENT: 145%.
    INTERNAL_SCALE_150_PERCENT: 150%.

chrome.devices.DeviceSecondFactorAuthentication: Integrated FIDO second factor.
  secondFactorAuthentication: TYPE_ENUM
    UNSET: Allow the user to decide.
    DISABLED: Disable integrated second factor.
    U2F: Enable integrated second factor.

chrome.devices.DeviceShowNumericKeyboardForPassword: Show numeric keyboard for password.
  deviceShowNumericKeyboardForPassword: TYPE_BOOL
    true: Default to a numeric keyboard for password input.
    false: Default to a standard keyboard for password input.

chrome.devices.DeviceSwitchFunctionKeysBehaviorEnabled: Function keys behavior.
  deviceSwitchFunctionKeysBehaviorEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Prevent the launcher/search key from changing the behavior of function keys.
    TRUE: Allow the launcher/search key to change the behavior of function keys.

chrome.devices.DeviceSystemWideTracingEnabled: System-wide performance trace collection.
  deviceSystemWideTracingEnabled: TYPE_BOOL
    true: Allow users to collect a system-wide performance trace.
    false: Prevent users from collecting a system-wide performance trace.

chrome.devices.DeviceUpdateDeviceAttributes: Asset identifier input after zero touch enrollment.
  allowToUpdateDeviceAttributes: TYPE_BOOL
    true: Allow asset ID and location to be entered for devices enrolled via zero touch enrollment.
    false: Do not allow asset ID and location to be entered for devices enrolled via zero touch enrollment.

chrome.devices.DeviceVerifiedMode: Verified mode.
  deviceVerifiedModeRequired: TYPE_BOOL
    true: Require verified mode boot for verified access.
    false: Skip boot mode check for verified access.
  servicesWithFullAccess: TYPE_LIST
    Services with full access. Service accounts which are allowed to receive device ID.
  servicesWithLimitedAccess: TYPE_LIST
    Services with limited access. Service accounts which can verify devices but do not receive device ID.

chrome.devices.DeviceWebBasedAttestationAllowedUrls: Single sign-on verified access.
  deviceWebBasedAttestationAllowedUrls: TYPE_LIST
    Allowed IdP redirect URLs. Enter the list of URLs that you want to be able to perform a verified access check during SAML authentication.

chrome.devices.DeviceWilcoDtc: Dell SupportAssist.
  deviceWilcoDtcAllowed: TYPE_BOOL
    true: Enable Dell SupportAssist.
    false: Disable Dell SupportAssist.
  ackNoticeForDeviceWilcoDtcAllowedSetToTrue: TYPE_BOOL
    This field must be set to true to acknowledge the notice message associated with the field 'device_wilco_dtc_allowed' set to value 'true'. Please sse the notices listed with this policy for more information.
  deviceWilcoDtcConfiguration
    downloadUri: TYPE_STRING
  installSupportAssistApp: TYPE_BOOL
    true: Force-install the Dell SupportAssist app for Dell devices.
    false: Do not automatically install the Dell SupportAssist app.

chrome.devices.DisabledDeviceReturnInstructions: Disabled device return instructions.
  deviceDisabledMessage: TYPE_STRING
    Disabled device return instructions. Custom text to display under the device locked message. We recommend including a return address and contact phone number in your message.

chrome.devices.DockMacAddress: MAC address pass through.
  dockMacAddressSource: TYPE_ENUM
    DEVICE_DOCK_MAC_ADDRESS: Use pre-assigned MAC address.
    DEVICE_NIC_MAC_ADDRESS: Use Chromebook built-in MAC address.
    DOCK_NIC_MAC_ADDRESS: Use dock built-in MAC address.

chrome.devices.EnableGranularDeviceHardwareReporting: Report device hardware information.
  reportingHardwareInfoBehavior: TYPE_ENUM
    REPORTING_DISABLE_ALL: Disable all hardware information reporting.
    REPORTING_ENABLE_ALL: Enable all hardware information reporting.
    REPORTING_CUSTOM_WITH_ALLOWLIST: Customize.
  reportHardwareInfoCustomAllowlist: TYPE_LIST
    report_vpd_info: Device vital product data info.
    report_system_info: Device system information.
    report_timezone_info: Device timezone status.

chrome.devices.EnableGranularDeviceOsReporting: Report device OS information.
  reportingOsInfoBehavior: TYPE_ENUM
    REPORTING_DISABLE_ALL: Disable all OS reporting.
    REPORTING_ENABLE_ALL: Enable all OS reporting.
    REPORTING_CUSTOM_WITH_ALLOWLIST: Customize.
  reportOsInfoCustomAllowlist: TYPE_LIST
    report_version_info: OS version info.
    report_boot_mode: OS boot mode.
    report_os_update_status: OS update status.

chrome.devices.EnableGranularDeviceTelemetryReporting: Report device telemetry.
  reportingTelemetryBehavior: TYPE_ENUM
    REPORTING_DISABLE_ALL: Disable all telemetry reporting.
    REPORTING_ENABLE_ALL: Enable all telemetry reporting.
    REPORTING_CUSTOM_WITH_ALLOWLIST: Customize.
  reportTelemetryCustomAllowlist: TYPE_LIST
    report_hardware_status: Hardware status (deprecated).
    report_network_interfaces: Network interface (deprecated).
    report_network_configuration: Network configuration.
    report_network_status: Network status.
    report_network_events: Network events.
    report_activity_times: Device activity status.
    report_power_status: Power status.
    report_storage_status: Storage status.
    report_board_status: Board status.
    report_cpu_info: CPU status.
    report_graphics_status: Graphics status.
    report_audio_status: Audio status.
    report_crash_report_info: Crash information.
    report_memory_info: Memory status.
    report_backlight_info: Backlight status.
    report_bluetooth_info: Bluetooth status.
    report_fan_info: Fan status.
    report_login_logout: Login/Logout status.
    report_crd_sessions: CRD sessions.
    report_security_status: Security status.
    report_peripherals: USB Peripherals Status.
    device_activity_heartbeat_enabled: Device activity heartbeat.
    report_runtime_counters: Device runtime counter.

chrome.devices.EnableReportDeviceKioskSession: Report kiosk session status.
  reportDeviceSessionStatus: TYPE_BOOL
    true: Enable kiosk session status reporting.
    false: Disable kiosk session status reporting.

chrome.devices.EnableReportDevicePrintJobs: Report device print jobs.
  reportDevicePrintJobs: TYPE_BOOL
    true: Enable print jobs reporting.
    false: Disable print jobs reporting.

chrome.devices.EnableReportDeviceRunningKioskApp: Report the running kiosk app.
  reportDeviceRunningKioskApp: TYPE_BOOL
    true: Enable the running kiosk app reporting.
    false: Disable the running kiosk app reporting.

chrome.devices.EnableReportDeviceUsers: Report device user tracking.
  reportDeviceUsers: TYPE_BOOL
    true: Enable tracking recent users.
    false: Disable tracking recent users.

chrome.devices.EnableReportUploadFrequency: Device status report upload frequency.
  reportDeviceUploadFrequency: TYPE_INT64

chrome.devices.EnableReportUploadFrequencyV2: Device status report upload frequency.
  reportDeviceUploadFrequency: TYPE_INT64

chrome.devices.ExtensionCacheSize: Apps and extensions cache size.
  extensionCacheSize: TYPE_INT64

chrome.devices.ForcedReenrollment: Forced re-enrollment.
  reenrollmentMode: TYPE_ENUM
    AUTO_REENROLLMENT: Force device to automatically re-enroll after wiping.
    MANUAL_REENROLLMENT: Force device to re-enroll with user credentials after wiping.
    NO_REENROLLMENT: Do not force device to re-enroll after wiping.

chrome.devices.GuestMode: Guest mode.
  guestModeEnabled: TYPE_BOOL
    true: Allow guest mode.
    false: Disable guest mode.

chrome.devices.HostnameTemplate: Device network hostname template.
  deviceHostnameTemplate: TYPE_STRING
    Device network hostname template. Select the hostname that is passed to the DHCP server with the DHCP request. Possible variables are ${ASSET_ID}, ${SERIAL_NUM}, ${MAC_ADDR}, ${MACHINE_NAME}, and ${LOCATION}.

chrome.devices.Imprivata: Imprivata login screen integration.
  imprivataIntegrationEnabled: TYPE_BOOL
    true: Use the Imprivata extension on the login screen.
    false: Do not use the Imprivata extension on the login screen.
  ackNoticeForImprivataIntegrationEnabledSetToTrue: TYPE_BOOL
    This field must be set to true to acknowledge the notice message associated with the field 'imprivata_integration_enabled' set to value 'true'. Please sse the notices listed with this policy for more information.
  imprivataExtensionConfiguration
    downloadUri: TYPE_STRING
  imprivataVersion: TYPE_ENUM
    IMPRIVATA_EXTENSION_VERSION_STABLE_OS: Bundled with ChromeOS (recommended).
    IMPRIVATA_EXTENSION_VERSION_M81: Pinned to v1 (Compatible with Chrome 81+).
    IMPRIVATA_EXTENSION_VERSION_M86: Pinned to v2 (Compatible with Chrome 86+).
    IMPRIVATA_EXTENSION_VERSION_3: Pinned to v3 (Compatible with Chrome 97+).
    IMPRIVATA_EXTENSION_VERSION_4: Pinned to v4 (Compatible with Chrome 118+).

chrome.devices.InactiveDeviceNotifications: Inactive device notifications.
  notificationEnabled: TYPE_BOOL
    true: Enable inactive device notifications.
    false: Disable inactive device notifications.
  numDaysConsideredInactive: TYPE_INT64
    Inactive range (days). Devices that have "Last Sync" time beyond this range are considered inactive.
  cadence: TYPE_INT64
    Notification cadence (days). Send me an inactive device report with this frequency.
  emailsToNotify: TYPE_LIST
    Email addresses to receive notification reports. Enter a list of email addresses to receive inactive device reports (one address per line). This field requires at least one element.

chrome.devices.kiosk.AccessibilityShortcutsEnabled: Kiosk accessibility shortcuts.
  accessibilityShortcutsEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable accessibility shortcuts.
    ACCESSIBILITY_ENABLED: Enable accessibility shortcuts.

chrome.devices.kiosk.AcPowerSettings: AC Kiosk power settings.
  acIdleTimeout: TYPE_INT64
  acWarningTimeout: TYPE_INT64
  acIdleAction: TYPE_ENUM
    IDLE_ACTION_SUSPEND: Sleep.
    IDLE_ACTION_LOGOUT: Logout.
    IDLE_ACTION_SHUTDOWN: Shutdown.
    IDLE_ACTION_DO_NOTHING: Do nothing.
  acDimTimeout: TYPE_INT64
  acScreenOffTimeout: TYPE_INT64

chrome.devices.kiosk.AcPowerSettingsV2: AC Kiosk power settings.
  acIdleTimeout: TYPE_INT64
  acWarningTimeout: TYPE_INT64
  acIdleAction: TYPE_ENUM
    IDLE_ACTION_SUSPEND: Sleep.
    IDLE_ACTION_LOGOUT: Logout.
    IDLE_ACTION_SHUTDOWN: Shutdown.
    IDLE_ACTION_DO_NOTHING: Do nothing.
  acDimTimeout: TYPE_INT64
  acScreenOffTimeout: TYPE_INT64

chrome.devices.kiosk.Alerting: Kiosk device status alerting delivery.
  deviceStatusAlertDeliveryModes: TYPE_LIST
    EMAIL: Receive alerts via email.
    SMS: Receive alerts via SMS.

chrome.devices.kiosk.AlertingContactInfo: Kiosk device status alerting contact info.
  alertingEmail: TYPE_LIST
    Alerting emails. Email addresses (e.g. user@example.com).
  alertingMobilePhone: TYPE_LIST
    Alerting mobile phones. Phone numbers (e.g. +1XXXYYYZZZZ, +1AAABBBCCCC).

chrome.devices.kiosk.apps.ChromeExtensionsForWebApps: Allows setting of chrome extensions for web apps.
  chromeExtensionsForWebApps
    appId: TYPE_STRING
    configJson: TYPE_STRING
    url: TYPE_STRING
    allowedEnterpriseChallenge: TYPE_BOOL

chrome.devices.kiosk.apps.ForceInstall: Force installs the app. Note: It's required in order to add an App or Extension to the set of managed apps & extensions of an Organizational Unit.
  forceInstall: TYPE_BOOL
    true: Force install the app.
    false: Do not force install the app.

chrome.devices.kiosk.apps.FunctionKeys: Allows setting Function Keys.
  allowFunctionKeys: TYPE_BOOL
    Sets the top row of the keyboard as Function keys.

chrome.devices.kiosk.apps.InstallationUrlV2: Specifies the url from which to install a self hosted Chrome Extension.
  installationUrl: TYPE_STRING
    The url from which to install a self hosted Chrome Extension.

chrome.devices.kiosk.apps.KioskBrowserPermissionsAllowedForOrigins: Allows setting of additional origins to access browser permissions and device attributes API (if enabled) for web app.
  kioskBrowserPermissionsAllowedOrigins: TYPE_LIST
    The list of additional origins to access browser permissions and device attributes API (if enabled) for web app.

chrome.devices.kiosk.apps.KioskWebAppOfflineEnabled: Allow setting whether the web app can run offline.
  kioskWebAppOfflineEnabled: TYPE_BOOL
    Controls whether a kiosk web app is offline enabled or not.

chrome.devices.kiosk.apps.ManagedConfiguration: Allows setting of the managed configuration.
  managedConfiguration: TYPE_STRING
    Sets the managed configuration JSON format.

chrome.devices.kiosk.apps.Plugins: Allows setting Plugins.
  allowPlugins: TYPE_BOOL
    Controls whether a Kiosk app is allowed to use Plug-ins.

chrome.devices.kiosk.apps.PowerManagement: Allows setting Power Management.
  allowPowerManagement: TYPE_BOOL
    Controls whether a Kiosk app is allowed to manage power.

chrome.devices.kiosk.apps.UnifiedDesktop: Allows setting Unified Desktop.
  enableUnifiedDesktop: TYPE_BOOL
    Controls whether a Kiosk app is allowed to use Unified Desktop.

chrome.devices.kiosk.apps.VirtualKeyboard: Allows setting Virtual Keyboard.
  allowVirtualKeyboard: TYPE_BOOL
    Controls whether a Kiosk app is allowed to use Virtual Keyboard.

chrome.devices.kiosk.appsconfig.AutoLaunchApp: Allows setting of the auto-launch app.
  appId: TYPE_STRING
    Id of the app prefixed with one of either "chrome:" or "web:", depending on the app type. For Chrome apps, the app id can be found on the Chrome Web Store, example: "chrome:aapbdbdomjkkjkaonfhkkikfgjllcleb". For Web apps, the app id is simply the URL, example: "web:https://translate.google.com".
  enableHealthMonitoring: TYPE_BOOL
    Enables health monitoring of the auto launch app, which will alert you if it crashes.
  screenRotation: TYPE_ENUM
    ROTATE_0: Rotate by 0 degrees.
    ROTATE_90: Rotate by 90 degrees.
    ROTATE_180: Rotate by 180 degrees.
    ROTATE_270: Rotate by 270 degrees.
    UNSET: Allow the device to set screen rotation.
  enableSystemLogUpload: TYPE_BOOL
    true: Enables system log upload of the auto launch app.
    false: Disables system log upload of the auto launch app.
  ackNoticeForEnableSystemLogUploadSetToTrue: TYPE_BOOL
    This field must be set to true to acknowledge the notice message associated with the field 'enable_system_log_upload' set to value 'true'. Please sse the notices listed with this policy for more information.
  enableAutoLoginBailout: TYPE_BOOL
    Enables auto login bailout for the auto launch app.
  promptForNetworkWhenOffline: TYPE_BOOL
    Enables prompting for network if auto launch app is offline.

chrome.devices.kiosk.AutoclickEnabled: Kiosk auto-click enabled.
  autoclickEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable auto-click.
    ACCESSIBILITY_ENABLED: Enable auto-click.

chrome.devices.kiosk.BatteryPowerSettings: Battery Kiosk power settings.
  batteryIdleTimeout: TYPE_INT64
  batteryWarningTimeout: TYPE_INT64
  batteryIdleAction: TYPE_ENUM
    IDLE_ACTION_SUSPEND: Sleep.
    IDLE_ACTION_LOGOUT: Logout.
    IDLE_ACTION_SHUTDOWN: Shutdown.
    IDLE_ACTION_DO_NOTHING: Do nothing.
  batteryDimTimeout: TYPE_INT64
  batteryScreenOffTimeout: TYPE_INT64

chrome.devices.kiosk.BatteryPowerSettingsV2: Battery Kiosk power settings.
  batteryIdleTimeout: TYPE_INT64
  batteryWarningTimeout: TYPE_INT64
  batteryIdleAction: TYPE_ENUM
    IDLE_ACTION_SUSPEND: Sleep.
    IDLE_ACTION_LOGOUT: Logout.
    IDLE_ACTION_SHUTDOWN: Shutdown.
    IDLE_ACTION_DO_NOTHING: Do nothing.
  batteryDimTimeout: TYPE_INT64
  batteryScreenOffTimeout: TYPE_INT64

chrome.devices.kiosk.CaretHighlightEnabled: Kiosk caret highlight.
  caretHighlightEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable caret highlight.
    ACCESSIBILITY_ENABLED: Enable caret highlight.

chrome.devices.kiosk.CursorHighlightEnabled: Kiosk cursor highlight.
  cursorHighlightEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable cursor highlight.
    ACCESSIBILITY_ENABLED: Enable cursor highlight.

chrome.devices.kiosk.DeviceWeeklyScheduledSuspend: Device sleep mode.
  weeklySchedules
    weeklySchedule
      start
        timeOfDay
          hours: TYPE_INT32
          minutes: TYPE_INT32
          seconds: TYPE_INT32
          nanos: TYPE_INT32
      end
        timeOfDay
          hours: TYPE_INT32
          minutes: TYPE_INT32
          seconds: TYPE_INT32
          nanos: TYPE_INT32

chrome.devices.kiosk.DictationEnabled: Kiosk dictation.
  dictationEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable dictation.
    ACCESSIBILITY_ENABLED: Enable dictation.

chrome.devices.kiosk.EnterpriseHardwarePlatformApiEnabled: Enterprise Hardware Platform API.
  enterpriseHardwarePlatformApiEnabled: TYPE_BOOL
    true: Allow managed extensions to use the Enterprise Hardware Platform API.
    false: Do not allow managed extensions to use the Enterprise Hardware Platform API.

chrome.devices.kiosk.HighContrastEnabled: Kiosk high contrast.
  highContrastEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable high contrast.
    ACCESSIBILITY_ENABLED: Enable high contrast.

chrome.devices.kiosk.KeyboardFocusHighlightEnabled: Kiosk keyboard focus highlighting.
  keyboardFocusHighlightEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable keyboard focus highlighting.
    ACCESSIBILITY_ENABLED: Enable keyboard focus highlighting.

chrome.devices.kiosk.KioskAllowedInputMethods: Kiosk allowed input methods.
  allowedInputMethods: TYPE_LIST
    xkb:jp::jpn: Alphanumeric with Japanese keyboard.
    am-t-i0-und: Amharic Transliteration.
    vkd_ar: Arabic.
    ar-t-i0-und: Arabic Transliteration.
    xkb:am:phonetic:arm: Armenian.
    vkd_bn_phone: Bangla Phonetic.
    bn-t-i0-und: Bangla Transliteration.
    xkb:by::bel: Belarusian.
    _comp_ime_jddehjeebkoimngcbdkaahpobgicbffpbraille: Braille Keyboard.
    xkb:bg::bul: Bulgarian.
    xkb:bg:phonetic:bul: Bulgarian with Phonetic keyboard.
    vkd_my: Burmese/Myanmar.
    vkd_my_myansan: Burmese/Myanmar with Myansan keyboard.
    yue-hant-t-i0-und: Cantonese.
    xkb:es:cat:cat: Catalan.
    zh-hant-t-i0-pinyin: Chinese (Traditional) Pinyin.
    zh-hant-t-i0-array-1992: Chinese Array.
    zh-hant-t-i0-cangjie-1987: Chinese Cangjie.
    zh-hant-t-i0-dayi-1988: Chinese Dayi.
    zh-t-i0-pinyin: Chinese Pinyin.
    zh-hant-t-i0-cangjie-1987-x-m0-simplified: Chinese Quick.
    zh-t-i0-wubi-1986: Chinese Wubi.
    zh-hant-t-i0-und: Chinese Zhuyin.
    xkb:hr::scr: Croatian.
    xkb:cz::cze: Czech.
    xkb:cz:qwerty:cze: Czech with Qwerty keyboard.
    xkb:dk::dan: Danish.
    vkd_deva_phone: Devanagari keyboard (Phonetic).
    xkb:be::nld: Dutch (Belgium).
    xkb:us:intl:nld: Dutch (Netherlands).
    xkb:us:intl_pc:nld: Dutch (Netherlands) with US International PC keyboard.
    xkb:ca:eng:eng: English (Canada).
    xkb:in::eng: English (India).
    xkb:pk::eng: English (Pakistan).
    xkb:za:gb:eng: English (South Africa).
    xkb:gb:extd:eng: English (UK).
    xkb:gb:dvorak:eng: English (UK) with Dvorak keyboard.
    xkb:us::eng: English (US).
    xkb:us:colemak:eng: English (US) with Colemak keyboard.
    xkb:us:dvorak:eng: English (US) with Dvorak keyboard.
    xkb:us:altgr-intl:eng: English (US) with Extended keyboard.
    xkb:us:intl_pc:eng: English (US) with International PC keyboard.
    xkb:us:intl:eng: English (US) with International keyboard.
    xkb:us:dvp:eng: English (US) with Programmer Dvorak keyboard.
    xkb:us:workman-intl:eng: English (US) with Workman International keyboard.
    xkb:us:workman:eng: English (US) with Workman keyboard.
    xkb:ee::est: Estonian.
    vkd_ethi: Ethiopic keyboard.
    xkb:fo::fao: Faroese.
    xkb:us::fil: Filipino.
    xkb:fi::fin: Finnish.
    xkb:be::fra: French (Belgium).
    xkb:ca::fra: French (Canada).
    xkb:ca:multix:fra: French (Canada) with Multilingual keyboard.
    xkb:fr::fra: French (France).
    xkb:fr:bepo:fra: French (France) with Bépo keyboard.
    xkb:ch:fr:fra: French (Switzerland).
    xkb:ge::geo: Georgian.
    xkb:be::ger: German (Belgium).
    xkb:de::ger: German (Germany).
    xkb:de:neo:ger: German (Germany) with Neo 2 keyboard.
    xkb:ch::ger: German (Switzerland).
    xkb:gr::gre: Greek.
    el-t-i0-und: Greek Transliteration.
    vkd_gu_phone: Gujarati Phonetic.
    gu-t-i0-und: Gujarati Transliteration.
    xkb:il::heb: Hebrew.
    he-t-i0-und: Hebrew Transliteration.
    hi-t-i0-und: Hindi.
    vkd_hi_inscript: Hindi with InScript keyboard.
    xkb:hu::hun: Hungarian.
    xkb:hu:qwerty:hun: Hungarian with Qwerty keyboard.
    xkb:is::ice: Icelandic.
    xkb:us::ind: Indonesian.
    xkb:ie::ga: Irish.
    xkb:it::ita: Italian.
    nacl_mozc_jp: Japanese.
    nacl_mozc_us: Japanese with US keyboard.
    vkd_kn_phone: Kannada Phonetic.
    kn-t-i0-und: Kannada Transliteration.
    xkb:kz::kaz: Kazakh.
    vkd_km: Khmer.
    ko-t-i0-und: Korean.
    vkd_lo: Lao.
    xkb:lv:apostrophe:lav: Latvian.
    xkb:lt::lit: Lithuanian.
    xkb:mk::mkd: Macedonian.
    xkb:us::msa: Malay.
    vkd_ml_phone: Malayalam Phonetic.
    ml-t-i0-und: Malayalam Transliteration.
    xkb:mt::mlt: Maltese.
    mr-t-i0-und: Marathi.
    xkb:mn::mon: Mongolian.
    ne-t-i0-und: Nepali Transliteration.
    vkd_ne_inscript: Nepali with InScript keyboard.
    vkd_ne_phone: Nepali with Phonetic keyboard.
    xkb:no::nob: Norwegian.
    or-t-i0-und: Odia.
    vkd_fa: Persian.
    fa-t-i0-und: Persian Transliteration.
    xkb:pl::pol: Polish.
    xkb:br::por: Portuguese (Brazil).
    xkb:pt::por: Portuguese (Portugal).
    xkb:us:intl_pc:por: Portuguese with US International PC keyboard.
    xkb:us:intl:por: Portuguese with US International keyboard.
    pa-t-i0-und: Punjabi.
    xkb:ro::rum: Romanian.
    xkb:ro:std:rum: Romanian with Standard keyboard.
    xkb:ru::rus: Russian.
    vkd_ru_phone_aatseel: Russian with Phonetic AATSEEL keyboard.
    vkd_ru_phone_yazhert: Russian with Phonetic YaZHert keyboard.
    xkb:ru:phonetic:rus: Russian with Phonetic keyboard.
    sa-t-i0-und: Sanskrit.
    xkb:rs::srp: Serbian.
    sr-t-i0-und: Serbian Transliteration.
    vkd_si: Sinhala.
    xkb:sk::slo: Slovak.
    xkb:si::slv: Slovenian.
    vkd_ckb_ar: Sorani Kurdish with Arabic-based keyboard.
    vkd_ckb_en: Sorani Kurdish with English-based keyboard.
    xkb:latam::spa: Spanish (Latin America).
    xkb:es::spa: Spanish (Spain).
    xkb:se::swe: Swedish.
    vkd_ta_itrans: Tamil ITRANS.
    vkd_ta_phone: Tamil Phonetic.
    ta-t-i0-und: Tamil Transliteration.
    vkd_ta_inscript: Tamil with InScript keyboard.
    vkd_ta_tamil99: Tamil with Tamil99 keyboard.
    vkd_ta_typewriter: Tamil with Typewriter keyboard.
    vkd_te_phone: Telugu Phonetic.
    te-t-i0-und: Telugu Transliteration.
    vkd_th: Thai with Kedmanee keyboard.
    vkd_th_pattajoti: Thai with Pattachote keyboard.
    vkd_th_tis: Thai with TIS 820-2531 keyboard.
    ti-t-i0-und: Tigrinya.
    xkb:tr::tur: Turkish.
    xkb:tr:f:tur: Turkish with F-keyboard.
    xkb:ua::ukr: Ukrainian.
    ur-t-i0-und: Urdu.
    vkd_vi_telex: Vietnamese Telex.
    vkd_vi_viqr: Vietnamese VIQR.
    vkd_vi_vni: Vietnamese VNI.
    vkd_vi_tcvn: Vietnamese with TCVN keyboard.

chrome.devices.kiosk.KioskTroubleshootingToolsEnabled: Kiosk troubleshooting tools.
  kioskTroubleshootingToolsEnabled: TYPE_BOOL
    true: Enable troubleshooting tools.
    false: Disable troubleshooting tools.

chrome.devices.kiosk.KioskVirtualKeyboardFeatures: Kiosk virtual keyboard features (websites only).
  virtualKeyboardFeatures: TYPE_LIST
    AUTO_SUGGEST: Auto suggest.
    HANDWRITING: Handwriting recognition.
    VOICE_INPUT: Voice input.

chrome.devices.kiosk.LargeCursorEnabled: Kiosk large cursor.
  largeCursorEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable large cursor.
    ACCESSIBILITY_ENABLED: Enable large cursor.

chrome.devices.kiosk.LidCloseAction: Action on lid close.
  lidCloseAction: TYPE_ENUM
    SUSPEND: Sleep.
    SHUTDOWN: Shutdown.
    DO_NOTHING: Do nothing.

chrome.devices.kiosk.MonoAudioEnabled: Kiosk mono audio.
  monoAudioEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable mono audio.
    ACCESSIBILITY_ENABLED: Enable mono audio.

chrome.devices.kiosk.PrimaryMouseButtonSwitch: Kiosk primary mouse button.
  primaryMouseButtonSwitch: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Left button is primary.
    ACCESSIBILITY_ENABLED: Right button is primary.

chrome.devices.kiosk.RemoteAccessHostAllowEnterpriseFileTransfer: Allow remote access admins to transfer files to/from the host.
  remoteAccessHostAllowEnterpriseFileTransfer: TYPE_BOOL
    true: Enable Chrome Remote Desktop File Transfer.
    false: Disable Chrome Remote Desktop File Transfer.

chrome.devices.kiosk.ScreenMagnifierType: Kiosk screen magnifier.
  screenMagnifierType: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable screen magnifier.
    ACCESSIBILITY_FULL_SCREEN: Enable full-screen magnifier.
    ACCESSIBILITY_DOCKED: Enable docked magnifier.

chrome.devices.kiosk.SelectToSpeakEnabled: Kiosk select to speak.
  selectToSpeakEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable select to speak.
    ACCESSIBILITY_ENABLED: Enable select to speak.

chrome.devices.kiosk.SerialAllowUsbDevicesForUrls: Web Serial API allowed devices.
  serialAllowUsbDevicesForUrls
    webOrigin
      url: TYPE_STRING
      device: TYPE_LIST

chrome.devices.kiosk.ShowAccessibilityMenu: Kiosk floating accessibility menu.
  showAccessibilityMenu: TYPE_BOOL
    true: Show the floating accessibility menu in kiosk mode.
    false: Do not show the floating accessibility menu in kiosk mode.

chrome.devices.kiosk.SpokenFeedbackEnabled: Kiosk spoken feedback.
  spokenFeedbackEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable spoken feedback.
    ACCESSIBILITY_ENABLED: Enable spoken feedback.

chrome.devices.kiosk.StickyKeysEnabled: Kiosk sticky keys.
  stickyKeysEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable sticky keys.
    ACCESSIBILITY_ENABLED: Enable sticky keys.

chrome.devices.kiosk.UrlBlocking: URL blocking.
  urlBlocklist: TYPE_LIST
    Blocked URLs. Any URL in the URL blocklist will be blocked, unless it also appears in the URL blocklist exception list.Maximum of 1000 URLs. .
  urlAllowlist: TYPE_LIST
    Blocked URLs exceptions. Any URL that matches an entry in the blocklist exception list will be allowed, even if it matches an entry in the URL blocklist. Wildcards ("*") are allowed when appended to a URL, but cannot be entered alone.

chrome.devices.kiosk.UrlKeyedAnonymizedDataCollectionEnabled: URL-keyed anonymized data collection.
  urlKeyedAnonymizedDataCollectionEnabled: TYPE_BOOL
    true: Send anonymized URL-keyed data for kiosk sessions.
    false: Do not send anonymized URL-keyed data for kiosk sessions.

chrome.devices.kiosk.VirtualKeyboardEnabled: Kiosk on-screen keyboard.
  virtualKeyboardEnabled: TYPE_ENUM
    DEFAULT_USER_CHOICE: Allow the user to decide.
    ACCESSIBILITY_DISABLED: Disable on-screen keyboard.
    ACCESSIBILITY_ENABLED: Enable on-screen keyboard.

chrome.devices.kiosk.WebUsbAllowDevicesForUrls: WebUSB API allowed devices.
  webUsbAllowDevicesForUrls
    webApplications
      url: TYPE_STRING
      devices: TYPE_LIST

chrome.devices.KioskAppControlChromeVersion: Kiosk-controlled updates.
  allowKioskAppControlChromeVersion: TYPE_BOOL
    true: Allow kiosk app to control OS version.
    false: Do not allow kiosk app to control OS version.

chrome.devices.LoginScreenAccessibilityShortcutsEnabled: Accessibility shortcuts.
  loginScreenAccessibilityShortcutsEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable accessibility shortcuts on the sign-in screen.
    TRUE: Enable accessibility shortcuts on the sign-in screen.

chrome.devices.LoginScreenAutoclickEnabled: Auto-click enabled.
  loginScreenAutoclickEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable auto-click on the sign-in screen.
    TRUE: Enable auto-click on the sign-in screen.

chrome.devices.LoginScreenCaretHighlightEnabled: Caret highlight.
  loginScreenCaretHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable caret highlight on the sign-in screen.
    TRUE: Enable caret highlight on the sign-in screen.

chrome.devices.LoginScreenCursorHighlightEnabled: Cursor highlight.
  loginScreenCursorHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable cursor highlight on the sign-in screen.
    TRUE: Enable cursor highlight on the sign-in screen.

chrome.devices.LoginScreenDictationEnabled: Dictation.
  loginScreenDictationEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable dictation on the sign-in screen.
    TRUE: Enable dictation on the sign-in screen.

chrome.devices.LoginScreenHighContrastEnabled: High contrast.
  loginScreenHighContrastEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable high contrast on the sign-in screen.
    TRUE: Enable high contrast on the sign-in screen.

chrome.devices.LoginScreenKeyboardFocusHighlightEnabled: Keyboard focus highlighting.
  loginScreenKeyboardFocusHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable keyboard focus highlighting on the sign-in screen.
    TRUE: Enable keyboard focus highlighting on the sign-in screen.

chrome.devices.LoginScreenLargeCursorEnabled: Large cursor.
  loginScreenLargeCursorEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable large cursor on the sign-in screen.
    TRUE: Enable large cursor on the sign-in screen.

chrome.devices.LoginScreenMonoAudioEnabled: Mono audio.
  loginScreenMonoAudioEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable mono audio on the sign-in screen.
    TRUE: Enable mono audio on the sign-in screen.

chrome.devices.LoginScreenNamesAndPhotos: Show user names and photos on the sign-in screen.
  showUserNames: TYPE_BOOL
    true: Always show user names and photos.
    false: Never show user names and photos.

chrome.devices.LoginScreenPrimaryMouseButtonSwitch: Primary mouse button.
  loginScreenPrimaryMouseButtonSwitch: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Left button is primary on the sign-in screen.
    TRUE: Right button is primary on the sign-in screen.

chrome.devices.LoginScreenScreenMagnifierType: Screen magnifier.
  loginScreenScreenMagnifierType: TYPE_ENUM
    UNSET: Allow the user to decide.
    DISABLED: Disable screen magnifier on the sign-in screen.
    FULL_SCREEN: Enable full-screen magnifier on the sign-in screen.
    DOCKED: Enable docked magnifier on the sign-in screen.

chrome.devices.LoginScreenSelectToSpeakEnabled: Select to speak.
  loginScreenSelectToSpeakEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable select to speak on the sign-in screen.
    TRUE: Enable select to speak on the sign-in screen.

chrome.devices.LoginScreenSpokenFeedbackEnabled: Spoken feedback.
  loginScreenSpokenFeedbackEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable spoken feedback on the sign-in screen.
    TRUE: Enable spoken feedback on the sign-in screen.

chrome.devices.LoginScreenStickyKeysEnabled: Sticky keys.
  loginScreenStickyKeysEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable sticky keys on the sign-in screen.
    TRUE: Enable sticky keys on the sign-in screen.

chrome.devices.LoginScreenVirtualKeyboardEnabled: On-screen keyboard.
  loginScreenVirtualKeyboardEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable on-screen keyboard on the sign-in screen.
    TRUE: Enable on-screen keyboard on the sign-in screen.

chrome.devices.LogUploadEnabled: Device system log upload.
  logUploadEnabled: TYPE_BOOL
    true: Enable device system log upload.
    false: Disable device system log upload.

chrome.devices.managedguest.AbusiveExperienceInterventionEnforce: Abusive Experience Intervention.
  abusiveExperienceInterventionEnforce: TYPE_BOOL
    true: Prevent sites with abusive experiences from opening new windows or tabs.
    false: Allow sites with abusive experiences to open new windows or tabs.

chrome.devices.managedguest.AccessControlAllowMethodsInCorsPreflightSpecConformant: CORS Access-Control-Allow-Methods conformance.
  accessControlAllowMethodsInCorsPreflightSpecConformant: TYPE_BOOL
    true: Do not uppercase request methods except for DELETE/GET/HEAD/OPTIONS/POST/PUT.
    false: Always uppercase request methods.

chrome.devices.managedguest.AccessibilityImageLabelsEnabled: Image descriptions.
  accessibilityImageLabelsEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not use Google services to provide automatic image descriptions.
    TRUE: Use an anonymous Google service to provide automatic descriptions for unlabeled images.

chrome.devices.managedguest.AccessibilityShortcutsEnabled: Accessibility shortcuts.
  accessibilityShortcutsEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable accessibility shortcuts.
    TRUE: Enable accessibility shortcuts.

chrome.devices.managedguest.AdditionalDnsQueryTypesEnabled: DNS queries for additional DNS record types.
  additionalDnsQueryTypesEnabled: TYPE_BOOL
    true: Allow additional DNS query types.
    false: Prevent additional DNS query types.

chrome.devices.managedguest.AdsSettingForIntrusiveAdsSites: Sites with intrusive ads.
  adsSettingForIntrusiveAdsSites: TYPE_ENUM
    ALLOW_ADS: Allow ads on all sites.
    BLOCK_ADS: Block ads on sites with intrusive ads.

chrome.devices.managedguest.AllowBackForwardCacheForCacheControlNoStorePageEnabled: No-store header back/forward cache.
  allowBackForwardCacheForCacheControlNoStorePageEnabled: TYPE_BOOL
    true: Allow pages with CCNS header to be stored in back/forward cache.
    false: Disallow pages with CCNS header from being stored in back/forward cache.

chrome.devices.managedguest.AllowDinosaurEasterEgg: Dinosaur game.
  allowDinosaurEasterEgg: TYPE_ENUM
    UNSET: Allow users to play the dinosaur game when the device is offline on Chrome browser, but not on enrolled ChromeOS devices.
    FALSE: Do not allow users to play the dinosaur game when the device is offline.
    TRUE: Allow users to play the dinosaur game when the device is offline.

chrome.devices.managedguest.AllowedInputMethods: Allowed input methods.
  allowedInputMethods: TYPE_LIST
    xkb:jp::jpn: Alphanumeric with Japanese keyboard.
    am-t-i0-und: Amharic Transliteration.
    vkd_ar: Arabic.
    ar-t-i0-und: Arabic Transliteration.
    xkb:am:phonetic:arm: Armenian.
    vkd_bn_phone: Bangla Phonetic.
    bn-t-i0-und: Bangla Transliteration.
    xkb:by::bel: Belarusian.
    _comp_ime_jddehjeebkoimngcbdkaahpobgicbffpbraille: Braille Keyboard.
    xkb:bg::bul: Bulgarian.
    xkb:bg:phonetic:bul: Bulgarian with Phonetic keyboard.
    vkd_my: Burmese/Myanmar.
    vkd_my_myansan: Burmese/Myanmar with Myansan keyboard.
    yue-hant-t-i0-und: Cantonese.
    xkb:es:cat:cat: Catalan.
    zh-hant-t-i0-pinyin: Chinese (Traditional) Pinyin.
    zh-hant-t-i0-array-1992: Chinese Array.
    zh-hant-t-i0-cangjie-1987: Chinese Cangjie.
    zh-hant-t-i0-dayi-1988: Chinese Dayi.
    zh-t-i0-pinyin: Chinese Pinyin.
    zh-hant-t-i0-cangjie-1987-x-m0-simplified: Chinese Quick.
    zh-t-i0-wubi-1986: Chinese Wubi.
    zh-hant-t-i0-und: Chinese Zhuyin.
    xkb:hr::scr: Croatian.
    xkb:cz::cze: Czech.
    xkb:cz:qwerty:cze: Czech with Qwerty keyboard.
    xkb:dk::dan: Danish.
    vkd_deva_phone: Devanagari keyboard (Phonetic).
    xkb:be::nld: Dutch (Belgium).
    xkb:us:intl:nld: Dutch (Netherlands).
    xkb:us:intl_pc:nld: Dutch (Netherlands) with US International PC keyboard.
    xkb:ca:eng:eng: English (Canada).
    xkb:in::eng: English (India).
    xkb:pk::eng: English (Pakistan).
    xkb:za:gb:eng: English (South Africa).
    xkb:gb:extd:eng: English (UK).
    xkb:gb:dvorak:eng: English (UK) with Dvorak keyboard.
    xkb:us::eng: English (US).
    xkb:us:colemak:eng: English (US) with Colemak keyboard.
    xkb:us:dvorak:eng: English (US) with Dvorak keyboard.
    xkb:us:altgr-intl:eng: English (US) with Extended keyboard.
    xkb:us:intl_pc:eng: English (US) with International PC keyboard.
    xkb:us:intl:eng: English (US) with International keyboard.
    xkb:us:dvp:eng: English (US) with Programmer Dvorak keyboard.
    xkb:us:workman-intl:eng: English (US) with Workman International keyboard.
    xkb:us:workman:eng: English (US) with Workman keyboard.
    xkb:ee::est: Estonian.
    vkd_ethi: Ethiopic keyboard.
    xkb:fo::fao: Faroese.
    xkb:us::fil: Filipino.
    xkb:fi::fin: Finnish.
    xkb:be::fra: French (Belgium).
    xkb:ca::fra: French (Canada).
    xkb:ca:multix:fra: French (Canada) with Multilingual keyboard.
    xkb:fr::fra: French (France).
    xkb:fr:bepo:fra: French (France) with Bépo keyboard.
    xkb:ch:fr:fra: French (Switzerland).
    xkb:ge::geo: Georgian.
    xkb:be::ger: German (Belgium).
    xkb:de::ger: German (Germany).
    xkb:de:neo:ger: German (Germany) with Neo 2 keyboard.
    xkb:ch::ger: German (Switzerland).
    xkb:gr::gre: Greek.
    el-t-i0-und: Greek Transliteration.
    vkd_gu_phone: Gujarati Phonetic.
    gu-t-i0-und: Gujarati Transliteration.
    xkb:il::heb: Hebrew.
    he-t-i0-und: Hebrew Transliteration.
    hi-t-i0-und: Hindi.
    vkd_hi_inscript: Hindi with InScript keyboard.
    xkb:hu::hun: Hungarian.
    xkb:hu:qwerty:hun: Hungarian with Qwerty keyboard.
    xkb:is::ice: Icelandic.
    xkb:us::ind: Indonesian.
    xkb:ie::ga: Irish.
    xkb:it::ita: Italian.
    nacl_mozc_jp: Japanese.
    nacl_mozc_us: Japanese with US keyboard.
    vkd_kn_phone: Kannada Phonetic.
    kn-t-i0-und: Kannada Transliteration.
    xkb:kz::kaz: Kazakh.
    vkd_km: Khmer.
    ko-t-i0-und: Korean.
    vkd_lo: Lao.
    xkb:lv:apostrophe:lav: Latvian.
    xkb:lt::lit: Lithuanian.
    xkb:mk::mkd: Macedonian.
    xkb:us::msa: Malay.
    vkd_ml_phone: Malayalam Phonetic.
    ml-t-i0-und: Malayalam Transliteration.
    xkb:mt::mlt: Maltese.
    mr-t-i0-und: Marathi.
    xkb:mn::mon: Mongolian.
    ne-t-i0-und: Nepali Transliteration.
    vkd_ne_inscript: Nepali with InScript keyboard.
    vkd_ne_phone: Nepali with Phonetic keyboard.
    xkb:no::nob: Norwegian.
    or-t-i0-und: Odia.
    vkd_fa: Persian.
    fa-t-i0-und: Persian Transliteration.
    xkb:pl::pol: Polish.
    xkb:br::por: Portuguese (Brazil).
    xkb:pt::por: Portuguese (Portugal).
    xkb:us:intl_pc:por: Portuguese with US International PC keyboard.
    xkb:us:intl:por: Portuguese with US International keyboard.
    pa-t-i0-und: Punjabi.
    xkb:ro::rum: Romanian.
    xkb:ro:std:rum: Romanian with Standard keyboard.
    xkb:ru::rus: Russian.
    vkd_ru_phone_aatseel: Russian with Phonetic AATSEEL keyboard.
    vkd_ru_phone_yazhert: Russian with Phonetic YaZHert keyboard.
    xkb:ru:phonetic:rus: Russian with Phonetic keyboard.
    sa-t-i0-und: Sanskrit.
    xkb:rs::srp: Serbian.
    sr-t-i0-und: Serbian Transliteration.
    vkd_si: Sinhala.
    xkb:sk::slo: Slovak.
    xkb:si::slv: Slovenian.
    vkd_ckb_ar: Sorani Kurdish with Arabic-based keyboard.
    vkd_ckb_en: Sorani Kurdish with English-based keyboard.
    xkb:latam::spa: Spanish (Latin America).
    xkb:es::spa: Spanish (Spain).
    xkb:se::swe: Swedish.
    vkd_ta_itrans: Tamil ITRANS.
    vkd_ta_phone: Tamil Phonetic.
    ta-t-i0-und: Tamil Transliteration.
    vkd_ta_inscript: Tamil with InScript keyboard.
    vkd_ta_tamil99: Tamil with Tamil99 keyboard.
    vkd_ta_typewriter: Tamil with Typewriter keyboard.
    vkd_te_phone: Telugu Phonetic.
    te-t-i0-und: Telugu Transliteration.
    vkd_th: Thai with Kedmanee keyboard.
    vkd_th_pattajoti: Thai with Pattachote keyboard.
    vkd_th_tis: Thai with TIS 820-2531 keyboard.
    ti-t-i0-und: Tigrinya.
    xkb:tr::tur: Turkish.
    xkb:tr:f:tur: Turkish with F-keyboard.
    xkb:ua::ukr: Ukrainian.
    ur-t-i0-und: Urdu.
    vkd_vi_telex: Vietnamese Telex.
    vkd_vi_viqr: Vietnamese VIQR.
    vkd_vi_vni: Vietnamese VNI.
    vkd_vi_tcvn: Vietnamese with TCVN keyboard.
  allowedInputMethodsForceEnabled: TYPE_BOOL
    true: Automatically install selected keyboard languages.
    false: Do not automatically install any keyboard languages.

chrome.devices.managedguest.AllowedLanguages: Allowed ChromeOS languages.
  allowedLanguages: TYPE_LIST
    ar: Arabic - ‫العربية‬.
    bn: Bangla - ‪বাংলা‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    zh-CN: Chinese (Simplified) - ‪简体中文‬.
    zh-TW: Chinese (Traditional) - ‪繁體中文‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-NZ: English (New Zealand).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fil: Filipino.
    fi: Finnish - ‪Suomi‬.
    fr-CA: French (Canada) - ‪Français (Canada)‬.
    fr: French (France) - ‪Français (France)‬.
    fr-CH: French (Switzerland) - ‪Français (Suisse)‬.
    de: German (Germany) - ‪Deutsch (Deutschland)‬.
    de-CH: German (Switzerland) - ‪Deutsch (Schweiz)‬.
    el: Greek - ‪Ελληνικά‬.
    gu: Gujarati - ‪ગુજરાતી‬.
    iw: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    is: Icelandic - ‪íslenska‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    ja: Japanese - ‪日本語‬.
    kn: Kannada - ‪ಕನ್ನಡ‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    ms: Malay - ‪Melayu‬.
    ml: Malayalam - ‪മലയാളം‬.
    mr: Marathi - ‪मराठी‬.
    no: Norwegian - ‪norsk‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es: Spanish (Spain) - ‪Español (España)‬.
    sv: Swedish - ‪Svenska‬.
    ta: Tamil - ‪தமிழ்‬.
    te: Telugu - ‪తెలుగు‬.
    th: Thai - ‪ไทย‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.

chrome.devices.managedguest.AllowExcludeDisplayInMirrorMode: Exclude display in mirror mode.
  allowExcludeDisplayInMirrorMode: TYPE_BOOL
    true: Allow users to exclude displays from mirror mode.
    false: Do not allow users to exclude displays from mirror mode.

chrome.devices.managedguest.AllowPrinting: Printing.
  printingEnabled: TYPE_BOOL
    true: Enable printing.
    false: Disable printing.

chrome.devices.managedguest.AllowWakeLocks: Wake locks.
  allowScreenWakeLocks: TYPE_BOOL
    true: Allow screen wake locks for power management.
    false: Demote screen wake lock requests to system wake lock requests.
  allowWakeLocks: TYPE_BOOL
    true: Allow wake locks.
    false: Do not allow wake locks.

chrome.devices.managedguest.AllowWebAuthnWithBrokenTlsCerts: Web Authentication requests on sites with broken TLS certificates.
  allowWebAuthnWithBrokenTlsCerts: TYPE_BOOL
    true: Allow WebAuthn API requests on sites with broken TLS certificates.
    false: Do not allow WebAuthn API requests on sites with broken TLS certificates.

chrome.devices.managedguest.AlwaysOnVpn: Always on VPN.
  alwaysOnVpnApp: TYPE_STRING
    Activate Always-on VPN for all user traffic with an app from a list of force installed Android VPN apps. Please make sure the configured app is force installed.
  vpnConfigAllowed: TYPE_BOOL
    true: Allow user to disconnect from a VPN manually (VPN will reconnect on log in).
    false: Do not allow user to disconnect from a VPN manually.

chrome.devices.managedguest.AlwaysOnVpnPreConnectUrlAllowlist: Always on VPN URL exceptions.
  alwaysOnVpnPreConnectUrlAllowlist: TYPE_LIST
    URL exceptions. Allow the user to navigate to any URL in this list while an Android Always on VPN is set to strict mode and the VPN is not connected. Maximum of 1000 URLs.

chrome.devices.managedguest.AppCacheForceEnabled: AppCache.
  appCacheForceEnabled: TYPE_BOOL
    true: Allow websites to use the deprecated AppCache feature.
    false: Do not allow websites to use the deprecated AppCache feature.

chrome.devices.managedguest.AppRecommendationZeroStateEnabled: Previously installed app recommendations.
  appRecommendationZeroStateEnabled: TYPE_BOOL
    true: Show app recommendations in the ChromeOS launcher.
    false: Do not show app recommendations in the ChromeOS launcher.

chrome.devices.managedguest.apps.AccessToKeys: Allows setting of whether the app can access client keys.
  allowAccessToKeys: TYPE_BOOL
    Controls whether the app can access client keys.

chrome.devices.managedguest.apps.AppInstallationUrl: Specifies the url from which to install a self hosted Chrome Extension.
  installationUrl: TYPE_STRING
    The url from which to install a self hosted Chrome Extension.

chrome.devices.managedguest.apps.CertificateManagement: Allows setting of certificate management related permissions.
  allowAccessToKeys: TYPE_BOOL
    Controls whether the app can access client keys.
  allowEnterpriseChallenge: TYPE_BOOL
    Controls whether the app can challenge enterprise keys.

chrome.devices.managedguest.apps.DefaultLaunchContainer: Allows setting of the default launch container for web apps.
  defaultLaunchContainer: TYPE_ENUM
    TAB: Tab.
    WINDOW: Window.

chrome.devices.managedguest.apps.EnterpriseChallenge: Allows setting of whether the app can challenge enterprise keys.
  allowEnterpriseChallenge: TYPE_BOOL
    Controls whether the app can challenge enterprise keys.

chrome.devices.managedguest.apps.IncludeInChromeWebStoreCollection: Specifies whether the Chrome Application should appear in the Chrome Web Store collection.
  includeInCollection: TYPE_BOOL
    Controls whether a Chrome Application should appear in the Chrome Web Store collection.
  spotlightRecommended: TYPE_BOOL
    Controls whether a Chrome Application should be spotlighted in the Chrome Web Store collection.

chrome.devices.managedguest.apps.InstallationUrl: Specifies the url from which to install a self hosted Chrome Extension.
  installationUrl: TYPE_STRING
    The url from which to install a self hosted Chrome Extension.
  overrideInstallationUrl: TYPE_BOOL
    Override the URL provided in the extension manifest with the provided installation url.

chrome.devices.managedguest.apps.InstallType: Specifies the manner in which the app is to be installed. Note: It's required in order to add an App or Extension to the set of managed apps & extensions of an Organizational Unit.
  appInstallType: TYPE_ENUM
    NOT_INSTALLED: Not Installed.
    FORCED: Force Install.
    FORCED_AND_PIN_TO_TOOLBAR: Force Install + pin.

chrome.devices.managedguest.apps.ManagedConfiguration: Allows setting of the managed configuration.
  managedConfiguration: TYPE_STRING
    Sets the managed configuration JSON format.

chrome.devices.managedguest.apps.OverrideInstallationUrl: Allows overriding of the url from which to install a self hosted Chrome Extension.
  overrideInstallationUrl: TYPE_BOOL
    true: Use URL provided by AppInstallationUrl.
    false: Use URL provided in the extension manifest.

chrome.devices.managedguest.apps.PermissionsAndUrlAccess: Allows setting of allowed and blocked hosts.
  blockedPermissions: TYPE_LIST
    : Allow all permissions. If empty string is set, it must be the only value set for the policy.
    activeTab: Active tab.
    app.window.alwaysOnTop: Always on top.
    alarms: Alarms.
    audioCapture: Audio capture.
    certificateProvider: Certificate provider.
    clipboardRead: Clipboard read.
    clipboardWrite: Clipboard write.
    contextMenus: Context menus.
    cookies: Cookies.
    desktopCapture: Desktop capture.
    documentScan: Document scan.
    enterprise.deviceAttributes: Enterprise device attributes.
    experimental: Experimental APIs.
    app.window.fullscreen: Fullscreen apps.
    fileBrowserHandler: File browser handler.
    fileSystem: File system.
    fileSystemProvider: File system provider.
    hid: HID.
    app.window.fullscreen.overrideEsc: Override fullscreen escape.
    idle: Detect idle.
    identity: Identity.
    gcm: Google Cloud Messaging.
    geolocation: Geo location.
    mediaGalleries: Media galleries.
    nativeMessaging: Native messaging.
    networking.config: Captive portal authenticator.
    power: Power.
    notifications: Notifications.
    printerProvider: Printers.
    serial: Serial.
    proxy: Set proxy.
    platformKeys: Platform keys.
    storage: Storage.
    syncFileSystem: Sync file system.
    system.cpu: CPU metadata.
    system.memory: Memory metadata.
    system.network: Network metadata.
    system.display: Display metadata.
    system.storage: Storage metadata.
    tts: Text to speech.
    unlimitedStorage: Unlimited storage.
    usb: USB.
    videoCapture: Video capture.
    vpnProvider: VPN provider.
    webRequest: Web requests.
    webRequestBlocking: Block web requests.
    app.window.alpha: Alpha.
    app.window.alwaysOnTop: Always on top.
    appview: App view.
    audio: Audio.
    bluetoothPrivate: Bluetooth private.
    cecPrivate: Cec private.
    clipboard: Clipboard.
    declarativeNetRequest: Declarative net request.
    declarativeNetRequestWithHostAccess: Declarative net request with host access.
    declarativeNetRequestFeedback: Declarative net request feedback.
    declarativeWebRequest: Declarative web request.
    diagnostics: Diagnostics.
    dns: Dns.
    externally_connectable.all_urls: All URLs externally connectable.
    feedbackPrivate: Feedback private.
    fileSystem.directory: File system directory.
    fileSystem.retainEntries: File system retain entries.
    fileSystem.write: File system write.
    fileSystem.requestFileSystem: File system request file system.
    app.window.ime: Ime.
    lockScreen: Lock screen.
    mediaPerceptionPrivate: Media perception private.
    metricsPrivate: Metrics private.
    networking.onc: Networking open network configuration.
    networkingPrivate: Networking private.
    odfsConfigPrivate: ODFS config private.
    offscreen: Offscreen.
    runtime: Runtime.
    socket: Socket.
    app.window.shape: Shape.
    usbDevices: USB Devices.
    u2fDevices: U2F devices.
    userScripts: User scripts.
    virtualKeyboard: Virtual keyboard.
    virtualKeyboardPrivate: Virtual keyboard private.
    webview: Web view.
    webRequestAuthProvider: Auth provider web requests.
    arcAppsPrivate: Arc apps private.
    browser: Browser.
    enterprise.remoteApps: Enterprise remote apps.
    firstRunPrivate: First run private.
    mediaGalleries.allAutoDetected: All autodetected media galleries.
    mediaGalleries.scan: Scan media galleries.
    mediaGalleries.read: Read media galleries.
    mediaGalleries.copyTo: Copy to media galleries.
    mediaGalleries.delete: Delete media galleries.
    pointerLock: Pointer lock.
    os.attached_device_info: OS attached device info.
    os.bluetooth_peripherals_info: OS bluetooth peripherals info.
    os.diagnostics: OS diagnostics.
    os.diagnostics.network_info_mlab: OS network info MLAB diagnostics.
    os.events: OS events.
    os.management.audio: OS management audio.
    os.telemetry: OS telemetry.
    os.telemetry.serial_number: OS serial number telemetry.
    os.telemetry.network_info: OS network info telemetry.
    accessibilityFeatures.modify: Accessibility features modify.
    accessibilityFeatures.read: Accessibility features read.
    accessibilityPrivate: Accessibility private.
    accessibilityServicePrivate: Accessibility service private.
    activityLogPrivate: Activity log private.
    autofillPrivate: Autofill private.
    autotestPrivate: Autotest private.
    background: Background.
    bookmarks: Bookmarks.
    brailleDisplayPrivate: Braille display private.
    browsingData: Browsing data.
    chromePrivate: Chrome private.
    chromeosInfoPrivate: ChromeOS info private.
    commandLinePrivate: Command line private.
    commands.accessibility: Commands accessibility.
    contentSettings: Content settings.
    crashReportPrivate: Crash report private.
    devtools: Devtools.
    debugger: Debugger.
    developerPrivate: Developer private.
    declarativeContent: Declarative content.
    downloads: Downloads.
    downloads.open: Downloads open.
    downloads.shelf: Downloads shelf.
    downloads.ui: Downloads UI.
    enterprise.networkingAttributes: Enterprise networking attributes.
    enterprise.hardwarePlatform: Enterprise hardware platform.
    enterprise.kioskInput: Enterprise kiosk input.
    enterprise.platformKeys: Enterprise platform keys.
    enterprise.platformKeysPrivate: Enterprise platform keys private.
    enterprise.reportingPrivate: Enterprise reporting private.
    experimentalAiData: Experimental AI data.
    favicon: Favicon.
    fileManagerPrivate: File manager private.
    fontSettings: Font settings.
    sharedStoragePrivate: Shared storage private.
    history: History.
    identity.email: Identity email.
    idltest: IDL test.
    input: Input.
    imageLoaderPrivate: Image loader private.
    inputMethodPrivate: Input method private.
    languageSettingsPrivate: Language settings private.
    lockWindowFullscreenPrivate: Lock window fullscreen private.
    login: Login.
    loginScreenStorage: Login screen storage.
    loginScreenUi: Login screen UI.
    loginState: Login state.
    webcamPrivate: Webcam private.
    management: Management.
    mediaPlayerPrivate: Media player private.
    mdns: Multicast domain name system.
    echoPrivate: Echo private.
    pageCapture: Page capture.
    passwordsPrivate: Passwords private.
    pdfViewerPrivate: PDF viewer private.
    plugin: Plugin.
    printing: Printing.
    printingMetrics: Printing metrics.
    privacy: Privacy.
    processes: Processes.
    imageWriterPrivate: Image writer private.
    readingList: Reading list.
    resourcesPrivate: Resources private.
    rtcPrivate: RTC private.
    safeBrowsingPrivate: Safe browsing private.
    scripting: Scripting.
    search: Search.
    sessions: Sessions.
    settingsPrivate: Settings private.
    sidePanel: Side panel.
    smartCardProviderPrivate: Smart card provider private.
    speechRecognitionPrivate: Speech recognition private.
    systemLog: System log.
    systemPrivate: System private.
    tabGroups: Tab groups.
    tabs: Tabs.
    tabCapture: Tab capture.
    terminalPrivate: Terminal private.
    topSites: Top sites.
    transientBackground: Transient background.
    ttsEngine: Text to speech engine.
    usersPrivate: Users private.
    wallpaper: Wallpaper.
    webAuthenticationProxy: Web authentication proxy.
    webNavigation: Web navigation.
    webrtcAudioPrivate: WebRTC audio private.
    webrtcDesktopCapturePrivate: WebRTC desktop capture private.
    webrtcLoggingPrivate: WebRTC logging private.
    webrtcLoggingPrivate.audioDebug: WebRTC audio debug logging private.
    webstorePrivate: Webstore private.
    wmDesksPrivate: WM desks private.
  allowedPermissions: TYPE_LIST
    activeTab: Active tab.
    app.window.alwaysOnTop: Always on top.
    alarms: Alarms.
    audioCapture: Audio capture.
    certificateProvider: Certificate provider.
    clipboardRead: Clipboard read.
    clipboardWrite: Clipboard write.
    contextMenus: Context menus.
    desktopCapture: Desktop capture.
    documentScan: Document scan.
    enterprise.deviceAttributes: Enterprise device attributes.
    experimental: Experimental APIs.
    app.window.fullscreen: Fullscreen apps.
    fileBrowserHandler: File browser handler.
    fileSystem: File system.
    fileSystemProvider: File system provider.
    hid: HID.
    app.window.fullscreen.overrideEsc: Override fullscreen escape.
    idle: Detect idle.
    identity: Identity.
    gcm: Google Cloud Messaging.
    geolocation: Geo location.
    mediaGalleries: Media galleries.
    nativeMessaging: Native messaging.
    networking.config: Captive portal authenticator.
    power: Power.
    notifications: Notifications.
    printerProvider: Printers.
    serial: Serial.
    proxy: Set proxy.
    platformKeys: Platform keys.
    storage: Storage.
    syncFileSystem: Sync file system.
    system.cpu: CPU metadata.
    system.memory: Memory metadata.
    system.network: Network metadata.
    system.display: Display metadata.
    system.storage: Storage metadata.
    tts: Text to speech.
    unlimitedStorage: Unlimited storage.
    usb: USB.
    videoCapture: Video capture.
    vpnProvider: VPN provider.
    webRequest: Web requests.
    webRequestBlocking: Block web requests.
    app.window.alpha: Alpha.
    app.window.alwaysOnTop: Always on top.
    appview: App view.
    audio: Audio.
    bluetoothPrivate: Bluetooth private.
    cecPrivate: Cec private.
    clipboard: Clipboard.
    declarativeNetRequest: Declarative net request.
    declarativeNetRequestWithHostAccess: Declarative net request with host access.
    declarativeNetRequestFeedback: Declarative net request feedback.
    declarativeWebRequest: Declarative web request.
    diagnostics: Diagnostics.
    dns: Dns.
    externally_connectable.all_urls: All URLs externally connectable.
    feedbackPrivate: Feedback private.
    fileSystem.directory: File system directory.
    fileSystem.retainEntries: File system retain entries.
    fileSystem.write: File system write.
    fileSystem.requestFileSystem: File system request file system.
    app.window.ime: Ime.
    lockScreen: Lock screen.
    mediaPerceptionPrivate: Media perception private.
    metricsPrivate: Metrics private.
    networking.onc: Networking open network configuration.
    networkingPrivate: Networking private.
    odfsConfigPrivate: ODFS config private.
    offscreen: Offscreen.
    runtime: Runtime.
    socket: Socket.
    app.window.shape: Shape.
    usbDevices: USB Devices.
    u2fDevices: U2F devices.
    userScripts: User scripts.
    virtualKeyboard: Virtual keyboard.
    virtualKeyboardPrivate: Virtual keyboard private.
    webview: Web view.
    webRequestAuthProvider: Auth provider web requests.
    arcAppsPrivate: Arc apps private.
    browser: Browser.
    enterprise.remoteApps: Enterprise remote apps.
    firstRunPrivate: First run private.
    mediaGalleries.allAutoDetected: All autodetected media galleries.
    mediaGalleries.scan: Scan media galleries.
    mediaGalleries.read: Read media galleries.
    mediaGalleries.copyTo: Copy to media galleries.
    mediaGalleries.delete: Delete media galleries.
    pointerLock: Pointer lock.
    os.attached_device_info: OS attached device info.
    os.bluetooth_peripherals_info: OS bluetooth peripherals info.
    os.diagnostics: OS diagnostics.
    os.diagnostics.network_info_mlab: OS network info MLAB diagnostics.
    os.events: OS events.
    os.management.audio: OS management audio.
    os.telemetry: OS telemetry.
    os.telemetry.serial_number: OS serial number telemetry.
    os.telemetry.network_info: OS network info telemetry.
    accessibilityFeatures.modify: Accessibility features modify.
    accessibilityFeatures.read: Accessibility features read.
    accessibilityPrivate: Accessibility private.
    accessibilityServicePrivate: Accessibility service private.
    activityLogPrivate: Activity log private.
    autofillPrivate: Autofill private.
    autotestPrivate: Autotest private.
    background: Background.
    bookmarks: Bookmarks.
    brailleDisplayPrivate: Braille display private.
    browsingData: Browsing data.
    chromePrivate: Chrome private.
    chromeosInfoPrivate: ChromeOS info private.
    commandLinePrivate: Command line private.
    commands.accessibility: Commands accessibility.
    contentSettings: Content settings.
    crashReportPrivate: Crash report private.
    devtools: Devtools.
    debugger: Debugger.
    developerPrivate: Developer private.
    declarativeContent: Declarative content.
    downloads: Downloads.
    downloads.open: Downloads open.
    downloads.shelf: Downloads shelf.
    downloads.ui: Downloads UI.
    enterprise.networkingAttributes: Enterprise networking attributes.
    enterprise.hardwarePlatform: Enterprise hardware platform.
    enterprise.kioskInput: Enterprise kiosk input.
    enterprise.platformKeys: Enterprise platform keys.
    enterprise.platformKeysPrivate: Enterprise platform keys private.
    enterprise.reportingPrivate: Enterprise reporting private.
    experimentalAiData: Experimental AI data.
    favicon: Favicon.
    fileManagerPrivate: File manager private.
    fontSettings: Font settings.
    sharedStoragePrivate: Shared storage private.
    history: History.
    identity.email: Identity email.
    idltest: IDL test.
    input: Input.
    imageLoaderPrivate: Image loader private.
    inputMethodPrivate: Input method private.
    languageSettingsPrivate: Language settings private.
    lockWindowFullscreenPrivate: Lock window fullscreen private.
    login: Login.
    loginScreenStorage: Login screen storage.
    loginScreenUi: Login screen UI.
    loginState: Login state.
    webcamPrivate: Webcam private.
    management: Management.
    mediaPlayerPrivate: Media player private.
    mdns: Multicast domain name system.
    echoPrivate: Echo private.
    pageCapture: Page capture.
    passwordsPrivate: Passwords private.
    pdfViewerPrivate: PDF viewer private.
    plugin: Plugin.
    printing: Printing.
    printingMetrics: Printing metrics.
    privacy: Privacy.
    processes: Processes.
    imageWriterPrivate: Image writer private.
    readingList: Reading list.
    resourcesPrivate: Resources private.
    rtcPrivate: RTC private.
    safeBrowsingPrivate: Safe browsing private.
    scripting: Scripting.
    search: Search.
    sessions: Sessions.
    settingsPrivate: Settings private.
    sidePanel: Side panel.
    smartCardProviderPrivate: Smart card provider private.
    speechRecognitionPrivate: Speech recognition private.
    systemLog: System log.
    systemPrivate: System private.
    tabGroups: Tab groups.
    tabs: Tabs.
    tabCapture: Tab capture.
    terminalPrivate: Terminal private.
    topSites: Top sites.
    transientBackground: Transient background.
    ttsEngine: Text to speech engine.
    usersPrivate: Users private.
    wallpaper: Wallpaper.
    webAuthenticationProxy: Web authentication proxy.
    webNavigation: Web navigation.
    webrtcAudioPrivate: WebRTC audio private.
    webrtcDesktopCapturePrivate: WebRTC desktop capture private.
    webrtcLoggingPrivate: WebRTC logging private.
    webrtcLoggingPrivate.audioDebug: WebRTC audio debug logging private.
    webstorePrivate: Webstore private.
    wmDesksPrivate: WM desks private.
  blockedHosts: TYPE_LIST
    Sets extension hosts that should be blocked.
  allowedHosts: TYPE_LIST
    Sets extension hosts that should be allowed. Allowed hosts override blocked hosts.

chrome.devices.managedguest.apps.SkipDocumentScanConfirmation: Allows the app to skip the confirmation dialog when using the Document Scan API.
  skipDocumentScanConfirmation: TYPE_BOOL
    Controls whether a Chrome Application can skip the confirmation dialog when using the Document Scan API.

chrome.devices.managedguest.apps.SkipPrintConfirmation: Allows the app to skip the confirmation dialog when sending print jobs via the Chrome Printing API.
  skipPrintConfirmation: TYPE_BOOL
    Controls whether a Chrome Application can skip the confirmation dialog when sending print jobs via the Chrome Printing API.

chrome.devices.managedguest.AssistantWebEnabled: Allow using Google Assistant on the web.
  assistantWebEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not allow using Google Assistant on the web.
    TRUE: Allow using Google Assistant on the web.

chrome.devices.managedguest.AudioCaptureAllowedUrls: Audio input allowed URLs.
  audioCaptureAllowedUrls: TYPE_LIST
    URL patterns to allow. URLs that will be granted access to the audio input device without a prompt. Prefix domain with [*.] to include subdomains.

chrome.devices.managedguest.AudioInput: Audio input (microphone).
  audioCaptureAllowed: TYPE_BOOL
    true: Prompt user to allow each time.
    false: Disable audio input.

chrome.devices.managedguest.AudioOutput: Audio output.
  audioOutputAllowed: TYPE_BOOL
    true: Enable audio output.
    false: Disable audio output.

chrome.devices.managedguest.AuthenticationServerAllowlist: Integrated authentication servers.
  authServerAllowlist: TYPE_LIST
    Allowed authentication servers. Enter a list of servers for integrated authentication.

chrome.devices.managedguest.AutoclickEnabled: Auto-click enabled.
  autoclickEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable auto-click.
    TRUE: Enable auto-click.

chrome.devices.managedguest.AutofillAddressEnabled: Address form autofill.
  autofillAddressEnabled: TYPE_BOOL
    true: Allow user to configure.
    false: Never Autofill address forms.

chrome.devices.managedguest.AutofillCreditCardEnabled: Credit card form autofill.
  autofillCreditCardEnabled: TYPE_BOOL
    true: Allow user to configure.
    false: Never Autofill credit card forms.

chrome.devices.managedguest.AutomaticFullscreen: Automatic fullscreen.
  automaticFullscreenAllowedForUrls: TYPE_LIST
    Allow automatic fullscreen on these sites. Supersedes users' personal settings and allows matching origins to call the API without a prior user gesture.
  automaticFullscreenBlockedForUrls: TYPE_LIST
    Block automatic fullscreen on these sites. Supersedes users' personal settings and blocks matching origins from calling the API without a prior user gesture.

chrome.devices.managedguest.AutoOpen: Auto open downloaded files.
  autoOpenAllowedForUrls: TYPE_LIST
    Auto open URLs. If this policy is set, only downloads that match these URLs and have an auto open type will be auto opened. If this policy is left unset, all downloads matching an auto open type will be auto opened. Wildcards ("*") are allowed when appended to a URL, but cannot be entered alone.
  autoOpenFileTypes: TYPE_LIST
    Auto open files types. Do not include the leading separator when listing the type. For example, use "txt", not ".txt".

chrome.devices.managedguest.AutoplayAllowlist: Autoplay video.
  autoplayAllowlist: TYPE_LIST
    Allowed URLs. URL patterns allowed to autoplay. Prefix domain with [*.] to include all subdomains. Use * to allow all domains.

chrome.devices.managedguest.Avatar: Custom avatar.
  userAvatarImage
    downloadUri: TYPE_STRING

chrome.devices.managedguest.BeforeunloadEventCancelByPreventDefaultEnabled: Behavior of event.preventDefault() for beforeunload event.
  beforeunloadEventCancelByPreventDefaultEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not show cancel dialog when event.preventDefault() is called for beforeunload event.
    TRUE: Show cancel dialog when event.preventDefault() is called for beforeunload event.

chrome.devices.managedguest.BookmarkBarEnabled: Bookmark bar.
  bookmarkBarEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable bookmark bar.
    TRUE: Enable bookmark bar.
  bookmarkBarPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.BrowserHistory: Browser history.
  savingBrowserHistoryDisabled: TYPE_BOOL
    true: Never save browser history.
    false: Always save browser history.

chrome.devices.managedguest.BrowsingDataLifetime: Browsing Data Lifetime.
  browsingHistoryTtl: TYPE_INT64
  downloadHistoryTtl: TYPE_INT64
  cookiesAndOtherSiteDataTtl: TYPE_INT64
  cachedImagesAndFilesTtl: TYPE_INT64
  passwordSigninTtl: TYPE_INT64
  autofillTtl: TYPE_INT64
  siteSettingsTtl: TYPE_INT64
  hostedAppDataTtl: TYPE_INT64

chrome.devices.managedguest.BrowsingDataLifetimeV2: Browsing Data Lifetime.
  browsingHistoryTtl: TYPE_INT64
  downloadHistoryTtl: TYPE_INT64
  cookiesAndOtherSiteDataTtl: TYPE_INT64
  cachedImagesAndFilesTtl: TYPE_INT64
  passwordSigninTtl: TYPE_INT64
  autofillTtl: TYPE_INT64
  siteSettingsTtl: TYPE_INT64
  hostedAppDataTtl: TYPE_INT64

chrome.devices.managedguest.BuiltInDnsClientEnabled: Built-in DNS client.
  builtInDnsClientEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never use the built-in DNS client.
    TRUE: Always use the built-in DNS client if available.

chrome.devices.managedguest.CaptivePortalAuthenticationIgnoresProxy: Ignore proxy on captive portals.
  captivePortalAuthenticationIgnoresProxy: TYPE_BOOL
    true: Ignore policies for captive portal pages.
    false: Keep policies for captive portal pages.

chrome.devices.managedguest.CaretHighlightEnabled: Caret highlight.
  caretHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable caret highlight.
    TRUE: Enable caret highlight.

chrome.devices.managedguest.Cecpq2Enabled: CECPQ2 post-quantum key-agreement for TLS.
  cecpq2Enabled: TYPE_BOOL
    true: Enable default CECPQ2 rollout process.
    false: Disable CECPQ2.

chrome.devices.managedguest.CertificateSynchronization: Certificate synchronization.
  arcCertificatesSyncMode: TYPE_ENUM
    SYNC_DISABLED: Disable usage of ChromeOS CA Certificates in Android apps.
    COPY_CA_CERTS: Enable usage of ChromeOS CA Certificates in Android apps.

chrome.devices.managedguest.ChromeAppsWebViewPermissiveBehaviorAllowed: Restore permissive Chrome Apps behavior.
  chromeAppsWebViewPermissiveBehaviorAllowed: TYPE_BOOL
    true: Allow permissive behavior.
    false: Use default navigation protections.

chrome.devices.managedguest.ClientCertificates: Client certificates.
  autoSelectCertificateForUrls: TYPE_LIST
    Automatically select for these sites. If a site matching a pattern specified here requests a client certificate, Chrome will automatically select one for it. More information and example values can be found in https://support.google.com/chrome/a/answer/2657289#AutoSelectCertificateForUrls.

chrome.devices.managedguest.ClipboardSettings: Clipboard.
  defaultClipboardSetting: TYPE_ENUM
    BLOCK_CLIPBOARD: Do not allow any site to use the clipboard site permission.
    ASK_CLIPBOARD: Allow sites to ask the user to grant the clipboard site permission.
    UNSET: Allow the user to decide.
  clipboardAllowedForUrls: TYPE_LIST
    Allow these sites to access the clipboard. Urls to allow clipboard access.
  clipboardBlockedForUrls: TYPE_LIST
    Block these sites from accessing the clipboard. Urls to block clipboard access.

chrome.devices.managedguest.ColorCorrectionEnabled: Color Correction.
  colorCorrectionEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable color correction accessibility.
    TRUE: Enable color correction accessibility.
  colorCorrectionEnabledSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.CompressionDictionaryTransportEnabled: Compression dictionary transport support.
  compressionDictionaryTransportEnabled: TYPE_BOOL
    true: Allow to use previous responses as compression dictionaries for future requests.
    false: Do not allow to use compression dictionary transport.

chrome.devices.managedguest.CpuTaskScheduler: CPU task scheduler.
  schedulerConfiguration: TYPE_ENUM
    USER_CHOICE: Allow the user to decide.
    CONSERVATIVE: Optimize for stability.
    PERFORMANCE: Optimize for performance.
  cpuTaskSchedulerPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.CssCustomStateDeprecatedSyntaxEnabled: CSS custom state deprecated syntax.
  cssCustomStateDeprecatedSyntaxEnabled: TYPE_BOOL
    true: Allow deprecated syntax.
    false: Do not allow deprecated syntax.

chrome.devices.managedguest.CursorHighlightEnabled: Cursor highlight.
  cursorHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable cursor highlight.
    TRUE: Enable cursor highlight.

chrome.devices.managedguest.CustomTermsOfService: Custom terms of service.
  termsOfServiceUrl
    downloadUri: TYPE_STRING

chrome.devices.managedguest.DataLeakPreventionReportingEnabled: Data controls reporting.
  dataLeakPreventionReportingEnabled: TYPE_BOOL
    true: Enable reporting of data control events.
    false: Disable reporting of data control events.

chrome.devices.managedguest.DataUrlInSvgUseEnabled: Data URL support for SVGUseElement.
  dataUrlInSvgUseEnabled: TYPE_BOOL
    true: Enable Data URL support in SVGUseElement.
    false: Disable Data URL support in SVGUseElement.

chrome.devices.managedguest.DataUrlWhitespacePreservationEnabled: Data URL whitespace preservation for all media types.
  dataUrlWhitespacePreservationEnabled: TYPE_BOOL
    true: Keep whitespace for all mime-types.
    false: Only keep whitespace for text and xml mime-types.

chrome.devices.managedguest.DefaultInsecureContentSetting: Control use of insecure content exceptions.
  defaultInsecureContentSetting: TYPE_ENUM
    BLOCK_INSECURE_CONTENT: Do not allow any site to load blockable mixed content.
    ALLOW_EXCEPTIONS_INSECURE_CONTENT: Allow users to add exceptions to allow blockable mixed content.

chrome.devices.managedguest.DefaultPrintColor: Default color printing mode.
  printingColorDefault: TYPE_ENUM
    COLOR: Color.
    MONOCHROME: Black and white.

chrome.devices.managedguest.DefaultPrintDuplexMode: Default page sides.
  printingDuplexDefault: TYPE_ENUM
    SIMPLEX: One-sided.
    SHORT_EDGE_DUPLEX: Short-edge two-sided printing.
    LONG_EDGE_DUPLEX: Long-edge two-sided printing.

chrome.devices.managedguest.DefaultPrinters: Print preview default.
  specifyDefaultPrinter: TYPE_BOOL
    true: Define the default printer.
    false: Use default print behavior.
  printerTypes: TYPE_ENUM
    CLOUD_AND_LOCAL: Cloud and local.
    CLOUD: Cloud only.
    LOCAL: Local only.
  printerMatching: TYPE_ENUM
    MATCH_BY_NAME: Match by name.
    MATCH_BY_ID: Match by ID.
  defaultPrinterPattern: TYPE_STRING
    Default printer. Enter a regular expression that matches the desired default printer selection. The print preview will default to the first printer to match the regular expression. For example, to match a printer named "Initech Lobby", use "Initech Lobby". To match any of {print "initech-lobby-1"}, {print "initech-lobby-2"}, etc. you could use {print "initech-lobby-.$"}. To match {print "initech-lobby-guest"} or {print "initech-partner-guest"}, you could use {print "initech-.*-guest"}.

chrome.devices.managedguest.DefaultSensorsSetting: Sensors.
  defaultSensorsSetting: TYPE_ENUM
    ALLOW_SENSORS: Allow sites to access sensors.
    BLOCK_SENSORS: Do not allow any site to access sensors.
    UNSET: Allow the user to decide if a site may access sensors.
  sensorsAllowedForUrls: TYPE_LIST
    Allow access to sensors on these sites. For detailed information on valid url patterns, please see https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  sensorsBlockedForUrls: TYPE_LIST
    Block access to sensors on these sites. For detailed information on valid url patterns, please see https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns Note: using only the "*" wildcard is not valid.

chrome.devices.managedguest.DeleteKeyModifier: Control the shortcut used to trigger the Delete "six pack" key.
  deleteKeyModifier: TYPE_ENUM
    NONE: Setting a shortcut for the "Delete" action is disabled.
    ALT: Delete shortcut setting uses the shortcut that contains the alt modifier.
    SEARCH: Delete shortcut setting uses the shortcut that contains the search modifier.
  deleteKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.DeletePrintJobHistoryAllowed: Print job history deletion.
  deletePrintJobHistoryAllowed: TYPE_BOOL
    true: Allow print job history to be deleted.
    false: Do not allow print job history to be deleted.

chrome.devices.managedguest.DeveloperTools: Developer tools.
  developerToolsAvailability: TYPE_ENUM
    ALWAYS_ALLOW_DEVELOPER_TOOLS: Always allow use of built-in developer tools.
    ALLOW_DEVELOPER_TOOLS_EXCEPT_FORCE_INSTALLED: Allow use of built-in developer tools except for force-installed extensions and component extensions.
    NEVER_ALLOW_DEVELOPER_TOOLS: Never allow use of built-in developer tools.
  extensionDeveloperModeSettings: TYPE_ENUM
    UNSET: Use 'developer tools availability' selection.
    ALLOW: Allow use of developer tools on extensions page.
    DISALLOW: Do not allow use of developer tools on extensions page.

chrome.devices.managedguest.DeviceAllowMgsToStoreDisplayProperties: Persist display settings.
  deviceAllowMgsToStoreDisplayProperties: TYPE_BOOL
    true: Display settings set in a managed guest session will persist across sessions.
    false: Display settings set in a managed guest session will not persist across sessions.

chrome.devices.managedguest.DictationEnabled: Dictation.
  dictationEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable dictation.
    TRUE: Enable dictation.

chrome.devices.managedguest.DisableSafeBrowsingProceedAnyway: Disable bypassing Safe Browsing warnings.
  disableSafeBrowsingProceedAnyway: TYPE_BOOL
    true: Do not allow user to bypass Safe Browsing warning.
    false: Allow user to bypass Safe Browsing warning.

chrome.devices.managedguest.DisplayCapturePermissionsPolicyEnabled: Insecure Media Capture.
  displayCapturePermissionsPolicyEnabled: TYPE_BOOL
    true: Deny insecure requests to access display.
    false: Allow requests to access display from non-allowlisted contexts.

chrome.devices.managedguest.DnsInterceptionChecksEnabled: DNS interception checks enabled.
  dnsInterceptionChecksEnabled: TYPE_BOOL
    true: Perform DNS interception checks.
    false: Do not perform DNS interception checks.

chrome.devices.managedguest.DnsOverHttps: DNS over HTTPS.
  dnsOverHttpsMode: TYPE_ENUM
    OFF: Disable DNS over HTTPS.
    AUTOMATIC: Prefer DNS over HTTPS, allow insecure fallback.
    SECURE: Require DNS over HTTPS.
    UNSET: Use system default behavior.
  dnsOverHttpsTemplates: TYPE_LIST
    DNS over HTTPS templates. URI templates of desired DNS over HTTPS resolvers. If the URI template contains a '{?dns}' variable, requests to the resolver will use GET; otherwise requests will use POST.

chrome.devices.managedguest.DnsOverHttpsDomainConfig: DNS over HTTPS included and excluded domains.
  dnsOverHttpsExcludedDomains: TYPE_LIST
    DNS over HTTPS excluded domains. List of fully qualified domain names (FQDN) or domain suffixes noted using a special wildcard prefix '*' to be resolved without using DNS over HTTPS.
  dnsOverHttpsIncludedDomains: TYPE_LIST
    DNS over HTTPS included domains. List of fully qualified domain names (FQDN) or domain suffixes noted using a special wildcard prefix '*' to be resolved using DNS over HTTPS.

chrome.devices.managedguest.DnsOverHttpsTemplatesWithIdentifiers: DNS-over-HTTPS with identifiers.
  dnsOverHttpsSalt: TYPE_STRING
    Salt for hashing identifiers in the URI templates. Salt used for hashing user and device identifiers in the template URIs. Optional starting Chrome version 114.
  dnsOverHttpsTemplatesWithIdentifiers: TYPE_LIST
    DNS-over-HTTPS templates with identifiers. URI templates of desired DNS-over-HTTPS resolvers which contain user or device identifiers. If the URI template contains a '{?dns}' variable, requests to the resolver will use GET; otherwise requests will use POST. If both DNS-over-HTTPS templates and DNS-over-HTTPS templates with identifiers are set, ChromeOS will default to DNS-over-HTTPS templates with identifiers.

chrome.devices.managedguest.DownloadBubbleEnabled: Download bubble.
  downloadBubbleEnabled: TYPE_BOOL
    true: Enable download bubble.
    false: Disable download bubble.

chrome.devices.managedguest.DownloadRestrictions: Download restrictions.
  safeBrowsingDownloadRestrictions: TYPE_ENUM
    NO_SPECIAL_RESTRICTIONS: No special restrictions.
    BLOCK_ALL_MALICIOUS_DOWNLOAD: Block malicious downloads.
    BLOCK_DANGEROUS_DOWNLOAD: Block malicious downloads and dangerous file types.
    BLOCK_POTENTIALLY_DANGEROUS_DOWNLOAD: Block malicious downloads, uncommon or unwanted downloads and dangerous file types.
    BLOCK_ALL_DOWNLOAD: Block all downloads.
  downloadRestrictionsPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.EmojiPickerGifSupportEnabled: GIF Support in Emoji Picker.
  emojiPickerGifSupportEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow GIFs to be selected in the Emoji picker.
    TRUE: Allow GIFs to be selected in the Emoji picker.

chrome.devices.managedguest.EmojiSuggestionEnabled: Emoji suggestions.
  emojiSuggestionEnabled: TYPE_BOOL
    true: Enable emoji suggestions when users type.
    false: Disable emoji suggestions when users type.

chrome.devices.managedguest.EnableCaptureAllowedSettings: Screen video capture allowed by sites.
  screenCaptureAllowedByOrigins: TYPE_LIST
    Allow tab, window, and desktop video capture by these sites. Sites set in this list will be ignored in the 'screenCaptureAllowed' field.
  windowCaptureAllowedByOrigins: TYPE_LIST
    Allow tab and window video capture by these sites. Sites set in this list will be ignored in the 'screenCaptureAllowedByOrigins' and 'screenCaptureAllowed' fields.
  tabCaptureAllowedByOrigins: TYPE_LIST
    Allow tab video capture by these sites. Sites set in this list will be ignored in the 'windowCaptureAllowedByOrigins', 'screenCaptureAllowedByOrigins', and 'screenCaptureAllowed' fields.
  sameOriginTabCaptureAllowedByOrigins: TYPE_LIST
    Allow tab video capture (same site only) by these sites. Sites set in this list will be ignored in the 'tabCaptureAllowedByOrigins', 'windowCaptureAllowedByOrigins', 'screenCaptureAllowedByOrigins', and 'screenCaptureAllowed' fields.

chrome.devices.managedguest.EnableDeprecatedPrivetPrinting: Deprecated privet printing.
  enableDeprecatedPrivetPrinting: TYPE_BOOL
    true: Enable deprecated privet printing.
    false: Disable deprecated privet printing.

chrome.devices.managedguest.EncryptedClientHelloEnabled: TLS encrypted ClientHello.
  encryptedClientHelloEnabled: TYPE_BOOL
    true: Enable the TLS Encrypted ClientHello experiment.
    false: Disable the TLS Encrypted ClientHello experiment.

chrome.devices.managedguest.EnhancedNetworkVoicesInSelectToSpeakAllowed: Select-to-speak.
  enhancedNetworkVoicesInSelectToSpeakAllowed: TYPE_BOOL
    true: Allow sending text to Google servers for enhanced Select-to-speak.
    false: Do not allow sending text to Google servers for enhanced Select-to-speak.

chrome.devices.managedguest.EnterpriseHardwarePlatformApiEnabled: Enterprise Hardware Platform API.
  enterpriseHardwarePlatformApiEnabled: TYPE_BOOL
    true: Allow managed extensions to use the Enterprise Hardware Platform API.
    false: Do not allow managed extensions to use the Enterprise Hardware Platform API.

chrome.devices.managedguest.EventPathEnabled: Re-enable the Event.path API until Chrome 115.
  eventPathEnabled: TYPE_ENUM
    UNSET: Enable Event.path API until Chrome 108.
    FALSE: Disable Event.path API.
    TRUE: Enable Event.path API until Chrome 115.

chrome.devices.managedguest.ExplicitlyAllowedNetworkPorts: Allowed network ports.
  explicitlyAllowedNetworkPorts: TYPE_LIST
    554: port 554 (expires 2021/10/15).
    989: port 989 (expires 2022/02/01).
    990: port 990 (expires 2022/02/01).
    6566: port 6566 (expires 2021/10/15).
    10080: port 10080 (expires 2022/04/01).

chrome.devices.managedguest.ExtensionExtendedBackgroundLifetimeForPortConnectionsToUrls: Extended background lifetime.
  extensionExtendedBackgroundLifetimeForPortConnectionsToUrls: TYPE_LIST
    Origins that grant extended background lifetime to connecting extensions. Enter a list of origins. Extensions that connect to one of these origins will be be kept running as long as the port is connected. One URL per line.

chrome.devices.managedguest.ExtensionManifestVTwoAvailability: Manifest V2 extension availability.
  extensionManifestVTwoAvailability: TYPE_ENUM
    DEFAULT: Default browser behavior.
    DISABLE: Disable manifest V2 extensions.
    ENABLE: Enable manifest V2 extensions.
    ENABLE_FOR_FORCED_EXTENSIONS: Enable force-installed manifest V2 extensions.

chrome.devices.managedguest.ExternalStorage: External storage devices.
  externalStorageDevices: TYPE_ENUM
    READ_WRITE: Allow read and write access to all external storage devices.
    READ_ONLY: Allow read only access to all external storage devices.
    DISALLOW: Do not allow read and write access to external storage devices.
  externalStorageAllowlist: TYPE_LIST
    Specify devices to always have read and write access. USB devices which are allowlisted for read and write access. To identify a specific device, enter colon separated hexadecimal pairs of USB Vendor Identifier and Product Identifier.

chrome.devices.managedguest.FastPairEnabled: Fast Pair (fast Bluetooth pairing).
  fastPairEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable Fast Pair.
    TRUE: Enable Fast Pair.

chrome.devices.managedguest.FeedbackSurveysEnabled: Google Chrome surveys.
  feedbackSurveysEnabled: TYPE_BOOL
    true: Enable in-product surveys.
    false: Disable in-product surveys.

chrome.devices.managedguest.FElevenKeyModifier: Control the shortcut used to trigger F11.
  fElevenKeyModifier: TYPE_ENUM
    DISABLED: F11 settings are disabled.
    ALT: F11 settings use the shortcut that contains the alt modifier.
    SHIFT: F11 settings use the shortcut that contains the shift modifier.
    CTRL_SHIFT: F11 settings use the shortcut that contains the modifiers ctrl and shift.
  fElevenKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.FileOrDirectoryPickerWithoutGestureAllowedForOrigins: File/directory picker without user gesture.
  fileOrDirectoryPickerWithoutGestureAllowedForOrigins: TYPE_LIST
    Allow file or directory picker APIs to be called without prior user gesture. Urls to allow file or directory pickers without user gesture.

chrome.devices.managedguest.FileSystemRead: File system read access.
  defaultFileSystemReadGuardSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ASK_FILE_SYSTEM_READ: Allow sites to ask the user to grant read access to files and directories.
    BLOCK_FILE_SYSTEM_READ: Do not allow sites to request read access to files and directories.
  fileSystemReadAskForUrls: TYPE_LIST
    Allow file system read access on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  fileSystemReadBlockedForUrls: TYPE_LIST
    Block read access on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.

chrome.devices.managedguest.FileSystemSyncAccessHandleAsyncInterfaceEnabled: File System Access API async interface.
  fileSystemSyncAccessHandleAsyncInterfaceEnabled: TYPE_BOOL
    true: Re-enable the deprecated async interface for FileSystemSyncAccessHandle.
    false: Disable the deprecated async interface for FileSystemSyncAccessHandle.

chrome.devices.managedguest.FileSystemWrite: File system write access.
  defaultFileSystemWriteGuardSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ASK_FILE_SYSTEM_WRITE: Allow sites to ask the user to grant write access to files and directories.
    BLOCK_FILE_SYSTEM_WRITE: Do not allow sites to request write access to files and directories.
  fileSystemWriteAskForUrls: TYPE_LIST
    Allow write access to files and directories on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  fileSystemWriteBlockedForUrls: TYPE_LIST
    Block write access to files and directories on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.

chrome.devices.managedguest.FocusModeSoundsEnabled: Sounds in Focus Mode.
  focusModeSoundsEnabled: TYPE_ENUM
    ENABLED: All sounds play in Focus Mode.
    FOCUS_SOUNDS: Only Focus Sounds play in Focus Mode.
    DISABLED: Disable all sounds in Focus Mode.

chrome.devices.managedguest.ForceEnablePepperVideoDecoderDevApi: PPB_VideoDecoder(Dev) API support.
  forceEnablePepperVideoDecoderDevApi: TYPE_BOOL
    true: Enable PPB_VideoDecoder(Dev) API.
    false: Let the browser decide.

chrome.devices.managedguest.ForceMajorVersionToMinorPositionInUserAgent: Freeze User-Agent string version.
  forceMajorVersionToMinorPositionInUserAgent: TYPE_ENUM
    DEFAULT: Default to browser settings for User-Agent string.
    FORCE_DISABLED: Do not freeze the major version.
    FORCE_ENABLED: Freeze the major version as 99.

chrome.devices.managedguest.ForceMaximizeOnFirstRun: Maximize window on first run.
  forceMaximizeOnFirstRun: TYPE_BOOL
    true: Maximize the first browser window on first run.
    false: Default system behavior (depends on screen size).

chrome.devices.managedguest.ForcePermissionPolicyUnloadDefaultEnabled: Unload event handlers.
  forcePermissionPolicyUnloadDefaultEnabled: TYPE_BOOL
    true: Enable unload event handlers.
    false: Do not enable unload event handlers.

chrome.devices.managedguest.FTwelveKeyModifier: Control the shortcut used to trigger F12.
  fTwelveKeyModifier: TYPE_ENUM
    DISABLED: F12 settings are disabled.
    ALT: F12 settings use the shortcut that contains the alt modifier.
    SHIFT: F12 settings use the shortcut that contains the shift modifier.
    CTRL_SHIFT: F12 settings use the shortcut that contains the modifiers ctrl and shift.
    UNSET: Allow the user to decide.
  fTwelveKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.FullscreenAllowed: Fullscreen mode.
  fullscreenAllowed: TYPE_BOOL
    true: Allow fullscreen mode.
    false: Do not allow fullscreen mode.

chrome.devices.managedguest.GenAiDefaultSettings: Generative AI policy defaults.
  genAiDefaultSettings: TYPE_ENUM
    ALLOWED: Allow GenAI features and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow GenAI features without improving AI models.
    DISABLED: Do not allow GenAI features.
    UNSET_DEFAULTS: Unset GenAI default policy values.
    UNSET: Use the default Chrome behavior.

chrome.devices.managedguest.GenAiVcBackgroundSettings: Video conference background settings.
  genAiVcBackgroundSettings: TYPE_ENUM
    ALLOWED: Allow Generative AI VC background and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow Generative AI VC background without improving AI models.
    DISABLED: Do not allow Generative AI VC background.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.devices.managedguest.GenAiWallpaperSettings: Wallpaper settings.
  genAiWallpaperSettings: TYPE_ENUM
    ALLOWED: Allow Generative AI wallpaper and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow Generative AI wallpaper without improving AI models.
    DISABLED: Do not allow Generative AI wallpaper.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.devices.managedguest.GloballyScopeHttpAuthCacheEnabled: Globally scoped HTTP authentication cache.
  globallyScopeHttpAuthCacheEnabled: TYPE_BOOL
    true: HTTP authentication credentials entered in the context of one site will automatically be used in the context of another.
    false: HTTP authentication credentials are scoped to top-level sites.

chrome.devices.managedguest.GoogleCast: Cast.
  showCastIconInToolbar: TYPE_BOOL
    true: Always show the Cast icon in the toolbar.
    false: Do not show the Cast icon in the toolbar by default, but let users choose.
  enableMediaRouter: TYPE_BOOL
    true: Allow users to Cast.
    false: Do not allow users to Cast.
  mediaRouterCastAllowAllIps: TYPE_ENUM
    UNSET: Enable restrictions, unless the CastAllowAllIPs feature is turned on.
    FALSE: Enable restrictions.
    TRUE: Disable restrictions (allow all IP addresses).

chrome.devices.managedguest.GoogleDriveSyncing: Google Drive syncing.
  driveDisabledBool: TYPE_BOOL
    true: Disable Google Drive syncing.
    false: Enable Google Drive syncing.

chrome.devices.managedguest.GoogleSearchSidePanelEnabled: Side Panel search.
  googleSearchSidePanelEnabled: TYPE_BOOL
    true: Enable Side Panel search on all web pages.
    false: Disable Side Panel search on all web pages.

chrome.devices.managedguest.HighContrastEnabled: High contrast.
  highContrastEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable high contrast.
    TRUE: Enable high contrast.

chrome.devices.managedguest.HighEfficiencyModeEnabled: High efficiency mode.
  highEfficiencyModeEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable high efficiency mode.
    TRUE: Enable high efficiency mode.

chrome.devices.managedguest.HomeAndEndKeysModifier: Control the shortcut used to trigger the Home/End "six pack" keys.
  homeAndEndKeysModifier: TYPE_ENUM
    NONE: Home/End settings are disabled.
    ALT: Home/End settings use the shortcut that contains the alt modifier.
    SEARCH: Home/End settings use the shortcut that contains the search modifier.
  homeAndEndKeysModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.HomeButton: Home button.
  showHomeButton: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never show "Home" button.
    TRUE: Always show "Home" button.
  homeButtonPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.Homepage: Homepage.
  homepageIsNewTabPage: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Homepage is always the URL set in 'homepageLocation'.
    TRUE: Homepage is always the new tab page.
  homepageLocation: TYPE_STRING
    Homepage URL. Specifies the URL that should be used as the home page in managed Chrome.
  homepagePolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.HstsPolicyBypassList: HSTS policy bypass list.
  hstsPolicyBypassList: TYPE_LIST
    List of hostnames that will bypass the HSTS policy check . Enter a list of hostnames that will be exempt from the HSTS policy check.

chrome.devices.managedguest.IdleSettingsExtended: Idle settings.
  lidCloseAction: TYPE_ENUM
    SLEEP: Sleep.
    LOGOUT: Logout.
    SHUTDOWN: Shutdown.
    DO_NOTHING: Do nothing.
  idleDelayAc: TYPE_INT64
  idleWarningDelayAc: TYPE_INT64
  idleActionAc: TYPE_ENUM
    SLEEP: Sleep.
    LOGOUT: Logout.
    SHUTDOWN: Shut down.
    DO_NOTHING: Do nothing.
  screenDimDelayAc: TYPE_INT64
  screenOffDelayAc: TYPE_INT64
  screenLockDelayAc: TYPE_INT64
  idleDelayBattery: TYPE_INT64
  idleWarningDelayBattery: TYPE_INT64
  idleActionBattery: TYPE_ENUM
    SLEEP: Sleep.
    LOGOUT: Logout.
    SHUTDOWN: Shut down.
    DO_NOTHING: Do nothing.
  screenDimDelayBattery: TYPE_INT64
  screenOffDelayBattery: TYPE_INT64
  screenLockDelayBattery: TYPE_INT64
  lockOnSleepOrLidClose: TYPE_ENUM
    UNSET: Allow user to configure.
    FALSE: Don't lock screen.
    TRUE: Lock screen.

chrome.devices.managedguest.IncognitoMode: Incognito mode.
  incognitoModeAvailability: TYPE_ENUM
    AVAILABLE: Allow incognito mode.
    UNAVAILABLE: Disallow incognito mode.
    FORCED: Force incognito mode.

chrome.devices.managedguest.InsecureContentAllowedForUrls: Allow insecure content on these sites.
  insecureContentAllowedForUrls: TYPE_LIST
    URL patterns to allow. Specifies which sites should allow insecure (HTTP) content to be shown.

chrome.devices.managedguest.InsecureContentBlockedForUrls: Block insecure content on these sites.
  insecureContentBlockedForUrls: TYPE_LIST
    URL patterns to block. Specifies which sites should block insecure (HTTP) content from being shown.

chrome.devices.managedguest.InsecureFormsWarningsEnabled: Insecure forms.
  insecureFormsWarningsEnabled: TYPE_BOOL
    true: Show warnings and disable autofill on insecure forms.
    false: Do not show warnings or disable autofill on insecure forms.

chrome.devices.managedguest.InsecureHashesInTlsHandshakesEnabled: Insecure hashes in TLS handshakes.
  insecureHashesInTlsHandshakesEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow insecure hashes in TLS handshakes.
    TRUE: Allow insecure hashes in TLS handshakes.

chrome.devices.managedguest.InsecurePrivateNetworkRequestsAllowed: Requests from insecure websites to more-private network endpoints.
  insecurePrivateNetworkRequestsAllowed: TYPE_BOOL
    true: Insecure websites are allowed to make requests to any network endpoint.
    false: Allow the user to decide.
  insecurePrivateNetworkRequestsAllowedForUrls: TYPE_LIST
    URL patterns to allow. Network requests to more-private endpoints, from insecure origins not covered by the patterns specified here, will use the global default value.

chrome.devices.managedguest.InsertKeyModifier: Control the shortcut used to trigger the Insert "six pack" key.
  insertKeyModifier: TYPE_ENUM
    NONE: Setting a shortcut for the "Insert" action is disabled.
    SEARCH: Insert shortcut setting uses the shortcut that contains the search modifier.
  insertKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.IntensiveWakeUpThrottlingEnabled: Javascript IntensiveWakeUpThrottling.
  intensiveWakeUpThrottlingEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Force no throttling of background JavaScript timers.
    TRUE: Force throttling of background JavaScript timers.

chrome.devices.managedguest.IntranetRedirectBehavior: Intranet Redirection Behavior.
  intranetRedirectBehavior: TYPE_ENUM
    DEFAULT: Use default browser behavior.
    DISABLE_INTERCEPTION_CHECKS_DISABLE_INFOBAR: Disable DNS interception checks and did-you-mean "http://intranetsite/" infobars.
    DISABLE_INTERCEPTION_CHECKS_ENABLE_INFOBAR: Disable DNS interception checks; allow did-you-mean "http://intranetsite/" infobars.
    ENABLE_INTERCEPTION_CHECKS_ENABLE_INFOBAR: Allow DNS interception checks and did-you-mean "http://intranetsite/" infobars.

chrome.devices.managedguest.JavaScriptJitSettings: JavaScript JIT.
  defaultJavaScriptJitSetting: TYPE_ENUM
    ALLOW_JAVA_SCRIPT_JIT: Allow sites to run JavaScript JIT.
    BLOCK_JAVA_SCRIPT_JIT: Do not allow sites to run JavaScript JIT.
  javaScriptJitAllowedForSites: TYPE_LIST
    Allow JavaScript to use JIT on these sites. Specifies the site allowlist for JavaScript to use JIT.
  javaScriptJitBlockedForSites: TYPE_LIST
    Block JavaScript from using JIT on these sites. Specifies the site blocklist for JavaScript to be blocked from using JIT.

chrome.devices.managedguest.KeepFullscreenWithoutNotificationUrlAllowList: Fullscreen after unlock.
  keepFullscreenWithoutNotificationUrlAllowList: TYPE_LIST
    Keep full screen after unlock without warning for the following URLs. Enter a list of URL patterns, one per line.

chrome.devices.managedguest.KerberosCustomPrefilledConfigSettingGroup: Kerberos ticket default configuration.
  kerberosCustomPrefilledConfig: TYPE_STRING
    Custom configuration. Kerberos ticket prefilled config.
  kerberosUseCustomPrefilledConfig: TYPE_BOOL
    true: Customize Kerberos configuration.
    false: Use recommended Kerberos configuration.

chrome.devices.managedguest.KerberosDomainAutocomplete: Autocomplete Kerberos domain.
  kerberosDomainAutocomplete: TYPE_STRING
    Kerberos domain. Autocomplete Kerberos domain.

chrome.devices.managedguest.KerberosTickets: Kerberos tickets.
  kerberosEnabled: TYPE_BOOL
    true: Enable kerberos.
    false: Disable kerberos.

chrome.devices.managedguest.KeyboardFocusableScrollersEnabled: Keyboard focusable scrollers.
  keyboardFocusableScrollersEnabled: TYPE_BOOL
    true: Allow scrollers to be focusable by default.
    false: Do not allow scrollers to be focusable by default.

chrome.devices.managedguest.KeyboardFocusHighlightEnabled: Keyboard focus highlighting.
  keyboardFocusHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable keyboard focus highlighting.
    TRUE: Enable keyboard focus highlighting.

chrome.devices.managedguest.KeyboardFunctionKeys: Keyboard.
  keyboardDefaultToFunctionKeys: TYPE_BOOL
    true: Treat top-row keys as function keys, but allow user to change.
    false: Treat top-row keys as media keys, but allow user to change.

chrome.devices.managedguest.LargeCursorEnabled: Large cursor.
  largeCursorEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable large cursor.
    TRUE: Enable large cursor.

chrome.devices.managedguest.LensDesktopNtpSearchEnabled: New Tab page Google Lens button.
  lensDesktopNtpSearchEnabled: TYPE_BOOL
    true: Show the Google Lens button in the search box on the New Tab page.
    false: Do not show the Google Lens button in the search box on the New Tab page.

chrome.devices.managedguest.LensOnGalleryEnabled: Lens Gallery App integration.
  lensOnGalleryEnabled: TYPE_BOOL
    true: Enable Lens integration.
    false: Disable Lens integration.
  lensOnGalleryEnabledSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.LensOverlaySettings: Google Lens Overlay.
  lensOverlaySettings: TYPE_ENUM
    ENABLED: Enable Google Lens overlay.
    DISABLED: Disable Google Lens overlay.

chrome.devices.managedguest.LensRegionSearchEnabled: Google Lens region search.
  lensRegionSearchEnabled: TYPE_BOOL
    true: Enable Google Lens region search.
    false: Disable Google Lens region search.

chrome.devices.managedguest.LoadCryptoTokenExtension: Re-enable CryptoToken component extension until Chrome 107.
  loadCryptoTokenExtension: TYPE_BOOL
    true: Enable the CryptoToken component extension until Chrome 107.
    false: Enable the CryptoToken component extension until Chrome 105.

chrome.devices.managedguest.LockIconInAddressBarEnabled: Lock icon in the omnibox for secure connections.
  lockIconInAddressBarEnabled: TYPE_BOOL
    true: Use the lock icon for secure connections.
    false: Use default icons for secure connections.

chrome.devices.managedguest.LookalikeWarningAllowlistDomains: Suppress lookalike domain warnings on domains.
  lookalikeWarningAllowlistDomains: TYPE_LIST
    Allowlisted Domains. Enter list of domains where Chrome should prevent the display of lookalike URL warnings.

chrome.devices.managedguest.ManagedBookmarksSetting: Managed bookmarks.
  managedBookmarks
    bookmarks
      folder
        name: TYPE_STRING
        entries
      link
        name: TYPE_STRING
        url: TYPE_STRING
    toplevelName: TYPE_STRING

chrome.devices.managedguest.ManagedGuestSession: Managed guest session.
  userDisplayName: TYPE_STRING
    Session name to display on login screen. Specifies the name of a managed guest session on the login screen.
  managedGuestSessionAvailability: TYPE_ENUM
    NOT_ALLOWED: Do not allow managed guest sessions.
    ALLOWED: Allow managed guest sessions.
    AUTO_LAUNCH: Auto-launch managed guest session.
  autoLaunchDelaySeconds: TYPE_INT64
    Auto-launch delay. Number of seconds to delay before launching the managed guest session. During this time the sign-in screen will be visible.
  deviceHealthMonitoring: TYPE_BOOL
    true: Enable device health monitoring.
    false: Disable device health monitoring.
  systemLogUploadEnabled: TYPE_BOOL
    true: Enable device system log upload.
    false: Disable device system log upload.
  displayRotation: TYPE_ENUM
    UNSET: No policy set (allow the device to keep its current display rotation).
    ROTATE_0: 0 degrees.
    ROTATE_90: 90 degrees.
    ROTATE_180: 180 degrees.
    ROTATE_270: 270 degrees.

chrome.devices.managedguest.ManagedGuestSessionV2: Managed guest session.
  userDisplayName: TYPE_STRING
    Session name to display on login screen. Specifies the name of a managed guest session on the login screen.
  managedGuestSessionAvailability: TYPE_ENUM
    NOT_ALLOWED: Do not allow managed guest sessions.
    ALLOWED: Allow managed guest sessions.
    AUTO_LAUNCH: Auto-launch managed guest session.
  autoLaunchDelaySeconds: TYPE_INT64
    Auto-launch delay. Number of seconds to delay before launching the managed guest session. During this time the sign-in screen will be visible.
  deviceHealthMonitoring: TYPE_BOOL
    true: Enable device health monitoring.
    false: Disable device health monitoring.
  displayRotation: TYPE_ENUM
    UNSET: No policy set (allow the device to keep its current display rotation).
    ROTATE_0: 0 degrees.
    ROTATE_90: 90 degrees.
    ROTATE_180: 180 degrees.
    ROTATE_270: 270 degrees.

chrome.devices.managedguest.MaxInvalidationFetchDelay: Policy fetch delay.
  maxInvalidationFetchDelay: TYPE_INT64

chrome.devices.managedguest.MaxInvalidationFetchDelayV2: Policy fetch delay.
  maxInvalidationFetchDelay: TYPE_INT64

chrome.devices.managedguest.MemorySaverModeSavings: Memory saver.
  memorySaverModeSavings: TYPE_ENUM
    MODERATE: Apply moderate memory savings.
    BALANCED: Apply balanced memory savings.
    MAXIMUM: Apply maximum memory savings.
    UNSET: Allow the user to decide.

chrome.devices.managedguest.MonoAudioEnabled: Mono audio.
  monoAudioEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable mono audio.
    TRUE: Enable mono audio.

chrome.devices.managedguest.MultiScreenCaptureAllowedForUrls: URLs allowed for multi-screen capture .
  multiScreenCaptureAllowedForUrls: TYPE_LIST
    URLs allowed for multi-screen capture . The getAllScreensMedia API allows isolated web applications to capture multiple surfaces at once without additional user permission.

chrome.devices.managedguest.MutationEventsEnabled: Mutation Events.
  mutationEventsEnabled: TYPE_BOOL
    true: Temporarily re-enable mutation events.
    false: Mutation events stop firing after the removal date.

chrome.devices.managedguest.NativeClientForceAllowed: Allow Native Client (NaCl).
  nativeClientForceAllowed: TYPE_BOOL
    true: Allow Native Client to run even if it is disabled by default.
    false: Use default behavior.

chrome.devices.managedguest.NetworkFileShares: Network file shares.
  networkFileSharesAllowed: TYPE_BOOL
    true: Allow network file shares.
    false: Block network file shares.
  netBiosShareDiscoveryEnabled: TYPE_BOOL
    true: Use NetBIOS discovery.
    false: Do not allow NetBIOS discovery.
  ntlmShareAuthenticationEnabled: TYPE_BOOL
    true: Use NTLM authentication.
    false: Do not use NTLM authentication.
  networkFileSharesPreconfiguredShares
    preconfiguredFiles
      mode: TYPE_ENUM
        DROP_DOWN:
        PRE_MOUNT:
      shareUrl: TYPE_STRING

chrome.devices.managedguest.NewBaseUrlInheritanceBehaviorAllowed: Enable the feature NewBaseUrlInheritanceBehavior.
  newBaseUrlInheritanceBehaviorAllowed: TYPE_BOOL
    true: NewBaseUrlInheritanceBehavior feature available.
    false: NewBaseUrlInheritanceBehavior feature disabled.

chrome.devices.managedguest.NewTabPageLocation: New tab page.
  newTabPageLocation: TYPE_STRING
    New tab URL (leave empty for default). Specifies the URL of the page that should load when Chrome opens a new tab.

chrome.devices.managedguest.Notifications: Notifications.
  defaultNotificationsSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_NOTIFICATIONS: Allow sites to show desktop notifications.
    BLOCK_NOTIFICATIONS: Do not allow sites to show desktop notifications.
    ASK_NOTIFICATIONS: Always ask the user if a site can show desktop notifications.
  notificationsAllowedForUrls: TYPE_LIST
    Allow these sites to show notifications. Urls to allow notifications. Prefix domain with [*.] to include all subdomains.Maximum of 1000 URLs. .
  notificationsBlockedForUrls: TYPE_LIST
    Block notifications on these sites. Urls to block notifications. Prefix domain with [*.] to include all subdomains.Maximum of 1000 URLs. .

chrome.devices.managedguest.OptimizationGuideFetchingEnabled: Optimization Guide Fetching.
  optimizationGuideFetchingEnabled: TYPE_BOOL
    true: Enable fetching of page load metadata and machine learning models to enhance the browsing experience.
    false: Disable fetching of page load metadata and machine learning models that enhance the browsing experience.

chrome.devices.managedguest.OriginAgentClusterDefaultEnabled: Origin-keyed agent clustering.
  originAgentClusterDefaultEnabled: TYPE_BOOL
    true: Use origin-keyed agent clusters.
    false: Use site-keyed agent clusters.

chrome.devices.managedguest.OsColorMode: ChromeOS color mode.
  osColorMode: TYPE_ENUM
    LIGHT: Recommend the light theme.
    DARK: Recommend the dark theme.
    AUTO: Recommend auto mode.

chrome.devices.managedguest.OverrideSecurityRestrictionsOnInsecureOrigin: Override insecure origin restrictions.
  overrideSecurityRestrictionsOnInsecureOrigin: TYPE_LIST
    Origin or hostname patterns to ignore insecure origins security restrictions. Specifies the origin or hostname patterns for which restrictions on insecure origins should not apply.

chrome.devices.managedguest.PageUpAndPageDownKeysModifier: Control the shortcut used to trigger the PageUp/PageDown "six pack" keys.
  pageUpAndPageDownKeysModifier: TYPE_ENUM
    NONE: PageUp/PageDown settings are disabled.
    ALT: PageUp/PageDown settings use the shortcut that contains the alt modifier.
    SEARCH: PageUp/PageDown settings use the shortcut that contains the search modifier.
  pageUpAndPageDownKeysModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.PaymentMethodQueryEnabled: Payment methods.
  paymentMethodQueryEnabled: TYPE_BOOL
    true: Allow websites to check if the user has payment methods saved.
    false: Always tell websites that no payment methods are saved.

chrome.devices.managedguest.PdfLocalFileAccessAllowedForDomains: Local file access to file:// URLs in the PDF Viewer.
  pdfLocalFileAccessAllowedForDomains: TYPE_LIST
    Allowed URLs. List of file URLs with local access enabled in the PDF viewer.

chrome.devices.managedguest.PdfUseSkiaRendererEnabled: Renderer for PDF files.
  pdfUseSkiaRendererEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Use AGG renderer for PDF files.
    TRUE: Use Skia renderer for PDF files.

chrome.devices.managedguest.PhysicalKeyboardAutocorrect: Physical keyboard autocorrect.
  physicalKeyboardAutocorrect: TYPE_BOOL
    true: Enable physical keyboard autocorrect.
    false: Disable physical keyboard autocorrect.

chrome.devices.managedguest.PhysicalKeyboardPredictiveWriting: Physical keyboard predictive writing.
  physicalKeyboardPredictiveWriting: TYPE_BOOL
    true: Enable physical keyboard predictive writing.
    false: Disable physical keyboard predictive writing.

chrome.devices.managedguest.Popups: Pop-ups.
  defaultPopupsSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_POPUPS: Allow all pop-ups.
    BLOCK_POPUPS: Block all pop-ups.
  popupsAllowedForUrls: TYPE_LIST
    Allow pop-ups on these sites. Urls to allow pop-ups.
  popupsBlockedForUrls: TYPE_LIST
    Block pop-ups on these sites. Urls to block pop-ups.

chrome.devices.managedguest.PostQuantumKeyAgreementEnabled: Post-quantum TLS.
  postQuantumKeyAgreementEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow post-quantum key agreement in TLS connections.
    TRUE: Allow post-quantum key agreement in TLS connections.

chrome.devices.managedguest.PowerManagementUsesAudioActivity: Power management uses audio activity.
  powerManagementUsesAudioActivity: TYPE_BOOL
    true: Disallow idle action when audio is playing.
    false: Allow idle action when audio is playing.

chrome.devices.managedguest.PowerManagementUsesVideoActivity: Power management uses video activity.
  powerManagementUsesVideoActivity: TYPE_BOOL
    true: Disallow idle action when video is playing.
    false: Allow idle action when video is playing.

chrome.devices.managedguest.PpapiSharedImagesForVideoDecoderAllowed: Allow Pepper to use shared images for video decoding.
  ppapiSharedImagesForVideoDecoderAllowed: TYPE_BOOL
    true: Allow new implementation.
    false: Force old implementation.

chrome.devices.managedguest.PpApiSharedImagesSwapChainAllowed: Modern buffer allocation for Graphics3D APIs PPAPI plugin.
  ppApiSharedImagesSwapChainAllowed: TYPE_BOOL
    true: Allow new implementation.
    false: Force old implementation.

chrome.devices.managedguest.PrefixedStorageInfoEnabled: Re-enable window.webkitStorageInfo API.
  prefixedStorageInfoEnabled: TYPE_BOOL
    true: Enable window.webkitStorageInfo.
    false: Disable window.webkitStorageInfo.

chrome.devices.managedguest.PrefixedVideoFullscreenApiAvailability: Prefixed video fullscreen API.
  prefixedVideoFullscreenApiAvailability: TYPE_ENUM
    RUNTIME_ENABLED: Use the default Chrome setting.
    DISABLED: Disable prefixed video fullscreen API.
    ENABLED: Enable prefixed video fullscreen API.

chrome.devices.managedguest.PrimaryMouseButtonSwitch: Primary mouse button.
  primaryMouseButtonSwitch: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Left button is primary.
    TRUE: Right button is primary.

chrome.devices.managedguest.PrinterTypeDenyList: Blocked printer types.
  printerTypeDenyList: TYPE_LIST
    privet: Privet zeroconf-based protocol (deprecated).
    extension: Extension-based.
    pdf: Save as PDF.
    local: Local printer.
    cloud: Google Cloud Print (deprecated).

chrome.devices.managedguest.PrintHeaderFooter: Print headers and footers.
  printHeaderFooter: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never print headers and footers.
    TRUE: Always print headers and footers.
  printHeaderFooterCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.PrintingAllowedBackgroundGraphicsModes: Background graphics printing restriction.
  printingAllowedBackgroundGraphicsModes: TYPE_ENUM
    ANY: Allow the user to decide.
    ENABLED: Always require printing of background images.
    DISABLED: Do not allow printing of background images.

chrome.devices.managedguest.PrintingAllowedPinModes: Restrict PIN printing mode.
  printingAllowedPinModes: TYPE_ENUM
    ANY_PIN_PRINTING_MODE: Do not restrict PIN printing mode.
    PIN_PRINTING_ONLY: Always require PIN printing.
    NON_PIN_PRINTING_ONLY: Do not allow PIN printing.

chrome.devices.managedguest.PrintingBackgroundGraphicsDefault: Background graphics printing default.
  printingBackgroundGraphicsDefault: TYPE_ENUM
    DISABLED: Disable background graphics printing mode by default.
    ENABLED: Enable background graphics printing mode by default.

chrome.devices.managedguest.PrintingMaxSheetsAllowed: Maximum sheets.
  printingMaxSheetsAllowedNullable: TYPE_INT64

chrome.devices.managedguest.PrintingPaperSizeDefault: Default printing page size.
  printingPaperSizeEnum: TYPE_ENUM
    UNSET: No policy set.
    NA_LETTER_8_5X11IN: Letter.
    NA_LEGAL_8_5X14IN: Legal.
    ISO_A4_210X297MM: A4.
    NA_LEDGER_11X17IN: Tabloid.
    ISO_A3_297X420MM: A3.
    CUSTOM: Custom.
  printingPaperSizeWidth: TYPE_STRING
    Page width (in millimeters). Sets a custom page width (in millimeters).
  printingPaperSizeHeight: TYPE_STRING
    Page height (in millimeters). Sets a custom page height (in millimeters).

chrome.devices.managedguest.PrintingPinDefault: Default PIN printing mode.
  printingPinDefault: TYPE_ENUM
    DEFAULT_TO_PIN_PRINTING: With PIN.
    DEFAULT_TO_NOT_PIN_PRINTING: Without PIN.

chrome.devices.managedguest.PrintJobHistoryExpirationPeriodNew: Print job history retention period.
  printJobHistoryExpirationPeriodDaysNew: TYPE_INT64

chrome.devices.managedguest.PrintJobHistoryExpirationPeriodNewV2: Print job history retention period.
  printJobHistoryExpirationPeriodDaysNew: TYPE_INT64

chrome.devices.managedguest.PrintPdfAsImage: Print PDF as image.
  printPdfAsImageAvailability: TYPE_BOOL
    true: Allow users to print PDF documents as images.
    false: Do not allow users to print PDF documents as images.
  printRasterizePdfDpi: TYPE_INT64
  printPdfAsImageDefault: TYPE_BOOL
    true: Default to printing PDFs as images when available.
    false: Default to printing PDFs without being rasterized.

chrome.devices.managedguest.PrivacyScreenEnabled: Privacy screen.
  privacyScreenEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Always disable the privacy screen.
    TRUE: Always enable the privacy screen.

chrome.devices.managedguest.PrivateNetworkAccessRestrictionsEnabled: Private Network Access restrictions.
  privateNetworkAccessRestrictionsEnabled: TYPE_BOOL
    true: Apply restrictions to requests to more-private network endpoints.
    false: Use default behavior when determining if websites can make requests to network endpoints.

chrome.devices.managedguest.PromptForDownloadLocation: Download location prompt.
  promptForDownloadLocation: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not ask the user (downloads start immediately).
    TRUE: Ask the user where to save the file before downloading.

chrome.devices.managedguest.QrCodeGeneratorEnabled: QR Code Generator.
  qrCodeGeneratorEnabled: TYPE_BOOL
    true: Enable QR Code Generator.
    false: Disable QR Code Generator.

chrome.devices.managedguest.QuickAnswersEnabled: Quick Answers.
  quickAnswersEnabled: TYPE_BOOL
    true: Enable Quick Answers.
    false: Disable Quick Answers.
  quickAnswersDefinitionEnabled: TYPE_BOOL
    true: Enable Quick Answers definition.
    false: Disable Quick Answers definition.
  quickAnswersTranslationEnabled: TYPE_BOOL
    true: Enable Quick Answers translation.
    false: Disable Quick Answers translation.
  quickAnswersUnitConversionEnabled: TYPE_BOOL
    true: Enable Quick Answers unit conversion.
    false: Disable Quick Answers unit conversion.

chrome.devices.managedguest.QuicProtocol: QUIC protocol.
  quicAllowed: TYPE_BOOL
    true: Enable.
    false: Disable.

chrome.devices.managedguest.RemoteAccessHostAllowEnterpriseRemoteSupportConnections: Enterprise remote support connections.
  remoteAccessHostAllowEnterpriseRemoteSupportConnections: TYPE_BOOL
    true: Allow remote support connections from enterprise admins.
    false: Prevent remote support connections from enterprise admins.

chrome.devices.managedguest.RemoteAccessHostAllowRemoteSupportConnections: Remote support connections.
  remoteAccessHostAllowRemoteSupportConnections: TYPE_BOOL
    true: Allow remote support connections.
    false: Prevent remote support connections.

chrome.devices.managedguest.RemoteAccessHostClientDomainList: Remote access clients.
  remoteAccessHostClientDomainList: TYPE_LIST
    Remote access client domain. Configure the required domain names for remote access clients.

chrome.devices.managedguest.RemoteAccessHostClipboardSizeBytes: Clipboard sync max size.
  remoteAccessHostClipboardSizeBytes: TYPE_INT64

chrome.devices.managedguest.RemoteAccessHostDomainList: Remote access hosts.
  remoteAccessHostDomainList: TYPE_LIST
    Remote access host domain. Configure the required domain names for remote access hosts.

chrome.devices.managedguest.RemoteAccessHostFirewallTraversal: Firewall traversal.
  remoteAccessHostFirewallTraversal: TYPE_BOOL
    true: Enable firewall traversal.
    false: Disable firewall traversal.
  remoteAccessHostAllowRelayedConnection: TYPE_BOOL
    true: Enable the use of relay servers.
    false: Disable the use of relay servers.
  remoteAccessHostUdpPortRange: TYPE_STRING
    UDP port range. Format: minimum-maximum (e.g. 12400-12409). If unset, any port may be used.

chrome.devices.managedguest.RemoteDebuggingAllowed: Allow remote debugging.
  remoteDebuggingAllowed: TYPE_BOOL
    true: Allow use of the remote debugging.
    false: Do not allow use of the remote debugging.

chrome.devices.managedguest.RequireOnlineRevocationChecksForLocalAnchors: Require online OCSP/CRL checks for local trust anchors.
  requireOnlineRevocationChecksForLocalAnchors: TYPE_BOOL
    true: Perform revocation checking for successfully validated server certificates signed by locally installed CA certificates.
    false: Use existing online revocation-checking settings.

chrome.devices.managedguest.RestrictPrintColor: Restrict color printing mode.
  printingAllowedColorModes: TYPE_ENUM
    ANY_COLOR_MODE: Do not restrict color printing mode.
    COLOR_ONLY: Color only.
    MONOCHROME_ONLY: Black and white only.

chrome.devices.managedguest.RestrictPrintDuplexMode: Restrict page sides.
  printingAllowedDuplexModes: TYPE_ENUM
    ANY_DUPLEX_MODE: Do not restrict duplex printing mode.
    SIMPLEX_ONLY: One-sided only.
    DUPLEX_ONLY: Two-sided only.

chrome.devices.managedguest.RsaKeyUsageForLocalAnchorsEnabled: Check RSA key usage.
  rsaKeyUsageForLocalAnchorsEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable RSA key usage checking.
    TRUE: Enable RSA key usage checking.

chrome.devices.managedguest.SafeBrowsingProtectionLevel: Safe Browsing protection.
  safeBrowsingProtectionLevel: TYPE_ENUM
    USER_CHOICE: Allow the user to decide.
    NO_PROTECTION: Safe Browsing is never active.
    STANDARD_PROTECTION: Safe Browsing is active in the standard mode.
    ENHANCED_PROTECTION: Safe Browsing is active in the enhanced mode. This mode provides better security, but requires sharing more browsing information with Google.
  safeBrowsingProxiedRealTimeChecksAllowed: TYPE_BOOL
    true: Allow real time proxied checks.
    false: Don't allow real time proxied checks.
  safeBrowsingProtectionLevelCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.SafeBrowsingSurveysEnabled: Safe Browsing Surveys.
  safeBrowsingSurveysEnabled: TYPE_BOOL
    true: Allow Safe Browsing surveys to be sent to users.
    false: Disable Safe Browsing surveys.

chrome.devices.managedguest.SafeSearchRestrictedMode: SafeSearch and Restricted Mode.
  forceGoogleSafeSearch: TYPE_BOOL
    true: Always use SafeSearch for Google Search queries.
    false: Do not enforce SafeSearch for Google Search queries.
  forceYoutubeRestrictedMode: TYPE_ENUM
    OFF: Do not enforce Restricted Mode on YouTube.
    MODERATE: Enforce at least Moderate Restricted Mode on YouTube.
    STRICT: Enforce Strict Restricted Mode on YouTube.

chrome.devices.managedguest.SafeSitesFilterBehavior: SafeSites URL filter.
  safeSitesFilterBehavior: TYPE_ENUM
    SAFE_SITES_FILTER_DISABLED: Do not filter sites for adult content.
    SAFE_SITES_FILTER_ENABLED: Filter sites for adult content.

chrome.devices.managedguest.SandboxExternalProtocolBlocked: iframe navigation.
  sandboxExternalProtocolBlocked: TYPE_BOOL
    true: Do not allow navigation to external protocols inside a sandboxed iframe.
    false: Allow navigation to external protocols inside a sandboxed iframe.

chrome.devices.managedguest.ScreenBrightnessPercent: Screen brightness.
  brightnessEnabled: TYPE_BOOL
    true: Set initial screen brightness.
    false: Do not set initial screen brightness.
  brightnessAc: TYPE_INT64
    Screen brightness (ac power). Specifies the screen brightness percent when running on AC power.
  brightnessBattery: TYPE_INT64
    Screen brightness (battery power). Specifies the screen brightness percent when running on battery power.

chrome.devices.managedguest.ScreenCaptureAllowed: Screen video capture.
  screenCaptureAllowed: TYPE_BOOL
    true: Allow sites to prompt the user to share a video stream of their screen.
    false: Do not allow sites to prompt the user to share a video stream of their screen.

chrome.devices.managedguest.ScreenCaptureWithoutGestureAllowedForOrigins: Media picker without user gesture.
  screenCaptureWithoutGestureAllowedForOrigins: TYPE_LIST
    Allow screen capture without prior user gesture. Urls to allow screencapture without user gesture.

chrome.devices.managedguest.ScreenMagnifierType: Screen magnifier.
  screenMagnifierType: TYPE_ENUM
    UNSET: Allow the user to decide.
    DISABLED: Disable screen magnifier.
    FULL_SCREEN: Enable full-screen magnifier.
    DOCKED: Enable docked magnifier.

chrome.devices.managedguest.ScreensaverLockScreenEnabled: Screen saver.
  screensaverLockScreenEnabled: TYPE_BOOL
    true: Display screen saver on lock screen when idle.
    false: Don't display screen saver on lock screen when idle.
  screensaverLockScreenIdleTimeoutSeconds: TYPE_INT64
  screensaverLockScreenImageDisplayIntervalSeconds: TYPE_INT64
  screensaverLockScreenImages: TYPE_LIST
    Screen saver image URLs. Enter one URL per line. Images must be in JPG format(.jpg or .jpeg files.

chrome.devices.managedguest.Screenshot: Screenshot.
  disableScreenshots: TYPE_BOOL
    true: Do not allow users to take screenshots or video recordings.
    false: Allow users to take screenshots and video recordings.

chrome.devices.managedguest.ScrollToTextFragmentEnabled: Scroll to text fragment.
  scrollToTextFragmentEnabled: TYPE_BOOL
    true: Allow sites to scroll to specific text fragments via URL.
    false: Do not allow sites to scroll to specific text fragments via URL.

chrome.devices.managedguest.SearchSuggest: Search suggest.
  searchSuggestEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never allow users to use Search Suggest.
    TRUE: Always allow users to use Search Suggest.
  searchSuggestPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.SecurityTokenSessionSettings: Security token removal.
  securityTokenSessionBehavior: TYPE_ENUM
    IGNORE: Nothing.
    LOGOUT: Log the user out.
    LOCK: Lock the current session.
  securityTokenSessionNotificationSeconds: TYPE_INT64

chrome.devices.managedguest.SecurityTokenSessionSettingsV2: Security token removal.
  securityTokenSessionBehavior: TYPE_ENUM
    IGNORE: Nothing.
    LOGOUT: Log the user out.
    LOCK: Lock the current session.
  securityTokenSessionNotificationSeconds: TYPE_INT64

chrome.devices.managedguest.SelectToSpeakEnabled: Select to speak.
  selectToSpeakEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable select to speak.
    TRUE: Enable select to speak.

chrome.devices.managedguest.SendMouseEventsDisabledFormControlsEnabled: Disabled element MouseEvents.
  sendMouseEventsDisabledFormControlsEnabled: TYPE_BOOL
    true: Dispatch most MouseEvents from disabled control elements.
    false: Do not dispatch MouseEvents from disabled control elements.

chrome.devices.managedguest.SerialAllowUsbDevicesForUrls: Web Serial API allowed devices.
  serialAllowUsbDevicesForUrls
    webOrigin
      url: TYPE_STRING
      device: TYPE_LIST

chrome.devices.managedguest.ServiceWorkerToControlSrcdocIframeEnabled: Service worker control of srcdoc iframes.
  serviceWorkerToControlSrcdocIframeEnabled: TYPE_BOOL
    true: Allow service workers to control srcdoc iframes.
    false: Block service workers from controlling srcdoc iframes.

chrome.devices.managedguest.SessionLength: Maximum user session length.
  sessionDurationLimit: TYPE_INT64

chrome.devices.managedguest.SessionLengthV2: Maximum user session length.
  sessionDurationLimit: TYPE_INT64

chrome.devices.managedguest.SessionLocale: Session locale.
  sessionLocalesRepeatedString: TYPE_LIST
    ar: Arabic - ‫العربية‬.
    bn: Bangla - ‪বাংলা‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    zh-CN: Chinese (Simplified) - ‪简体中文‬.
    zh-TW: Chinese (Traditional) - ‪繁體中文‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-NZ: English (New Zealand).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fil: Filipino.
    fi: Finnish - ‪Suomi‬.
    fr-CA: French (Canada) - ‪Français (Canada)‬.
    fr: French (France) - ‪Français (France)‬.
    fr-CH: French (Switzerland) - ‪Français (Suisse)‬.
    de: German (Germany) - ‪Deutsch (Deutschland)‬.
    de-CH: German (Switzerland) - ‪Deutsch (Schweiz)‬.
    el: Greek - ‪Ελληνικά‬.
    gu: Gujarati - ‪ગુજરાતી‬.
    iw: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    is: Icelandic - ‪íslenska‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    ja: Japanese - ‪日本語‬.
    kn: Kannada - ‪ಕನ್ನಡ‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    ms: Malay - ‪Melayu‬.
    ml: Malayalam - ‪മലയാളം‬.
    mr: Marathi - ‪मराठी‬.
    no: Norwegian - ‪norsk‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es: Spanish (Spain) - ‪Español (España)‬.
    sv: Swedish - ‪Svenska‬.
    ta: Tamil - ‪தமிழ்‬.
    te: Telugu - ‪తెలుగు‬.
    th: Thai - ‪ไทย‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.

chrome.devices.managedguest.SetTimeoutWithoutOneMsClampEnabled: Javascript setTimeout() minimum.
  setTimeoutWithoutOneMsClampEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Javascript setTimeout() with a timeout of 0ms will clamp to 1ms.
    TRUE: Javascript setTimeout() with a timeout of 0ms will not clamp to 1ms.

chrome.devices.managedguest.SharedArrayBufferUnrestrictedAccessAllowed: SharedArrayBuffer.
  sharedArrayBufferUnrestrictedAccessAllowed: TYPE_BOOL
    true: Allow sites that are not cross-origin isolated to use SharedArrayBuffers.
    false: Prevent sites that are not cross-origin isolated from using SharedArrayBuffers.

chrome.devices.managedguest.ShelfAlign: Shelf position.
  shelfAlignmentMgs: TYPE_ENUM
    BOTTOM: Bottom.
    LEFT: Left.
    RIGHT: Right.

chrome.devices.managedguest.ShoppingListEnabled: Shopping list.
  shoppingListEnabled: TYPE_BOOL
    true: Enable the shopping list feature.
    false: Disable the shopping list feature.

chrome.devices.managedguest.ShortcutCustomizationAllowed: Customization of system shortcuts.
  shortcutCustomizationAllowed: TYPE_BOOL
    true: Allow the user to customize system shortcuts.
    false: Disallow the user to customize system shortcuts.

chrome.devices.managedguest.ShowAccessibilityOptionsInSystemTrayMenu: Accessibility options in the system tray menu.
  showAccessibilityOptionsInSystemTrayMenu: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Hide accessibility options in the system tray menu.
    TRUE: Show accessibility options in the system tray menu.

chrome.devices.managedguest.ShowCastSessionsStartedByOtherDevices: Show media controls for Google Cast sessions started by other devices on the local network.
  showCastSessionsStartedByOtherDevices: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not show media controls for Google Cast sessions started by other devices.
    TRUE: Show media controls for Google Cast sessions started by other devices.

chrome.devices.managedguest.ShowFullUrlsInAddressBar: URLs in the address bar.
  showFullUrlsInAddressBar: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Display the default URL.
    TRUE: Display the full URL.
  showFullUrlsInAddressBarCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.ShowLogoutButton: Show logout button in tray.
  showLogoutButtonInTray: TYPE_BOOL
    true: Show logout button in tray.
    false: Do not show logout button in tray.

chrome.devices.managedguest.SignedHttpExchangeEnabled: Signed HTTP Exchange (SXG) support.
  signedHttpExchangeEnabled: TYPE_BOOL
    true: Accept web content served as Signed HTTP Exchanges.
    false: Prevent Signed HTTP Exchanges from loading.

chrome.devices.managedguest.SimpleProxySettings: Proxy mode.
  simpleProxyMode: TYPE_ENUM
    USER_CONFIGURED: Allow user to configure.
    DIRECT: Never use a proxy.
    SYSTEM: Use system proxy settings.
    AUTO_DETECT: Always auto detect the proxy.
    FIXED_SERVERS: Always use the proxy specified in 'simpleProxyServerUrl'.
    PAC_SCRIPT: Always use the proxy auto-config specified in 'simpleProxyPacUrl'.
  simpleProxyServerUrl: TYPE_STRING
    Proxy server URL. Specifies the URL of a proxy server to uesr on administered devices.
  simpleProxyPacUrl: TYPE_STRING
    Proxy server auto configuration file URL. URL of the .pac file that should be used for network connections.
  proxyBypassList: TYPE_LIST
    URLs which bypass the proxy. Specifies a list of URLs that will not user the configured proxy server.

chrome.devices.managedguest.SmartScreenDimDelay: Delay screen dim on user activity.
  userActivityScreenDimDelayScale: TYPE_INT64
    Scale percent for screen dim delay on user activity. Controls the percent that the screen dim delay scales when there's user activity while the screen dims or soon after the screen turns off.
  presentationScreenDimDelayScale: TYPE_INT64
    Scale percent for screen dim delay when presenting. Controls the percent that the screen dim delay scales when the device is presenting.
  powerSmartDimEnabled: TYPE_BOOL
    true: Enable smart dim model.
    false: Disable smart dim model.

chrome.devices.managedguest.SpellcheckEnabled: Spell check.
  spellcheckEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable spell check.
    TRUE: Enable spell check.
  spellcheckLanguage: TYPE_LIST
    af: Afrikaans.
    sq: Albanian - ‪shqip‬.
    hy: Armenian - ‪հայերեն‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fo: Faroese - ‪føroyskt‬.
    fr: French - ‪Français‬.
    fr-FR: French (France) - ‪Français (France)‬.
    de: German - ‪Deutsch‬.
    de-DE: German (Germany) - ‪Deutsch (Deutschland)‬.
    el: Greek - ‪Ελληνικά‬.
    he: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    it-IT: Italian (Italy) - ‪Italiano (Italia)‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    nb: Norwegian Bokmål - ‪norsk bokmål‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt: Portuguese - ‪Português‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sh: Serbo-Croatian - ‪srpskohrvatski‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es: Spanish - ‪Español‬.
    es-AR: Spanish (Argentina) - ‪Español (Argentina)‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es-MX: Spanish (Mexico) - ‪Español (México)‬.
    es-ES: Spanish (Spain) - ‪Español (España)‬.
    es-US: Spanish (United States) - ‪Español (Estados Unidos)‬.
    sv: Swedish - ‪Svenska‬.
    tg: Tajik - ‪тоҷикӣ‬.
    ta: Tamil - ‪தமிழ்‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.
  spellcheckLanguageBlocklist: TYPE_LIST
    af: Afrikaans.
    sq: Albanian - ‪shqip‬.
    hy: Armenian - ‪հայերեն‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fo: Faroese - ‪føroyskt‬.
    fr: French - ‪Français‬.
    fr-FR: French (France) - ‪Français (France)‬.
    de: German - ‪Deutsch‬.
    de-DE: German (Germany) - ‪Deutsch (Deutschland)‬.
    el: Greek - ‪Ελληνικά‬.
    he: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    it-IT: Italian (Italy) - ‪Italiano (Italia)‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    nb: Norwegian Bokmål - ‪norsk bokmål‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt: Portuguese - ‪Português‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sh: Serbo-Croatian - ‪srpskohrvatski‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es: Spanish - ‪Español‬.
    es-AR: Spanish (Argentina) - ‪Español (Argentina)‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es-MX: Spanish (Mexico) - ‪Español (México)‬.
    es-ES: Spanish (Spain) - ‪Español (España)‬.
    es-US: Spanish (United States) - ‪Español (Estados Unidos)‬.
    sv: Swedish - ‪Svenska‬.
    tg: Tajik - ‪тоҷикӣ‬.
    ta: Tamil - ‪தமிழ்‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.

chrome.devices.managedguest.SpellCheckService: Spell check service.
  spellCheckServiceEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable the spell checking web service.
    TRUE: Enable the spell checking web service.
  spellCheckServicePolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.SpokenFeedbackEnabled: Spoken feedback.
  spokenFeedbackEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable spoken feedback.
    TRUE: Enable spoken feedback.

chrome.devices.managedguest.SslErrorOverrideAllowed: SSL error override.
  sslErrorOverrideAllowed: TYPE_BOOL
    true: Allow users to click through SSL warnings and proceed to the page.
    false: Block users from clicking through SSL warnings.

chrome.devices.managedguest.SslErrorOverrideAllowedForOrigins: SSL error override allowed domains.
  sslErrorOverrideAllowedForOrigins: TYPE_LIST
    Domains that allow clicking through SSL warnings. Enter a list of domain names.

chrome.devices.managedguest.SslVersionMin: Minimum SSL version enabled.
  sslVersionMin: TYPE_ENUM
    TL_SV_1: TLS 1.0.
    TL_SV_1_1: TLS 1.1.
    TL_SV_1_2: TLS 1.2.
    SSL_V_3: SSL3.

chrome.devices.managedguest.StandardizedBrowserZoomEnabled: Zoom Behavior.
  standardizedBrowserZoomEnabled: TYPE_BOOL
    true: Standard CSS zoom.
    false: Legacy CSS zoom.

chrome.devices.managedguest.StartupBrowserLaunch: Browser launch on startup.
  startupBrowserWindowLaunchSuppressed: TYPE_BOOL
    true: Do not launch the browser on startup.
    false: Automatically launch the browser on startup.

chrome.devices.managedguest.StartupPages: Pages to load on startup.
  restoreOnStartupUrls: TYPE_LIST
    Startup pages. Example: https://example.com.
  restoreOnStartup: TYPE_ENUM
    UNSET: Allow the user to decide.
    NEW_TAB: Open New Tab page.
    RESTORE_SESSION: Restore the last session.
    LIST_OF_URLS: Open a list of URLs.
    LIST_OF_URLS_AND_RESTORE_SESSION: Open a list of URLs and restore the last session.

chrome.devices.managedguest.StickyKeysEnabled: Sticky keys.
  stickyKeysEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable sticky keys.
    TRUE: Enable sticky keys.

chrome.devices.managedguest.StrictMimetypeCheckForWorkerScriptsEnabled: Strict MIME type checking for worker scripts.
  strictMimetypeCheckForWorkerScriptsEnabled: TYPE_BOOL
    true: Require a JavaScript MIME type for worker scripts.
    false: Use lax MIME type checking for worker scripts.

chrome.devices.managedguest.SuggestedContentEnabled: Suggested content.
  suggestedContentEnabled: TYPE_BOOL
    true: Enable suggested content.
    false: Disable suggested content.

chrome.devices.managedguest.SuggestLogoutAfterClosingLastWindow: Display the logout confirmation dialog.
  suggestLogoutAfterClosingLastWindow: TYPE_BOOL
    true: Show logout dialog when the last window is closed.
    false: Do not show logout dialog when the last window is closed.

chrome.devices.managedguest.SuppressCrossOriginIframeDialogs: Cross-origin JavaScript dialogs.
  suppressCrossOriginIframeDialogs: TYPE_BOOL
    true: Block JavaScript dialogs triggered from a cross-origin iframe.
    false: Allow JavaScript dialogs triggered from a cross-origin iframe.

chrome.devices.managedguest.SuppressUnsupportedOsWarning: Unsupported system warning.
  suppressUnsupportedOsWarning: TYPE_BOOL
    true: Suppress warnings when Chrome is running on an unsupported system.
    false: Allow Chrome to display warnings when running on an unsupported system.

chrome.devices.managedguest.SystemFeaturesDisableList: Disabled system features.
  systemFeaturesDisableList: TYPE_LIST
    camera: Camera.
    os_settings: OS settings.
    browser_settings: Browser settings.
    scanning: Scanning.
    web_store: Web Store.
    canvas: Canvas.
    crosh: Crosh.
    explore: Explore.
    gallery: Gallery.
    terminal: Terminal.
    recorder: Recorder.
    print_jobs: Print Jobs.
    key_shortcuts: Key Shortcuts.

chrome.devices.managedguest.SystemFeaturesDisableMode: Disabled system features visibility.
  systemFeaturesDisableMode: TYPE_ENUM
    BLOCKED: Show disabled app icons.
    HIDDEN: Hide app icons.

chrome.devices.managedguest.SystemShortcutBehavior: Override system shortcuts.
  systemShortcutBehavior: TYPE_ENUM
    DEFAULT: Do not override system shortcuts.
    SHOULD_IGNORE_COMMON_VDI_SHORTCUTS: Override some system shortcuts.
    SHOULD_IGNORE_COMMON_VDI_SHORTCUTS_FULLSCREEN_ONLY: Override some system shortcuts while in fullscreen.
    ALLOW_PASSTHROUGH_OF_SEARCH_BASED_SHORTCUTS: Prioritize active app over OS for Search key shortcuts.
    ALLOW_PASSTHROUGH_OF_SEARCH_BASED_SHORTCUTS_FULLSCREEN_ONLY: Prioritize active app over OS for Search key shortcuts while in fullscreen.

chrome.devices.managedguest.TabDiscardingExceptions: Exceptions to tab discarding.
  tabDiscardingExceptions: TYPE_LIST
    URL pattern exceptions to tab discarding. Specifies URL patterns where any URL matching one or more of these patterns will never be discarded by the browser.

chrome.devices.managedguest.TargetBlankImpliesNoOpener: Pop-up interactions.
  targetBlankImpliesNoOpener: TYPE_BOOL
    true: Block pop-ups opened with a target of _blank from interacting with the page that opened the pop-up.
    false: Allow pop-ups opened with a target of _blank to interact with the page that opened the pop-up.

chrome.devices.managedguest.TaskManager: Task manager.
  taskManagerEndProcessEnabled: TYPE_BOOL
    true: Allow users to end processes with the Chrome task manager.
    false: Block users from ending processes with the Chrome task manager.

chrome.devices.managedguest.ThirdPartyStoragePartitioningSettings: Third-party storage partitioning.
  defaultThirdPartyStoragePartitioningSetting: TYPE_ENUM
    ALLOW_PARTITIONING: Allow third-party storage partitioning to be enabled.
    BLOCK_PARTITIONING: Block third-party storage partitioning from being enabled.
  thirdPartyStoragePartitioningBlockedForOrigins: TYPE_LIST
    Block third-party storage partitioning for these origins. Specifies top-level origins which block third-party storage partitioning.

chrome.devices.managedguest.ThrottleNonVisibleCrossOriginIframesAllowed: Throttling of non-visible, cross-origin iframes.
  throttleNonVisibleCrossOriginIframesAllowed: TYPE_BOOL
    true: Enable throttling.
    false: Disable throttling.

chrome.devices.managedguest.TouchVirtualKeyboardEnabled: Touch on-screen keyboard.
  touchVirtualKeyboardEnabled: TYPE_ENUM
    UNSET: Enable touch on-screen keyboard in tablet mode.
    FALSE: Don't enable touch on-screen keyboard in tablet mode.
    TRUE: Enable touch on-screen keyboard in both tablet and laptop modes.

chrome.devices.managedguest.Translate: Google Translate.
  translateEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never offer translation.
    TRUE: Always offer translation.
  translatePolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.devices.managedguest.TrashEnabled: Trashed files.
  trashEnabled: TYPE_BOOL
    true: Allow files to be sent to the Trash bin in the Files app.
    false: Do not allow files to be sent to the Trash bin in the Files app.

chrome.devices.managedguest.UnifiedDesktop: Unified Desktop (BETA).
  unifiedDesktopEnabledByDefault: TYPE_BOOL
    true: Make Unified Desktop mode available to user.
    false: Do not make Unified Desktop mode available to user.

chrome.devices.managedguest.UnthrottledNestedTimeoutEnabled: JavaScript setTimeout() clamping.
  unthrottledNestedTimeoutEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: JavaScript setTimeout() will be clamped after a normal nesting threshold.
    TRUE: JavaScript setTimeout() will not be clamped as aggressively.

chrome.devices.managedguest.UrlBlocking: URL blocking.
  urlBlocklist: TYPE_LIST
    Blocked URLs. Any URL in this list will be blocked, unless it also appears in the list of exceptions specified in 'urlAllowlist'. Maximum of 1000 URLs.
  urlAllowlist: TYPE_LIST
    Blocked URL exceptions. Any URL that matches an entry in this exception list will be allowed, even if it matches an entry in the blocked URLs. Wildcards ("*") are allowed when appended to a URL, but cannot be entered alone. Maximum of 1000 URLs. .
  chromeInternalUrlsBlocked: TYPE_BOOL
    true: Block sensitive internal Chrome URLs.
    false: Do not block sensitive internal Chrome URLs.

chrome.devices.managedguest.UrlKeyedAnonymizedDataCollectionEnabled: Enable URL-keyed anonymized data collection.
  urlKeyedAnonymizedDataCollectionEnabled: TYPE_BOOL
    true: Data collection is always active.
    false: Data collection is never active.

chrome.devices.managedguest.UrlParamFilterEnabled: URL parameter filtering.
  urlParamFilterEnabled: TYPE_BOOL
    true: Allow the browser to filter URL parameters.
    false: Disallow any filtering of URL parameters.

chrome.devices.managedguest.UsbDetectorNotificationEnabled: USB device detected notification.
  usbDetectorNotificationEnabled: TYPE_BOOL
    true: Show notifications when USB devices are detected.
    false: Do not show notifications when USB devices are detected.

chrome.devices.managedguest.UseMojoVideoDecoderForPepperAllowed: Use a new decoder for hardware accelerated video decoding.
  useMojoVideoDecoderForPepperAllowed: TYPE_BOOL
    true: Allow Pepper to use the new video decoder.
    false: Force Pepper to use the legacy video decoder.

chrome.devices.managedguest.UserAgentClientHintsEnabled: User-Agent client hints.
  userAgentClientHintsEnabled: TYPE_BOOL
    true: Allow User-Agent client hints.
    false: Disable User-Agent client hints.

chrome.devices.managedguest.UserAgentReduction: User-Agent Reduction.
  userAgentReduction: TYPE_ENUM
    DEFAULT: Allow reduction controlled via Field-Trials and Origin-Trials.
    FORCE_DISABLED: Disable reduction for all origins.
    FORCE_ENABLED: Enable reduction for all origins.

chrome.devices.managedguest.UserBorealisAllowed: Steam on ChromeOS.
  userBorealisAllowed: TYPE_BOOL
    true: Allow Steam on ChromeOS.
    false: Do not allow Steam on ChromeOS.

chrome.devices.managedguest.UserFeedbackAllowed: Allow user feedback.
  userFeedbackAllowed: TYPE_BOOL
    true: Allow user feedback.
    false: Do not allow user feedback.

chrome.devices.managedguest.UserPrintersAllowed: Printer management.
  userPrintersAllowed: TYPE_BOOL
    true: Allow users to add new printers.
    false: Do not allow users to add new printers.

chrome.devices.managedguest.VideoCaptureAllowedUrls: Video input allowed URLs.
  videoCaptureAllowedUrls: TYPE_LIST
    URL patterns to allow. URLs that will be granted access to the video input device without a prompt. Prefix domain with [*.] to include subdomains.

chrome.devices.managedguest.VideoInput: Built-in camera access.
  videoCaptureAllowed: TYPE_BOOL
    true: Enable camera input for websites and apps.
    false: Disable camera input for websites and apps.

chrome.devices.managedguest.VirtualKeyboardEnabled: Accessibility on-screen keyboard.
  virtualKeyboardEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Don't enable accessibility on-screen keyboard.
    TRUE: Enable accessibility on-screen keyboard.

chrome.devices.managedguest.WaitForInitialUserActivity: Wait for initial user activity.
  waitForInitialUserActivity: TYPE_BOOL
    true: Start power management delays and session length limits after initial user activity.
    false: Start power management delays and session length limits at session start.

chrome.devices.managedguest.Wallpaper: Custom wallpaper.
  wallpaperImage
    downloadUri: TYPE_STRING

chrome.devices.managedguest.WebBluetoothAccess: Web Bluetooth API.
  defaultWebBluetoothGuardSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    BLOCK_WEB_BLUETOOTH: Do not allow sites to request access to Bluetooth devices via the Web Bluetooth API.
    ASK_WEB_BLUETOOTH: Allow sites to request access to Bluetooth devices via the Web Bluetooth API.

chrome.devices.managedguest.WebHidAllowDevicesForUrls: WebHID API allowed devices.
  webHidAllowDevicesForUrls
    webOrigin
      url: TYPE_STRING
      device: TYPE_LIST

chrome.devices.managedguest.WebRtcAllowLegacyTlsProtocols: Legacy TLS/DTLS downgrade in WebRTC.
  webRtcAllowLegacyTlsProtocols: TYPE_BOOL
    true: Enable WebRTC peer connections downgrading to obsolete versions of the TLS/DTLS (DTLS 1.0, TLS 1.0 and TLS 1.1) protocols.
    false: Disable WebRTC peer connections downgrading to obsolete versions of the TLS/DTLS (DTLS 1.0, TLS 1.0 and TLS 1.1) protocols.

chrome.devices.managedguest.WebrtcEventLogCollectionAllowed: WebRTC event log collection.
  webRtcEventLogCollectionAllowed: TYPE_BOOL
    true: Allow WebRTC event log collection.
    false: Do not allow WebRTC event log collection.

chrome.devices.managedguest.WebRtcIpHandling: WebRTC IP handling.
  webRtcIpHandling: TYPE_ENUM
    DEFAULT: WebRTC will use all available interfaces when searching for the best path.
    DEFAULT_PUBLIC_AND_PRIVATE_INTERFACES: WebRTC will only use the interface connecting to the public Internet, but may connect using private IP addresses.
    DEFAULT_PUBLIC_INTERFACE_ONLY: WebRTC will only use the interface connecting to the public Internet, and will not connect using private IP addresses.
    DISABLE_NON_PROXIED_UDP: WebRTC will use TCP on the public-facing interface, and will only use UDP if supported by a configured proxy.

chrome.devices.managedguest.WebSerialPortAccess: Web Serial API.
  defaultSerialGuardSetting: TYPE_ENUM
    BLOCK_SERIAL: Do not allow any site to request access to serial ports via the Web Serial API.
    ALLOW_ASK_SERIAL: Allow sites to ask the user to grant access to a serial ports via the Web Serial API.
    UNSET: Allow the user to decide.
  serialAskForUrls: TYPE_LIST
    Allow the Web Serial API on these sites. List of URLs that specify websites that will be allowed to ask users to grant them access to the serial ports. Prefix domain with [*.] to include subdomains.
  serialBlockedForUrls: TYPE_LIST
    Block the Web Serial API on these sites. List of URLs patterns that specify which websites can't ask users to grant them access to a serial port. Prefix domain with [*.] to include subdomains.

chrome.devices.managedguest.WebSqlAccess: Force WebSQL to be enabled.
  webSqlAccess: TYPE_BOOL
    true: Force WebSQL to be enabled.
    false: Allow WebSQL to be disabled by a Chrome flag.

chrome.devices.managedguest.WebSqlInThirdPartyContextEnabled: WebSQL in third-party context.
  webSqlInThirdPartyContextEnabled: TYPE_BOOL
    true: Allow WebSQL in third-party contexts.
    false: Do not allow WebSQL in third-party contexts.

chrome.devices.managedguest.WebSqlNonSecureContextEnabled: WebSQL in non-secure contexts.
  webSqlNonSecureContextEnabled: TYPE_BOOL
    true: Enable WebSQL in non-secure contexts.
    false: Disable WebSQL in non-secure contexts unless enabled by Chrome flag.

chrome.devices.managedguest.WebUsbAllowDevicesForUrls: WebUSB API allowed devices.
  webUsbAllowDevicesForUrls
    webApplications
      url: TYPE_STRING
      devices: TYPE_LIST

chrome.devices.managedguest.WebUsbPortAccess: Controls which websites can ask for USB access.
  defaultWebUsbGuardSetting: TYPE_ENUM
    BLOCK_WEB_USB: Do not allow any site to request access.
    ASK_WEB_USB: Allow sites to ask the user for access.
    UNSET: Allow the user to decide if sites can ask.
  webUsbAskForUrls: TYPE_LIST
    Allow these sites to ask for USB access. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  webUsbBlockedForUrls: TYPE_LIST
    Block these sites from asking for USB access. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.

chrome.devices.managedguest.WpadQuickCheckEnabled: WPAD optimization.
  wpadQuickCheckEnabled: TYPE_BOOL
    true: Enable Web Proxy Auto-Discovery (WPAD) optimization.
    false: Disable Web Proxy Auto-Discovery (WPAD) optimization.

chrome.devices.managedguest.ZstdContentEncodingEnabled: Zstd compression.
  zstdContentEncodingEnabled: TYPE_BOOL
    true: Allow zstd-compressed web content.
    false: Do not allow zstd-compressed web content.

chrome.devices.MetricsReporting: Metrics reporting.
  metricsEnabled: TYPE_BOOL
    true: Always send metrics to Google.
    false: Never send metrics to Google.

chrome.devices.MobileDataRoaming: Mobile data roaming.
  dataRoamingEnabled: TYPE_BOOL
    true: Allow mobile data roaming.
    false: Do not allow mobile data roaming.

chrome.devices.PartnerAccess: Allow EMM partners access to device management.
  chromeDeviceManagementApiEnabled: TYPE_BOOL
    true: Enable Chrome management - partner access.
    false: Disable Chrome management - partner access.
  ackNoticeForChromeDeviceManagementApiEnabledSetToTrue: TYPE_BOOL
    This field must be set to true to acknowledge the notice message associated with the field 'chrome_device_management_api_enabled' set to value 'true'. Please sse the notices listed with this policy for more information.

chrome.devices.PowerManagement: Power management.
  loginScreenPowerManagement: TYPE_BOOL
    true: Allow device to sleep/shut down when idle on the sign-in screen.
    false: Do not allow device to sleep/shut down when idle on the sign-in screen.

chrome.devices.PowerPeakShift: Peak shift power management.
  powerPeakShiftEnabled: TYPE_BOOL
    true
    false
  powerPeakShiftBatteryThreshold: TYPE_INT64
    Sets the battery threshold for power peak shift.
  powerPeakShiftTimesOfDay
    dailyPeakShifts
      key: TYPE_STRING
      value
        startTime: TYPE_INT32
        endTime: TYPE_INT32
        chargeTime: TYPE_INT32

chrome.devices.QuirksDownloadEnabled: Hardware profiles.
  deviceQuirksDownloadEnabled: TYPE_BOOL
    true: Allow hardware profiles to be downloaded from Google servers.
    false: Disable hardware profile downloads from Google servers.

chrome.devices.RebootOnShutdown: Allow shutdown.
  rebootOnShutdown: TYPE_BOOL
    true: Only allow users to turn off the device using the physical power button.
    false: Allow users to turn off the device using either the shut down icon or the physical power button.

chrome.devices.RestrictedManagedGuestSessionExtensionCleanupExemptList: Shared apps & extensions.
  restrictedManagedGuestSessionExtensionCleanupExemptList: TYPE_LIST
    Extension IDs. Enter a list of extension IDs. Each extension ID must be exactly 32 characters.

chrome.devices.ScheduledRebootDuration: Reboot after uptime limit.
  uptimeLimitDuration: TYPE_INT64

chrome.devices.ScheduledRebootDurationV2: Reboot after uptime limit.
  uptimeLimitDuration: TYPE_INT64

chrome.devices.ShowLowDiskSpaceNotification: Low disk space notification.
  showLowDiskSpaceNotification: TYPE_BOOL
    true: Show notification when disk space is low.
    false: Do not show notification when disk space is low.

chrome.devices.SignInKeyboard: Login screen keyboard.
  loginScreenKeyboardSelections
    selections
      keyboardIds: TYPE_LIST

chrome.devices.SignInLanguage: Sign-in language.
  signInLanguageString: TYPE_STRING
    ar: Arabic - ‫العربية‬.
    bn: Bangla - ‪বাংলা‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    zh-CN: Chinese (Simplified) - ‪简体中文‬.
    zh-TW: Chinese (Traditional) - ‪繁體中文‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-NZ: English (New Zealand).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fil: Filipino.
    fi: Finnish - ‪Suomi‬.
    fr-CA: French (Canada) - ‪Français (Canada)‬.
    fr: French (France) - ‪Français (France)‬.
    fr-CH: French (Switzerland) - ‪Français (Suisse)‬.
    de: German (Germany) - ‪Deutsch (Deutschland)‬.
    de-CH: German (Switzerland) - ‪Deutsch (Schweiz)‬.
    el: Greek - ‪Ελληνικά‬.
    gu: Gujarati - ‪ગુજરાતી‬.
    iw: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    is: Icelandic - ‪íslenska‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    ja: Japanese - ‪日本語‬.
    kn: Kannada - ‪ಕನ್ನಡ‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    ms: Malay - ‪Melayu‬.
    ml: Malayalam - ‪മലയാളം‬.
    mr: Marathi - ‪मराठी‬.
    no: Norwegian - ‪norsk‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es: Spanish (Spain) - ‪Español (España)‬.
    sv: Swedish - ‪Svenska‬.
    ta: Tamil - ‪தமிழ்‬.
    te: Telugu - ‪తెలుగు‬.
    th: Thai - ‪ไทย‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.
    : Use the language of the last user session.

chrome.devices.SignInRestriction: Sign-in restriction.
  deviceAllowNewUsers: TYPE_ENUM
    RESTRICTED_LIST: Restrict sign-in to a list of users.
    ANY_USER: Allow any user to sign in.
    NO_USERS: Do not allow any user to sign in.
  userAllowlist: TYPE_LIST
    Allowed users. Enter a list of usernames who can sign in to the device. You can also allow all email addresses in a domain with the wildcard symbol (e.g. *@example.com).

chrome.devices.SignInRestrictionsOffHours: Device off hours.
  deviceOffHours
    timezone: TYPE_STRING
    timeWindows
      start
        dayOfWeek: TYPE_ENUM
          MONDAY:
          TUESDAY:
          WEDNESDAY:
          THURSDAY:
          FRIDAY:
          SATURDAY:
          SUNDAY:
        hours: TYPE_INT32
        minutes: TYPE_INT32
      end
        dayOfWeek: TYPE_ENUM
          MONDAY:
          TUESDAY:
          WEDNESDAY:
          THURSDAY:
          FRIDAY:
          SATURDAY:
          SUNDAY:
        hours: TYPE_INT32
        minutes: TYPE_INT32

chrome.devices.SignInWallpaperImage: Device wallpaper image.
  deviceWallpaperImage
    downloadUri: TYPE_STRING

chrome.devices.SsoCameraPermissions: Single sign-on camera permissions.
  loginVideoCaptureAllowedUrls: TYPE_LIST
    Allowed single sign-on camera permissions. By enabling this policy, you are granting third parties access to your users' cameras on your users' behalf. Please ensure you read the help center articles for more clarifications around single sign-on and camera permissions.

chrome.devices.SsoCookieBehavior: Single sign-on cookie behavior.
  transferSamlCookies: TYPE_BOOL
    true: Enable transfer of SAML SSO Cookies into user session during sign-in.
    false: Disable transfer of SAML SSO Cookies into user session during sign-in.

chrome.devices.SsoIdpRedirection: Single sign-on IdP redirection.
  loginAuthenticationBehavior: TYPE_ENUM
    GAIA: Take users to the default Google sign-in screen.
    SAML_INTERSTITIAL: Allow users to go directly to SAML SSO IdP page.

chrome.devices.SystemProxySettings: Authenticated Proxy Traffic.
  systemProxyEnabled: TYPE_BOOL
    true: Allow system traffic to go through a proxy with authentication.
    false: Block system traffic from going through a proxy with authentication.
  systemServicesUsername: TYPE_STRING
    Username. Sets the username for authenticating system services to the remote proxy.
  systemServicesPassword: TYPE_STRING
    Password. You can choose to provide service account credentials (username and password). These credentials will only be used for system traffic. Browser traffic will still require the user to authenticate to the proxy with their own credentials.

chrome.devices.SystemUseTwentyFourHourClock: System clock format.
  systemUseTwentyFourHourClock: TYPE_ENUM
    UNSET: Automatic, based on current language.
    FALSE: 12 hour clock format.
    TRUE: 24 hour clock format.

chrome.devices.ThrottleDeviceBandwidth: Throttle device bandwidth.
  networkThrottlingEnabled: TYPE_BOOL
    true: Enable network throttling.
    false: Disable network throttling.
  downloadRateKbits: TYPE_INT64
    Download rate (kbits). Sets the maximum download rate if network bandwidth throttling is enabled on a ChromeOS device.
  uploadRateKbits: TYPE_INT64
    Upload rate (kbits). Sets the maximum upload rate if network bandwidth throttling is enabled on a ChromeOS device.

chrome.devices.Timezone: Timezone.
  systemTimezone: TYPE_STRING
  timezoneDetectionType: TYPE_ENUM
    USERS_DECIDE: Let users decide.
    DISABLED: Never auto-detect timezone.
    IP_ONLY: Always use coarse timezone detection.
    SEND_WIFI_ACCESS_POINTS: Always send wifi access points to server while resolving timezone.
    SEND_ALL_LOCATION_INFO: Send all location information.

chrome.devices.TpmFirmwareUpdate: TPM firmware update.
  tpmFirmwareUpdateEnabled: TYPE_BOOL
    true: Allow users to perform TPM firmware update.
    false: Block users from performing TPM firmware update.
  allowUserInitiatedPreserveDeviceState: TYPE_BOOL
    true: Allow users to perform TPM firmware update that preserves device-wide state.
    false: Block users from performing TPM firmware update that preserves device-wide state.
  autoUpdateMode: TYPE_ENUM
    NEVER: Never.
    USER_ACKNOWLEDGMENT: User acknowledgment.
    WITHOUT_ACKNOWLEDGMENT: Without user acknowledgment.
    ENROLLMENT: Enrollment.

chrome.devices.UnaffiliatedArcAllowed: Android apps for unaffiliated users.
  unaffiliatedArcAllowed: TYPE_BOOL
    true: Allow unaffiliated users to use Android apps.
    false: Do not allow unaffiliated users to use Android apps.

chrome.devices.UsbDetachableAllowlist: USB access.
  usbDetachableAllowlist: TYPE_LIST
    Allowed USB devices. A list of USB devices that Chrome apps may access via the chrome.usb API. To identify a specific hardware, enter colon separated hexadecimal pairs of USB Vendor Identifier and Product Identifier. .

chrome.devices.UsbPowerShare: USB Powershare.
  usbPowerShareEnabled: TYPE_BOOL
    true: Enable USB Powershare.
    false: Disable USB Powershare.

chrome.devices.Variations: Variations.
  deviceVariationsEnabled: TYPE_ENUM
    ENABLED: Enable Chrome variations.
    CRITICAL_FIXES_ONLY: Enable variations for critical fixes only.
    DISABLED: Disable variations.

chrome.devices.VirtualMachineAndroidAdbSideloadingAllowed: Android apps from untrusted sources.
  virtualMachinesAndroidAdbSideloadingAllowed: TYPE_ENUM
    DISALLOW: Prevent users of this device from using ADB sideloading.
    DISALLOW_WITH_POWERWASH: Prevent users of this device from using ADB sideloading and force a device powerwash if sideloading was enabled before.
    ALLOW_FOR_AFFILIATED_USERS: Allow affiliated users of this device to use ADB sideloading.

chrome.devices.VirtualMachinesAllowedUnaffiliatedUser: Linux virtual machines for unaffiliated users.
  virtualMachinesAllowedForUnaffiliatedUser: TYPE_BOOL
    true: Allow usage for virtual machines needed to support Linux apps for unaffiliated users.
    false: Block usage for virtual machines needed to support Linux apps for unaffiliated users.

chrome.devices.WilcoScheduledUpdate: Scheduled updates.
  wilcoScheduledUpdateEnabled: TYPE_BOOL
    true
    false
  wilcoScheduledUpdateTimeOfDay: TYPE_INT64
    0: 12:00 AM.
    15: 12:15 AM.
    30: 12:30 AM.
    45: 12:45 AM.
    60: 1:00 AM.
    75: 1:15 AM.
    90: 1:30 AM.
    105: 1:45 AM.
    120: 2:00 AM.
    135: 2:15 AM.
    150: 2:30 AM.
    165: 2:45 AM.
    180: 3:00 AM.
    195: 3:15 AM.
    210: 3:30 AM.
    225: 3:45 AM.
    240: 4:00 AM.
    255: 4:15 AM.
    270: 4:30 AM.
    285: 4:45 AM.
    300: 5:00 AM.
    315: 5:15 AM.
    330: 5:30 AM.
    345: 5:45 AM.
    360: 6:00 AM.
    375: 6:15 AM.
    390: 6:30 AM.
    405: 6:45 AM.
    420: 7:00 AM.
    435: 7:15 AM.
    450: 7:30 AM.
    465: 7:45 AM.
    480: 8:00 AM.
    495: 8:15 AM.
    510: 8:30 AM.
    525: 8:45 AM.
    540: 9:00 AM.
    555: 9:15 AM.
    570: 9:30 AM.
    585: 9:45 AM.
    600: 10:00 AM.
    615: 10:15 AM.
    630: 10:30 AM.
    645: 10:45 AM.
    660: 11:00 AM.
    675: 11:15 AM.
    690: 11:30 AM.
    705: 11:45 AM.
    720: 12:00 PM.
    735: 12:15 PM.
    750: 12:30 PM.
    765: 12:45 PM.
    780: 1:00 PM.
    795: 1:15 PM.
    810: 1:30 PM.
    825: 1:45 PM.
    840: 2:00 PM.
    855: 2:15 PM.
    870: 2:30 PM.
    885: 2:45 PM.
    900: 3:00 PM.
    915: 3:15 PM.
    930: 3:30 PM.
    945: 3:45 PM.
    960: 4:00 PM.
    975: 4:15 PM.
    990: 4:30 PM.
    1005: 4:45 PM.
    1020: 5:00 PM.
    1035: 5:15 PM.
    1050: 5:30 PM.
    1065: 5:45 PM.
    1080: 6:00 PM.
    1095: 6:15 PM.
    1110: 6:30 PM.
    1125: 6:45 PM.
    1140: 7:00 PM.
    1155: 7:15 PM.
    1170: 7:30 PM.
    1185: 7:45 PM.
    1200: 8:00 PM.
    1215: 8:15 PM.
    1230: 8:30 PM.
    1245: 8:45 PM.
    1260: 9:00 PM.
    1275: 9:15 PM.
    1290: 9:30 PM.
    1305: 9:45 PM.
    1320: 10:00 PM.
    1335: 10:15 PM.
    1350: 10:30 PM.
    1365: 10:45 PM.
    1380: 11:00 PM.
    1395: 11:15 PM.
    1410: 11:30 PM.
    1425: 11:45 PM.
  wilcoScheduledUpdateFrequency: TYPE_ENUM
    DAILY:
    WEEKLY:
    MONTHLY:
  wilcoScheduledUpdateDayOfWeek: TYPE_ENUM
    MONDAY:
    TUESDAY:
    WEDNESDAY:
    THURSDAY:
    FRIDAY:
    SATURDAY:
    SUNDAY:
  wilcoScheduledUpdateDayOfMonth: TYPE_INT64
    1: The 1st day of the month.
    2: The 2nd day of the month.
    3: The 3rd day of the month.
    4: The 4th day of the month.
    5: The 5th day of the month.
    6: The 6th day of the month.
    7: The 7th day of the month.
    8: The 8th day of the month.
    9: The 9th day of the month.
    10: The 10th day of the month.
    11: The 11th day of the month.
    12: The 12th day of the month.
    13: The 13th day of the month.
    14: The 14th day of the month.
    15: The 15th day of the month.
    16: The 16th day of the month.
    17: The 17th day of the month.
    18: The 18th day of the month.
    19: The 19th day of the month.
    20: The 20th day of the month.
    21: The 21st day of the month.
    22: The 22nd day of the month.
    23: The 23rd day of the month.
    24: The 24th day of the month.
    25: The 25th day of the month.
    26: The 26th day of the month.
    27: The 27th day of the month.
    28: The 28th day of the month.
    29: The 29th day of the month.
    30: The 30th day of the month.
    31: The 31st day of the month.

chrome.devices.WipeUserData: Allows admins to make managed ChromeOS devices wipe user data after sign-out.
  ephemeralUsersEnabled: TYPE_BOOL
    true: Erase all local user data.
    false: Do not erase local user data.

chrome.networks.cellular.AllowForChromeDevices: Allow chrome devices to use this network.
  allowForChromeDevices: TYPE_BOOL
    true: Allow chrome devices to use this network.
    false: Do not allow chrome devices to use this network.

chrome.networks.cellular.Details: Cellular network configuration details.
  details
    name: TYPE_STRING
    smdpAddress: TYPE_STRING
    smdsAddress: TYPE_STRING

chrome.networks.cellular.DetailsV2: Cellular network configuration details.
  details
    name: TYPE_STRING
    smdpAddress: TYPE_STRING
    smdsAddress: TYPE_STRING

chrome.networks.certificates.AllowForChromeDevices: Allow chrome users to use this certificate.
  allowForChromeDevices: TYPE_BOOL
    true: Allow chrome devices to use this certificate.
    false: Do not allow chrome devices to use this certificate.

chrome.networks.certificates.AllowForChromeImprivata: Allow the Imprivata app to use this certificate.
  allowForChromeImprivata: TYPE_BOOL
    true: Allow the Imprivata app to use this certificate.
    false: Do not allow the Imprivata app to use this certificate.

chrome.networks.ethernet.AllowForChromeDevices: Allow chrome devices to use this network.
  allowForChromeDevices: TYPE_BOOL
    true: Allow chrome devices to use this network.
    false: Do not allow chrome devices to use this network.

chrome.networks.ethernet.AllowForChromeUsers: Allow this network to be used by chrome users.
  allowForChromeUsers: TYPE_BOOL
    true: Allow chrome users to use this network.
    false: Do not allow chrome users to use this network.

chrome.networks.ethernet.Details: Ethernet network configuration details.
  details
    name: TYPE_STRING
    authentication: TYPE_STRING
    eap
      outerProtocol: TYPE_STRING
      innerProtocol: TYPE_STRING
      useSystemCas: TYPE_BOOL
      serverCaRef: TYPE_STRING
      clientCertPattern
        enrollmentUrls: TYPE_LIST
        issuer
          commonName: TYPE_STRING
          locality: TYPE_STRING
          organization: TYPE_STRING
          organizationalUnit: TYPE_STRING
        subject
          commonName: TYPE_STRING
          locality: TYPE_STRING
          organization: TYPE_STRING
          organizationalUnit: TYPE_STRING
      identity: TYPE_STRING
      password: TYPE_STRING
      anonymousIdentity: TYPE_STRING
      tlsVersionMax: TYPE_STRING
      domainSuffixMatch: TYPE_LIST
    proxySettings
      type: TYPE_STRING
      manualConfiguration
        httpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        secureHttpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        ftpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        socks
          host: TYPE_STRING
          port: TYPE_INT32
      excludeDomains: TYPE_LIST
      automaticProxyConfigurationUrl: TYPE_STRING
    allowIpConfiguration: TYPE_BOOL
    allowNameServersConfiguration: TYPE_BOOL
    nameServerSelection: TYPE_ENUM
      AUTOMATIC:
      GOOGLE:
      CUSTOM:
    customNameServers: TYPE_LIST

chrome.networks.globalsettings.AllowedNetworkInterfaces: Allow users to connect to network interfaces by type.
  allowedNetworkInterfaces
    wifi: TYPE_BOOL
    ethernet: TYPE_BOOL
    cellular: TYPE_BOOL
    wimax: TYPE_BOOL
    vpn: TYPE_BOOL

chrome.networks.globalsettings.AllowedNetworkInterfacesV2: Allow users to connect to network interfaces by type.
  allowedNetworkInterfaces
    wifi: TYPE_BOOL
    ethernet: TYPE_BOOL
    cellular: TYPE_BOOL
    vpn: TYPE_BOOL

chrome.networks.globalsettings.AutoConnect: Restrict users to only auto-connect to managed networks.
  autoConnectRestricted: TYPE_BOOL
    true: Restrict users to only auto-connect to managed networks.
    false: Allow all networks to auto-connect.

chrome.networks.globalsettings.BlockedSsids: Restrict users to connect to WiFi SSIDs in the list.
  blockedSsids: TYPE_LIST
    Sets WiFi SSIDs that should be blocked.

chrome.networks.globalsettings.CellularNetworks: Restrict users to only connect to cellular networks configured for this organizational unit.
  cellularNetworksRestricted: TYPE_BOOL
    true: Restrict users to only connect to cellular networks configured for this organizational unit.
    false: Allow all cellular networks to connect.

chrome.networks.globalsettings.RestrictWifiNetworks: Restrict users to only connect to the Wi-Fi networks configured for this organizational unit.
  restrictWifiNetworks: TYPE_ENUM
    NO_RESTRICTION: Allow users to connect to networks not configured in this organizational unit.
    ONLY_POLICY_NETWORKS: Restrict users to only connect to Wi-Fi networks configured for this organizational unit.
    ONLY_POLICY_NETWORKS_IF_AVAILABLE: Restrict users to only connect to Wi-Fi networks configured for this organizational unit, but only if such networks are in range of the device.

chrome.networks.globalsettings.SimLock: Restrict users from PIN locking SIM(s) on the device.
  simLockRestricted: TYPE_BOOL
    true: Restrict users from PIN locking SIM(s) on the device.
    false: Allow users to PIN lock SIM(s).

chrome.networks.vpn.AllowForChromeDevices: Allow chrome devices to use this network.
  allowForChromeDevices: TYPE_BOOL
    true: Allow chrome devices to use this network.
    false: Do not allow chrome devices to use this network.

chrome.networks.vpn.AllowForChromeUsers: Allow this network to be used by chrome users.
  allowForChromeUsers: TYPE_BOOL
    true: Allow chrome users to use this network.
    false: Do not allow chrome users to use this network.

chrome.networks.vpn.Details: Vpn network configuration details.
  details
    name: TYPE_STRING
    remoteHost: TYPE_STRING
    automaticallyConnect: TYPE_BOOL
    vpnType: TYPE_STRING
    layerTwoTunnelingProtocol
      username: TYPE_STRING
      password: TYPE_STRING
      saveCredentials: TYPE_BOOL
    psk: TYPE_STRING
    openVpn
      remoteHostPort: TYPE_INT32
      protocol: TYPE_STRING
      authenticationAlgorithm: TYPE_STRING
      encryptionAlgorithm: TYPE_STRING
      compressionAlgorithm: TYPE_STRING
      tlsAuthenticationKey: TYPE_STRING
      keyDirection: TYPE_STRING
      serverVpnAuthority: TYPE_STRING
      clientCertPattern
        enrollmentUrls: TYPE_LIST
        issuer
          commonName: TYPE_STRING
          locality: TYPE_STRING
          organization: TYPE_STRING
          organizationalUnit: TYPE_STRING
        subject
          commonName: TYPE_STRING
          locality: TYPE_STRING
          organization: TYPE_STRING
          organizationalUnit: TYPE_STRING
      username: TYPE_STRING
      password: TYPE_STRING
      saveCredentials: TYPE_BOOL
    proxySettings
      type: TYPE_STRING
      manualConfiguration
        httpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        secureHttpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        ftpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        socks
          host: TYPE_STRING
          port: TYPE_INT32
      excludeDomains: TYPE_LIST
      automaticProxyConfigurationUrl: TYPE_STRING
    allowIpConfiguration: TYPE_BOOL
    allowNameServersConfiguration: TYPE_BOOL
    nameServerSelection: TYPE_ENUM
      AUTOMATIC:
      GOOGLE:
      CUSTOM:
    customNameServers: TYPE_LIST

chrome.networks.wifi.AllowForChromeDevices: Allow managed devices to use this network.
  allowForChromeDevices: TYPE_BOOL
    true: Allow chrome devices to use this network.
    false: Do not allow chrome devices to use this network.

chrome.networks.wifi.AllowForChromeUsers: Allow this network to be used by chrome users.
  allowForChromeUsers: TYPE_BOOL
    true: Allow chrome users to use this network.
    false: Do not allow chrome users to use this network.

chrome.networks.wifi.Details: Wifi network configuration details.
  details
    name: TYPE_STRING
    ssid: TYPE_STRING
    hiddenSsid: TYPE_BOOL
    automaticallyConnect: TYPE_BOOL
    security: TYPE_STRING
    passphrase: TYPE_STRING
    eap
      outerProtocol: TYPE_STRING
      innerProtocol: TYPE_STRING
      useSystemCas: TYPE_BOOL
      serverCaRef: TYPE_STRING
      clientCertRef: TYPE_STRING
      clientCertPattern
        enrollmentUrls: TYPE_LIST
        issuer
          commonName: TYPE_STRING
          locality: TYPE_STRING
          organization: TYPE_STRING
          organizationalUnit: TYPE_STRING
        subject
          commonName: TYPE_STRING
          locality: TYPE_STRING
          organization: TYPE_STRING
          organizationalUnit: TYPE_STRING
      identity: TYPE_STRING
      password: TYPE_STRING
      anonymousIdentity: TYPE_STRING
      tlsVersionMax: TYPE_STRING
      domainSuffixMatch: TYPE_LIST
    proxySettings
      type: TYPE_STRING
      manualConfiguration
        httpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        secureHttpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        ftpProxy
          host: TYPE_STRING
          port: TYPE_INT32
        socks
          host: TYPE_STRING
          port: TYPE_INT32
      excludeDomains: TYPE_LIST
      automaticProxyConfigurationUrl: TYPE_STRING
    allowIpConfiguration: TYPE_BOOL
    allowNameServersConfiguration: TYPE_BOOL
    nameServerSelection: TYPE_ENUM
      AUTOMATIC:
      GOOGLE:
      CUSTOM:
    customNameServers: TYPE_LIST

chrome.printers.AllowForDevices: Allows a printer for devices in a given organization.
  allowForDevices: TYPE_BOOL
    Controls whether a printer is allowed for devices in a given organization.

chrome.printers.AllowForManagedGuest: Allows a printer for Managed Guest in a given organization.
  allowForManagedGuest: TYPE_BOOL
    Controls whether a printer is allowed for Managed Guest in a given organization.

chrome.printers.AllowForUsers: Allows a printer for users in a given organization.
  allowForUsers: TYPE_BOOL
    Controls whether a printer is allowed for users in a given organization.

chrome.printservers.AllowForDevices: Allows a print server for devices in a given organization.
  allowForDevices: TYPE_BOOL
    Controls whether a print server is allowed for devices in a given organization.

chrome.printservers.AllowForManagedGuest: Allows a print server for Managed Guest in a given organization.
  allowForManagedGuest: TYPE_BOOL
    Controls whether a print server is allowed for Managed Guest in a given organization.

chrome.printservers.AllowForUsers: Allows a print server for users in a given organization.
  allowForUsers: TYPE_BOOL
    Controls whether a print server is allowed for users in a given organization.

chrome.users.AbusiveExperienceInterventionEnforce: Abusive Experience Intervention.
  abusiveExperienceInterventionEnforce: TYPE_BOOL
    true: Prevent sites with abusive experiences from opening new windows or tabs.
    false: Allow sites with abusive experiences to open new windows or tabs.

chrome.users.AccessCodeCast: Cast moderator.
  accessCodeCastEnabled: TYPE_BOOL
    true: Enable cast moderator.
    false: Disable cast moderator.
  accessCodeCastDeviceDuration: TYPE_ENUM
    INSTANT: Remove immediately.
    ONE_HOUR: 1 hour.
    ONE_DAY: 1 day.
    ONE_MONTH: 1 month.
    ONE_YEAR: 1 year.

chrome.users.AccessControlAllowMethodsInCorsPreflightSpecConformant: CORS Access-Control-Allow-Methods conformance.
  accessControlAllowMethodsInCorsPreflightSpecConformant: TYPE_BOOL
    true: Do not uppercase request methods except for DELETE/GET/HEAD/OPTIONS/POST/PUT.
    false: Always uppercase request methods.

chrome.users.AccessibilityImageLabelsEnabled: Image descriptions.
  accessibilityImageLabelsEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not use Google services to provide automatic image descriptions.
    TRUE: Use an anonymous Google service to provide automatic descriptions for unlabeled images.

chrome.users.AccessibilityPerformanceFilteringAllowed: Accessibility Performance Filtering.
  accessibilityPerformanceFilteringAllowed: TYPE_BOOL
    true: Allow Accessibility Performance Filtering to be used.
    false: Disallow Accessibility Performance Filtering to be used.

chrome.users.AccessibilityShortcutsEnabled: Accessibility shortcuts.
  accessibilityShortcutsEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable accessibility shortcuts.
    TRUE: Enable accessibility shortcuts.

chrome.users.AdditionalDnsQueryTypesEnabled: DNS queries for additional DNS record types.
  additionalDnsQueryTypesEnabled: TYPE_BOOL
    true: Allow additional DNS query types.
    false: Prevent additional DNS query types.

chrome.users.AdsSettingForIntrusiveAdsSites: Sites with intrusive ads.
  adsSettingForIntrusiveAdsSites: TYPE_ENUM
    ALLOW_ADS: Allow ads on all sites.
    BLOCK_ADS: Block ads on sites with intrusive ads.

chrome.users.AdvancedProtectionAllowed: Advanced Protection program.
  advancedProtectionAllowed: TYPE_BOOL
    true: Users enrolled in the Advanced Protection program will receive extra protections.
    false: Users enrolled in the Advanced Protection program will only receive standard consumer protections.

chrome.users.AllowBackForwardCacheForCacheControlNoStorePageEnabled: No-store header back/forward cache.
  allowBackForwardCacheForCacheControlNoStorePageEnabled: TYPE_BOOL
    true: Allow pages with CCNS header to be stored in back/forward cache.
    false: Disallow pages with CCNS header from being stored in back/forward cache.

chrome.users.AllowChromeDataInBackups: Backup of Google Chrome data.
  allowChromeDataInBackups: TYPE_BOOL
    true: Allow Google Chrome data to be included in backups.
    false: Prevent Google Chrome data from being included in backups.

chrome.users.AllowDinosaurEasterEgg: Dinosaur game.
  allowDinosaurEasterEgg: TYPE_ENUM
    UNSET: Allow users to play the dinosaur game when the device is offline on Chrome browser, but not on enrolled ChromeOS devices.
    FALSE: Do not allow users to play the dinosaur game when the device is offline.
    TRUE: Allow users to play the dinosaur game when the device is offline.

chrome.users.AllowedInputMethods: Allowed input methods.
  allowedInputMethods: TYPE_LIST
    xkb:jp::jpn: Alphanumeric with Japanese keyboard.
    am-t-i0-und: Amharic Transliteration.
    vkd_ar: Arabic.
    ar-t-i0-und: Arabic Transliteration.
    xkb:am:phonetic:arm: Armenian.
    vkd_bn_phone: Bangla Phonetic.
    bn-t-i0-und: Bangla Transliteration.
    xkb:by::bel: Belarusian.
    _comp_ime_jddehjeebkoimngcbdkaahpobgicbffpbraille: Braille Keyboard.
    xkb:bg::bul: Bulgarian.
    xkb:bg:phonetic:bul: Bulgarian with Phonetic keyboard.
    vkd_my: Burmese/Myanmar.
    vkd_my_myansan: Burmese/Myanmar with Myansan keyboard.
    yue-hant-t-i0-und: Cantonese.
    xkb:es:cat:cat: Catalan.
    zh-hant-t-i0-pinyin: Chinese (Traditional) Pinyin.
    zh-hant-t-i0-array-1992: Chinese Array.
    zh-hant-t-i0-cangjie-1987: Chinese Cangjie.
    zh-hant-t-i0-dayi-1988: Chinese Dayi.
    zh-t-i0-pinyin: Chinese Pinyin.
    zh-hant-t-i0-cangjie-1987-x-m0-simplified: Chinese Quick.
    zh-t-i0-wubi-1986: Chinese Wubi.
    zh-hant-t-i0-und: Chinese Zhuyin.
    xkb:hr::scr: Croatian.
    xkb:cz::cze: Czech.
    xkb:cz:qwerty:cze: Czech with Qwerty keyboard.
    xkb:dk::dan: Danish.
    vkd_deva_phone: Devanagari keyboard (Phonetic).
    xkb:be::nld: Dutch (Belgium).
    xkb:us:intl:nld: Dutch (Netherlands).
    xkb:us:intl_pc:nld: Dutch (Netherlands) with US International PC keyboard.
    xkb:ca:eng:eng: English (Canada).
    xkb:in::eng: English (India).
    xkb:pk::eng: English (Pakistan).
    xkb:za:gb:eng: English (South Africa).
    xkb:gb:extd:eng: English (UK).
    xkb:gb:dvorak:eng: English (UK) with Dvorak keyboard.
    xkb:us::eng: English (US).
    xkb:us:colemak:eng: English (US) with Colemak keyboard.
    xkb:us:dvorak:eng: English (US) with Dvorak keyboard.
    xkb:us:altgr-intl:eng: English (US) with Extended keyboard.
    xkb:us:intl_pc:eng: English (US) with International PC keyboard.
    xkb:us:intl:eng: English (US) with International keyboard.
    xkb:us:dvp:eng: English (US) with Programmer Dvorak keyboard.
    xkb:us:workman-intl:eng: English (US) with Workman International keyboard.
    xkb:us:workman:eng: English (US) with Workman keyboard.
    xkb:ee::est: Estonian.
    vkd_ethi: Ethiopic keyboard.
    xkb:fo::fao: Faroese.
    xkb:us::fil: Filipino.
    xkb:fi::fin: Finnish.
    xkb:be::fra: French (Belgium).
    xkb:ca::fra: French (Canada).
    xkb:ca:multix:fra: French (Canada) with Multilingual keyboard.
    xkb:fr::fra: French (France).
    xkb:fr:bepo:fra: French (France) with Bépo keyboard.
    xkb:ch:fr:fra: French (Switzerland).
    xkb:ge::geo: Georgian.
    xkb:be::ger: German (Belgium).
    xkb:de::ger: German (Germany).
    xkb:de:neo:ger: German (Germany) with Neo 2 keyboard.
    xkb:ch::ger: German (Switzerland).
    xkb:gr::gre: Greek.
    el-t-i0-und: Greek Transliteration.
    vkd_gu_phone: Gujarati Phonetic.
    gu-t-i0-und: Gujarati Transliteration.
    xkb:il::heb: Hebrew.
    he-t-i0-und: Hebrew Transliteration.
    hi-t-i0-und: Hindi.
    vkd_hi_inscript: Hindi with InScript keyboard.
    xkb:hu::hun: Hungarian.
    xkb:hu:qwerty:hun: Hungarian with Qwerty keyboard.
    xkb:is::ice: Icelandic.
    xkb:us::ind: Indonesian.
    xkb:ie::ga: Irish.
    xkb:it::ita: Italian.
    nacl_mozc_jp: Japanese.
    nacl_mozc_us: Japanese with US keyboard.
    vkd_kn_phone: Kannada Phonetic.
    kn-t-i0-und: Kannada Transliteration.
    xkb:kz::kaz: Kazakh.
    vkd_km: Khmer.
    ko-t-i0-und: Korean.
    vkd_lo: Lao.
    xkb:lv:apostrophe:lav: Latvian.
    xkb:lt::lit: Lithuanian.
    xkb:mk::mkd: Macedonian.
    xkb:us::msa: Malay.
    vkd_ml_phone: Malayalam Phonetic.
    ml-t-i0-und: Malayalam Transliteration.
    xkb:mt::mlt: Maltese.
    mr-t-i0-und: Marathi.
    xkb:mn::mon: Mongolian.
    ne-t-i0-und: Nepali Transliteration.
    vkd_ne_inscript: Nepali with InScript keyboard.
    vkd_ne_phone: Nepali with Phonetic keyboard.
    xkb:no::nob: Norwegian.
    or-t-i0-und: Odia.
    vkd_fa: Persian.
    fa-t-i0-und: Persian Transliteration.
    xkb:pl::pol: Polish.
    xkb:br::por: Portuguese (Brazil).
    xkb:pt::por: Portuguese (Portugal).
    xkb:us:intl_pc:por: Portuguese with US International PC keyboard.
    xkb:us:intl:por: Portuguese with US International keyboard.
    pa-t-i0-und: Punjabi.
    xkb:ro::rum: Romanian.
    xkb:ro:std:rum: Romanian with Standard keyboard.
    xkb:ru::rus: Russian.
    vkd_ru_phone_aatseel: Russian with Phonetic AATSEEL keyboard.
    vkd_ru_phone_yazhert: Russian with Phonetic YaZHert keyboard.
    xkb:ru:phonetic:rus: Russian with Phonetic keyboard.
    sa-t-i0-und: Sanskrit.
    xkb:rs::srp: Serbian.
    sr-t-i0-und: Serbian Transliteration.
    vkd_si: Sinhala.
    xkb:sk::slo: Slovak.
    xkb:si::slv: Slovenian.
    vkd_ckb_ar: Sorani Kurdish with Arabic-based keyboard.
    vkd_ckb_en: Sorani Kurdish with English-based keyboard.
    xkb:latam::spa: Spanish (Latin America).
    xkb:es::spa: Spanish (Spain).
    xkb:se::swe: Swedish.
    vkd_ta_itrans: Tamil ITRANS.
    vkd_ta_phone: Tamil Phonetic.
    ta-t-i0-und: Tamil Transliteration.
    vkd_ta_inscript: Tamil with InScript keyboard.
    vkd_ta_tamil99: Tamil with Tamil99 keyboard.
    vkd_ta_typewriter: Tamil with Typewriter keyboard.
    vkd_te_phone: Telugu Phonetic.
    te-t-i0-und: Telugu Transliteration.
    vkd_th: Thai with Kedmanee keyboard.
    vkd_th_pattajoti: Thai with Pattachote keyboard.
    vkd_th_tis: Thai with TIS 820-2531 keyboard.
    ti-t-i0-und: Tigrinya.
    xkb:tr::tur: Turkish.
    xkb:tr:f:tur: Turkish with F-keyboard.
    xkb:ua::ukr: Ukrainian.
    ur-t-i0-und: Urdu.
    vkd_vi_telex: Vietnamese Telex.
    vkd_vi_viqr: Vietnamese VIQR.
    vkd_vi_vni: Vietnamese VNI.
    vkd_vi_tcvn: Vietnamese with TCVN keyboard.
  allowedInputMethodsForceEnabled: TYPE_BOOL
    true: Automatically install selected keyboard languages.
    false: Do not automatically install any keyboard languages.

chrome.users.AllowedLanguages: Allowed ChromeOS languages.
  allowedLanguages: TYPE_LIST
    ar: Arabic - ‫العربية‬.
    bn: Bangla - ‪বাংলা‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    zh-CN: Chinese (Simplified) - ‪简体中文‬.
    zh-TW: Chinese (Traditional) - ‪繁體中文‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-NZ: English (New Zealand).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fil: Filipino.
    fi: Finnish - ‪Suomi‬.
    fr-CA: French (Canada) - ‪Français (Canada)‬.
    fr: French (France) - ‪Français (France)‬.
    fr-CH: French (Switzerland) - ‪Français (Suisse)‬.
    de: German (Germany) - ‪Deutsch (Deutschland)‬.
    de-CH: German (Switzerland) - ‪Deutsch (Schweiz)‬.
    el: Greek - ‪Ελληνικά‬.
    gu: Gujarati - ‪ગુજરાતી‬.
    iw: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    is: Icelandic - ‪íslenska‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    ja: Japanese - ‪日本語‬.
    kn: Kannada - ‪ಕನ್ನಡ‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    ms: Malay - ‪Melayu‬.
    ml: Malayalam - ‪മലയാളം‬.
    mr: Marathi - ‪मराठी‬.
    no: Norwegian - ‪norsk‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es: Spanish (Spain) - ‪Español (España)‬.
    sv: Swedish - ‪Svenska‬.
    ta: Tamil - ‪தமிழ்‬.
    te: Telugu - ‪తెలుగు‬.
    th: Thai - ‪ไทย‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.

chrome.users.AllowExcludeDisplayInMirrorMode: Exclude display in mirror mode.
  allowExcludeDisplayInMirrorMode: TYPE_BOOL
    true: Allow users to exclude displays from mirror mode.
    false: Do not allow users to exclude displays from mirror mode.

chrome.users.AllowFileSelectionDialogs: File selection dialogs.
  allowFileSelectionDialogs: TYPE_BOOL
    true: Allow users to open file selection dialogs.
    false: Block file selection dialogs.

chrome.users.AllowPopulateAssetIdentifier: Asset identifier during enrollment.
  allowToUpdateDeviceAttribute: TYPE_BOOL
    true: Users in this organization can provide asset ID and location during enrollment.
    false: Do not allow for users in this organization.

chrome.users.AllowPrinting: Printing.
  printingEnabled: TYPE_BOOL
    true: Enable printing.
    false: Disable printing.

chrome.users.AllowSystemNotifications: System notifications.
  allowSystemNotifications: TYPE_BOOL
    true: Allow system notifications to be used.
    false: Do not allow system notifications to be used.

chrome.users.AllowWakeLocks: Wake locks.
  allowScreenWakeLocks: TYPE_BOOL
    true: Allow screen wake locks for power management.
    false: Demote screen wake lock requests to system wake lock requests.
  allowWakeLocks: TYPE_BOOL
    true: Allow wake locks.
    false: Do not allow wake locks.

chrome.users.AllowWebAuthnWithBrokenTlsCerts: Web Authentication requests on sites with broken TLS certificates.
  allowWebAuthnWithBrokenTlsCerts: TYPE_BOOL
    true: Allow WebAuthn API requests on sites with broken TLS certificates.
    false: Do not allow WebAuthn API requests on sites with broken TLS certificates.

chrome.users.AlternateErrorPages: Alternate error pages.
  alternateErrorPagesEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never use alternate error pages.
    TRUE: Always use alternate error pages.

chrome.users.AlternativeBrowserParameters: Alternative browser parameters.
  alternativeBrowserParameters: TYPE_LIST
    Command-line parameters. Parameters for the alternative browser. If a parameter contains {"${url}"}, it gets replaced with the URL. Otherwise, the URL is appended at the end of the command line.

chrome.users.AlternativeBrowserPath: Alternative browser path.
  alternativeBrowserPath: TYPE_STRING
    Path to the alternative browser. If this policy is unset, a platform-specific default is used. Only some values are supported, such as: {"${ie}"}, {"${edge}"}, and the path to iexplore.exe.

chrome.users.AlwaysOnVpn: Always on VPN.
  alwaysOnVpnApp: TYPE_STRING
    Activate Always-on VPN for all user traffic with an app from a list of force installed Android VPN apps. Please make sure the configured app is force installed.
  vpnConfigAllowed: TYPE_BOOL
    true: Allow user to disconnect from a VPN manually (VPN will reconnect on log in).
    false: Do not allow user to disconnect from a VPN manually.

chrome.users.AlwaysOnVpnPreConnectUrlAllowlist: Always on VPN URL exceptions.
  alwaysOnVpnPreConnectUrlAllowlist: TYPE_LIST
    URL exceptions. Allow the user to navigate to any URL in this list while an Android Always on VPN is set to strict mode and the VPN is not connected. Maximum of 1000 URLs.

chrome.users.AlwaysOpenPdfExternally: PDF files.
  alwaysOpenPdfExternally: TYPE_BOOL
    true: Open PDF files with the system default app.
    false: Open PDF files in Chrome.
  alwaysOpenPdfExternallyCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.AmbientAuthenticationInPrivateModesEnabled: Ambient authentication.
  ambientAuthenticationInPrivateModesEnabled: TYPE_ENUM
    UNSET: No policy set.
    REGULAR_ONLY: Enable in regular sessions only.
    INCOGNITO_AND_REGULAR: Enable in regular and incognito sessions.
    GUEST_AND_REGULAR: Enable in regular and guest sessions.
    ALL: Enable in regular, incognito and guest sessions.

chrome.users.AndroidBackupRestoreServiceEnabled: Control Android backup and restore service.
  arcBackupRestoreServiceEnabled: TYPE_ENUM
    BACKUP_AND_RESTORE_DISABLED: Backup and restore disabled.
    BACKUP_AND_RESTORE_UNDER_USER_CONTROL: Let user decides whether to enable backup and restore.

chrome.users.AndroidGoogleLocationServicesEnabled: Google location services.
  arcGoogleLocationServicesEnabled: TYPE_ENUM
    DISABLED: Disable location services during initial setup for Android apps on ChromeOS.
    UNDER_USER_CONTROL: Allow the user to decide whether to use location services for Android apps on ChromeOS during initial setup.

chrome.users.AppCacheForceEnabled: AppCache.
  appCacheForceEnabled: TYPE_BOOL
    true: Allow websites to use the deprecated AppCache feature.
    false: Do not allow websites to use the deprecated AppCache feature.

chrome.users.ApplicationBoundEncryptionEnabled: Application bound encryption.
  applicationBoundEncryptionEnabled: TYPE_BOOL
    true: Enable application bound encryption.
    false: Disable application bound encryption.

chrome.users.ApplicationLocaleValue: Browser locale.
  applicationLocaleValue: TYPE_STRING
    : Use the language specified by user or system.
    af: Afrikaans.
    sq: Albanian - ‪shqip‬.
    am: Amharic - ‪አማርኛ‬.
    ar: Arabic - ‫العربية‬.
    an: Aragonese.
    hy: Armenian - ‪հայերեն‬.
    as: Assamese - ‪অসমীয়া‬.
    ast: Asturian - ‪asturianu‬.
    az: Azerbaijani - ‪azərbaycan‬.
    bn: Bangla - ‪বাংলা‬.
    eu: Basque - ‪euskara‬.
    be: Belarusian - ‪беларуская‬.
    bs: Bosnian - ‪bosanski‬.
    br: Breton - ‪brezhoneg‬.
    bg: Bulgarian - ‪български‬.
    my: Burmese - ‪မြန်မာ‬.
    ca: Catalan - ‪català‬.
    ceb: Cebuano.
    ckb: Central Kurdish - ‫کوردیی ناوەندی‬.
    chr: Cherokee - ‪ᏣᎳᎩ‬.
    zh: Chinese - ‪中文‬.
    zh-HK: Chinese (Hong Kong) - ‪中文（香港）‬.
    zh-CN: Chinese (Simplified) - ‪简体中文‬.
    zh-TW: Chinese (Traditional) - ‪繁體中文‬.
    co: Corsican.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en: English.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-IN: English (India).
    en-NZ: English (New Zealand).
    en-ZA: English (South Africa).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    eo: Esperanto.
    et: Estonian - ‪eesti‬.
    fo: Faroese - ‪føroyskt‬.
    fil: Filipino.
    fi: Finnish - ‪Suomi‬.
    fr: French - ‪Français‬.
    fr-CA: French (Canada) - ‪Français (Canada)‬.
    fr-FR: French (France) - ‪Français (France)‬.
    fr-CH: French (Switzerland) - ‪Français (Suisse)‬.
    gl: Galician - ‪galego‬.
    ka: Georgian - ‪ქართული‬.
    de: German - ‪Deutsch‬.
    de-AT: German (Austria) - ‪Deutsch (Österreich)‬.
    de-DE: German (Germany) - ‪Deutsch (Deutschland)‬.
    de-LI: German (Liechtenstein) - ‪Deutsch (Liechtenstein)‬.
    de-CH: German (Switzerland) - ‪Deutsch (Schweiz)‬.
    el: Greek - ‪Ελληνικά‬.
    gn: Guarani.
    gu: Gujarati - ‪ગુજરાતી‬.
    ht: Haitian Creole - ‪Créole haïtien‬.
    ha: Hausa.
    haw: Hawaiian - ‪ʻŌlelo Hawaiʻi‬.
    iw: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hmn: Hmong.
    hu: Hungarian - ‪magyar‬.
    is: Icelandic - ‪íslenska‬.
    ig: Igbo.
    id: Indonesian - ‪Indonesia‬.
    ia: Interlingua - ‪interlingua‬.
    ga: Irish - ‪Gaeilge‬.
    it: Italian - ‪Italiano‬.
    it-IT: Italian (Italy) - ‪Italiano (Italia)‬.
    it-CH: Italian (Switzerland) - ‪Italiano (Svizzera)‬.
    ja: Japanese - ‪日本語‬.
    jv: Javanese - ‪Jawa‬.
    kn: Kannada - ‪ಕನ್ನಡ‬.
    kk: Kazakh - ‪қазақ тілі‬.
    km: Khmer - ‪ខ្មែរ‬.
    rw: Kinyarwanda - ‪Ikinyarwanda‬.
    kok: Konkani - ‪कोंकणी‬.
    ko: Korean - ‪한국어‬.
    ku: Kurdish - ‪kurdî [kurmancî]‬.
    ky: Kyrgyz - ‪кыргызча‬.
    lo: Lao - ‪ລາວ‬.
    la: Latin.
    lv: Latvian - ‪latviešu‬.
    ln: Lingala - ‪lingála‬.
    lt: Lithuanian - ‪lietuvių‬.
    lb: Luxembourgish - ‪Lëtzebuergesch‬.
    mk: Macedonian - ‪македонски‬.
    mg: Malagasy.
    ms: Malay - ‪Melayu‬.
    ml: Malayalam - ‪മലയാളം‬.
    mt: Maltese - ‪Malti‬.
    mi: Māori.
    mr: Marathi - ‪मराठी‬.
    mn: Mongolian - ‪монгол‬.
    ne: Nepali - ‪नेपाली‬.
    no: Norwegian - ‪norsk‬.
    nn: Norwegian Nynorsk - ‪norsk nynorsk‬.
    ny: Nyanja.
    oc: Occitan - ‪occitan‬.
    or: Odia - ‪ଓଡ଼ିଆ‬.
    om: Oromo - ‪Oromoo‬.
    ps: Pashto - ‫پښتو‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt: Portuguese - ‪Português‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    pa: Punjabi - ‪ਪੰਜਾਬੀ‬.
    qu: Quechua - ‪Runasimi‬.
    ro: Romanian - ‪română‬.
    rm: Romansh - ‪rumantsch‬.
    ru: Russian - ‪Русский‬.
    sm: Samoan.
    gd: Scottish Gaelic - ‪Gàidhlig‬.
    sr: Serbian - ‪српски‬.
    sn: Shona - ‪chiShona‬.
    sd: Sindhi - ‫سنڌي‬.
    si: Sinhala - ‪සිංහල‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    so: Somali - ‪Soomaali‬.
    st: Southern Sotho - ‪Sesotho‬.
    es: Spanish - ‪Español‬.
    es-AR: Spanish (Argentina) - ‪Español (Argentina)‬.
    es-CL: Spanish (Chile) - ‪Español (Chile)‬.
    es-CO: Spanish (Colombia) - ‪Español (Colombia)‬.
    es-CR: Spanish (Costa Rica) - ‪Español (Costa Rica)‬.
    es-HN: Spanish (Honduras) - ‪Español (Honduras)‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es-MX: Spanish (Mexico) - ‪Español (México)‬.
    es-PE: Spanish (Peru) - ‪Español (Perú)‬.
    es-ES: Spanish (Spain) - ‪Español (España)‬.
    es-US: Spanish (United States) - ‪Español (Estados Unidos)‬.
    es-UY: Spanish (Uruguay) - ‪Español (Uruguay)‬.
    es-VE: Spanish (Venezuela) - ‪Español (Venezuela)‬.
    su: Sundanese - ‪Basa Sunda‬.
    sw: Swahili - ‪Kiswahili‬.
    sv: Swedish - ‪Svenska‬.
    tg: Tajik - ‪тоҷикӣ‬.
    ta: Tamil - ‪தமிழ்‬.
    tt: Tatar - ‪татар‬.
    te: Telugu - ‪తెలుగు‬.
    th: Thai - ‪ไทย‬.
    ti: Tigrinya - ‪ትግርኛ‬.
    to: Tongan - ‪lea fakatonga‬.
    tn: Tswana - ‪Setswana‬.
    tr: Turkish - ‪Türkçe‬.
    tk: Turkmen - ‪türkmen dili‬.
    uk: Ukrainian - ‪Українська‬.
    ur: Urdu - ‫اردو‬.
    ug: Uyghur - ‫ئۇيغۇرچە‬.
    uz: Uzbek - ‪o‘zbek‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    wa: Walloon.
    cy: Welsh - ‪Cymraeg‬.
    fy: Western Frisian - ‪Frysk‬.
    wo: Wolof.
    xh: Xhosa - ‪IsiXhosa‬.
    yi: Yiddish - ‫ייִדיש‬.
    yo: Yoruba - ‪Èdè Yorùbá‬.
    zu: Zulu - ‪isiZulu‬.
  applicationLocaleValueSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.AppRecommendationZeroStateEnabled: Previously installed app recommendations.
  appRecommendationZeroStateEnabled: TYPE_BOOL
    true: Show app recommendations in the ChromeOS launcher.
    false: Do not show app recommendations in the ChromeOS launcher.

chrome.users.apps.AccessToKeys: Allows setting of whether the app can access client keys.
  allowAccessToKeys: TYPE_BOOL
    Controls whether the app can access client keys.

chrome.users.apps.AppInstallationUrl: Specifies the url from which to install a self hosted Chrome Extension.
  installationUrl: TYPE_STRING
    The url from which to install a self hosted Chrome Extension.

chrome.users.apps.CertificateManagement: Allows setting of certificate management related permissions.
  allowAccessToKeys: TYPE_BOOL
    Controls whether the app can access client keys.
  allowEnterpriseChallenge: TYPE_BOOL
    Controls whether the app can challenge enterprise keys.

chrome.users.apps.DefaultLaunchContainer: Allows setting of the default launch container for web apps.
  defaultLaunchContainer: TYPE_ENUM
    TAB: Browser tab.
    WINDOW: Separate window.

chrome.users.apps.EnterpriseChallenge: Allows setting of whether the app can challenge enterprise keys.
  allowEnterpriseChallenge: TYPE_BOOL
    Controls whether the app can challenge enterprise keys.

chrome.users.apps.IncludeInChromeWebStoreCollection: Specifies whether the Chrome Application should appear in the Chrome Web Store collection.
  includeInCollection: TYPE_BOOL
    Controls whether a Chrome Application should appear in the Chrome Web Store collection.
  spotlightRecommended: TYPE_BOOL
    Controls whether a Chrome Application should be spotlighted in the Chrome Web Store collection.

chrome.users.apps.InstallationUrl: Specifies the url from which to install a self hosted Chrome Extension.
  installationUrl: TYPE_STRING
    The url from which to install a self hosted Chrome Extension.
  overrideInstallationUrl: TYPE_BOOL
    Override the URL provided in the extension manifest with the provided installation url.

chrome.users.apps.InstallType: Specifies the manner in which the app is to be installed. Note: It's required in order to add an App or Extension to the set of managed apps & extensions of an Organizational Unit.
  appInstallType: TYPE_ENUM
    BLOCKED: Block installation of the app. Note: Web apps can't be Blocked, which means setting this option for Web Apps is disallowed.
    ALLOWED: Allow installation of the app.
    FORCED: Force install the app.
    FORCED_AND_PIN_TO_TOOLBAR: Force install and pin the app to the toolbar.
    NORMAL: Force install the app, but allow the user to disable it. This option is only available for Chrome extensions.
    NORMAL_AND_PIN_TO_TOOLBAR: Force install and pin the app to the toolbar, but allow the user to disable it. This option is only available for Chrome extensions.
    REMOVE: Block installation of the app and remove it from the device. This option is only available for Chrome extensions.

chrome.users.apps.ManagedConfiguration: Allows setting of the managed configuration.
  managedConfiguration: TYPE_STRING
    Sets the managed configuration JSON format.

chrome.users.apps.MandatoryForIncognitoNavigation: Sets the chrome app as mandatory for incognito navigation. User will have to install the app in order to access Incognito Mode in Chrome. Note: The policy is only applicable if the Incognito mode is enabled for the user.
  mandatoryForIncognitoNavigation: TYPE_BOOL
    true: Set the chrome app as mandatory for incognito navigation.
    false: Set the chrome app as not mandatory for incognito navigation.

chrome.users.apps.OverrideInstallationUrl: Allows overriding of the url from which to install a self hosted Chrome Extension.
  overrideInstallationUrl: TYPE_BOOL
    true: Use URL provided by AppInstallationUrl.
    false: Use URL provided in the extension manifest.

chrome.users.apps.PermissionsAndUrlAccess: Allows setting of allowed and blocked hosts.
  blockedPermissions: TYPE_LIST
    : Allow all permissions. If empty string is set, it must be the only value set for the policy.
    activeTab: Active tab.
    app.window.alwaysOnTop: Always on top.
    alarms: Alarms.
    audioCapture: Audio capture.
    certificateProvider: Certificate provider.
    clipboardRead: Clipboard read.
    clipboardWrite: Clipboard write.
    contextMenus: Context menus.
    cookies: Cookies.
    desktopCapture: Desktop capture.
    documentScan: Document scan.
    enterprise.deviceAttributes: Enterprise device attributes.
    experimental: Experimental APIs.
    app.window.fullscreen: Fullscreen apps.
    fileBrowserHandler: File browser handler.
    fileSystem: File system.
    fileSystemProvider: File system provider.
    hid: HID.
    app.window.fullscreen.overrideEsc: Override fullscreen escape.
    idle: Detect idle.
    identity: Identity.
    gcm: Google Cloud Messaging.
    geolocation: Geo location.
    mediaGalleries: Media galleries.
    nativeMessaging: Native messaging.
    networking.config: Captive portal authenticator.
    power: Power.
    notifications: Notifications.
    printerProvider: Printers.
    serial: Serial.
    proxy: Set proxy.
    platformKeys: Platform keys.
    storage: Storage.
    syncFileSystem: Sync file system.
    system.cpu: CPU metadata.
    system.memory: Memory metadata.
    system.network: Network metadata.
    system.display: Display metadata.
    system.storage: Storage metadata.
    tts: Text to speech.
    unlimitedStorage: Unlimited storage.
    usb: USB.
    videoCapture: Video capture.
    vpnProvider: VPN provider.
    webRequest: Web requests.
    webRequestBlocking: Block web requests.
    app.window.alpha: Alpha.
    app.window.alwaysOnTop: Always on top.
    appview: App view.
    audio: Audio.
    bluetoothPrivate: Bluetooth private.
    cecPrivate: Cec private.
    clipboard: Clipboard.
    declarativeNetRequest: Declarative net request.
    declarativeNetRequestWithHostAccess: Declarative net request with host access.
    declarativeNetRequestFeedback: Declarative net request feedback.
    declarativeWebRequest: Declarative web request.
    diagnostics: Diagnostics.
    dns: Dns.
    externally_connectable.all_urls: All URLs externally connectable.
    feedbackPrivate: Feedback private.
    fileSystem.directory: File system directory.
    fileSystem.retainEntries: File system retain entries.
    fileSystem.write: File system write.
    fileSystem.requestFileSystem: File system request file system.
    app.window.ime: Ime.
    lockScreen: Lock screen.
    mediaPerceptionPrivate: Media perception private.
    metricsPrivate: Metrics private.
    networking.onc: Networking open network configuration.
    networkingPrivate: Networking private.
    odfsConfigPrivate: ODFS config private.
    offscreen: Offscreen.
    runtime: Runtime.
    socket: Socket.
    app.window.shape: Shape.
    usbDevices: USB Devices.
    u2fDevices: U2F devices.
    userScripts: User scripts.
    virtualKeyboard: Virtual keyboard.
    virtualKeyboardPrivate: Virtual keyboard private.
    webview: Web view.
    webRequestAuthProvider: Auth provider web requests.
    arcAppsPrivate: Arc apps private.
    browser: Browser.
    enterprise.remoteApps: Enterprise remote apps.
    firstRunPrivate: First run private.
    mediaGalleries.allAutoDetected: All autodetected media galleries.
    mediaGalleries.scan: Scan media galleries.
    mediaGalleries.read: Read media galleries.
    mediaGalleries.copyTo: Copy to media galleries.
    mediaGalleries.delete: Delete media galleries.
    pointerLock: Pointer lock.
    os.attached_device_info: OS attached device info.
    os.bluetooth_peripherals_info: OS bluetooth peripherals info.
    os.diagnostics: OS diagnostics.
    os.diagnostics.network_info_mlab: OS network info MLAB diagnostics.
    os.events: OS events.
    os.management.audio: OS management audio.
    os.telemetry: OS telemetry.
    os.telemetry.serial_number: OS serial number telemetry.
    os.telemetry.network_info: OS network info telemetry.
    accessibilityFeatures.modify: Accessibility features modify.
    accessibilityFeatures.read: Accessibility features read.
    accessibilityPrivate: Accessibility private.
    accessibilityServicePrivate: Accessibility service private.
    activityLogPrivate: Activity log private.
    autofillPrivate: Autofill private.
    autotestPrivate: Autotest private.
    background: Background.
    bookmarks: Bookmarks.
    brailleDisplayPrivate: Braille display private.
    browsingData: Browsing data.
    chromePrivate: Chrome private.
    chromeosInfoPrivate: ChromeOS info private.
    commandLinePrivate: Command line private.
    commands.accessibility: Commands accessibility.
    contentSettings: Content settings.
    crashReportPrivate: Crash report private.
    devtools: Devtools.
    debugger: Debugger.
    developerPrivate: Developer private.
    declarativeContent: Declarative content.
    downloads: Downloads.
    downloads.open: Downloads open.
    downloads.shelf: Downloads shelf.
    downloads.ui: Downloads UI.
    enterprise.networkingAttributes: Enterprise networking attributes.
    enterprise.hardwarePlatform: Enterprise hardware platform.
    enterprise.kioskInput: Enterprise kiosk input.
    enterprise.platformKeys: Enterprise platform keys.
    enterprise.platformKeysPrivate: Enterprise platform keys private.
    enterprise.reportingPrivate: Enterprise reporting private.
    experimentalAiData: Experimental AI data.
    favicon: Favicon.
    fileManagerPrivate: File manager private.
    fontSettings: Font settings.
    sharedStoragePrivate: Shared storage private.
    history: History.
    identity.email: Identity email.
    idltest: IDL test.
    input: Input.
    imageLoaderPrivate: Image loader private.
    inputMethodPrivate: Input method private.
    languageSettingsPrivate: Language settings private.
    lockWindowFullscreenPrivate: Lock window fullscreen private.
    login: Login.
    loginScreenStorage: Login screen storage.
    loginScreenUi: Login screen UI.
    loginState: Login state.
    webcamPrivate: Webcam private.
    management: Management.
    mediaPlayerPrivate: Media player private.
    mdns: Multicast domain name system.
    echoPrivate: Echo private.
    pageCapture: Page capture.
    passwordsPrivate: Passwords private.
    pdfViewerPrivate: PDF viewer private.
    plugin: Plugin.
    printing: Printing.
    printingMetrics: Printing metrics.
    privacy: Privacy.
    processes: Processes.
    imageWriterPrivate: Image writer private.
    readingList: Reading list.
    resourcesPrivate: Resources private.
    rtcPrivate: RTC private.
    safeBrowsingPrivate: Safe browsing private.
    scripting: Scripting.
    search: Search.
    sessions: Sessions.
    settingsPrivate: Settings private.
    sidePanel: Side panel.
    smartCardProviderPrivate: Smart card provider private.
    speechRecognitionPrivate: Speech recognition private.
    systemLog: System log.
    systemPrivate: System private.
    tabGroups: Tab groups.
    tabs: Tabs.
    tabCapture: Tab capture.
    terminalPrivate: Terminal private.
    topSites: Top sites.
    transientBackground: Transient background.
    ttsEngine: Text to speech engine.
    usersPrivate: Users private.
    wallpaper: Wallpaper.
    webAuthenticationProxy: Web authentication proxy.
    webNavigation: Web navigation.
    webrtcAudioPrivate: WebRTC audio private.
    webrtcDesktopCapturePrivate: WebRTC desktop capture private.
    webrtcLoggingPrivate: WebRTC logging private.
    webrtcLoggingPrivate.audioDebug: WebRTC audio debug logging private.
    webstorePrivate: Webstore private.
    wmDesksPrivate: WM desks private.
  allowedPermissions: TYPE_LIST
    activeTab: Active tab.
    app.window.alwaysOnTop: Always on top.
    alarms: Alarms.
    audioCapture: Audio capture.
    certificateProvider: Certificate provider.
    clipboardRead: Clipboard read.
    clipboardWrite: Clipboard write.
    contextMenus: Context menus.
    desktopCapture: Desktop capture.
    documentScan: Document scan.
    enterprise.deviceAttributes: Enterprise device attributes.
    experimental: Experimental APIs.
    app.window.fullscreen: Fullscreen apps.
    fileBrowserHandler: File browser handler.
    fileSystem: File system.
    fileSystemProvider: File system provider.
    hid: HID.
    app.window.fullscreen.overrideEsc: Override fullscreen escape.
    idle: Detect idle.
    identity: Identity.
    gcm: Google Cloud Messaging.
    geolocation: Geo location.
    mediaGalleries: Media galleries.
    nativeMessaging: Native messaging.
    networking.config: Captive portal authenticator.
    power: Power.
    notifications: Notifications.
    printerProvider: Printers.
    serial: Serial.
    proxy: Set proxy.
    platformKeys: Platform keys.
    storage: Storage.
    syncFileSystem: Sync file system.
    system.cpu: CPU metadata.
    system.memory: Memory metadata.
    system.network: Network metadata.
    system.display: Display metadata.
    system.storage: Storage metadata.
    tts: Text to speech.
    unlimitedStorage: Unlimited storage.
    usb: USB.
    videoCapture: Video capture.
    vpnProvider: VPN provider.
    webRequest: Web requests.
    webRequestBlocking: Block web requests.
    app.window.alpha: Alpha.
    app.window.alwaysOnTop: Always on top.
    appview: App view.
    audio: Audio.
    bluetoothPrivate: Bluetooth private.
    cecPrivate: Cec private.
    clipboard: Clipboard.
    declarativeNetRequest: Declarative net request.
    declarativeNetRequestWithHostAccess: Declarative net request with host access.
    declarativeNetRequestFeedback: Declarative net request feedback.
    declarativeWebRequest: Declarative web request.
    diagnostics: Diagnostics.
    dns: Dns.
    externally_connectable.all_urls: All URLs externally connectable.
    feedbackPrivate: Feedback private.
    fileSystem.directory: File system directory.
    fileSystem.retainEntries: File system retain entries.
    fileSystem.write: File system write.
    fileSystem.requestFileSystem: File system request file system.
    app.window.ime: Ime.
    lockScreen: Lock screen.
    mediaPerceptionPrivate: Media perception private.
    metricsPrivate: Metrics private.
    networking.onc: Networking open network configuration.
    networkingPrivate: Networking private.
    odfsConfigPrivate: ODFS config private.
    offscreen: Offscreen.
    runtime: Runtime.
    socket: Socket.
    app.window.shape: Shape.
    usbDevices: USB Devices.
    u2fDevices: U2F devices.
    userScripts: User scripts.
    virtualKeyboard: Virtual keyboard.
    virtualKeyboardPrivate: Virtual keyboard private.
    webview: Web view.
    webRequestAuthProvider: Auth provider web requests.
    arcAppsPrivate: Arc apps private.
    browser: Browser.
    enterprise.remoteApps: Enterprise remote apps.
    firstRunPrivate: First run private.
    mediaGalleries.allAutoDetected: All autodetected media galleries.
    mediaGalleries.scan: Scan media galleries.
    mediaGalleries.read: Read media galleries.
    mediaGalleries.copyTo: Copy to media galleries.
    mediaGalleries.delete: Delete media galleries.
    pointerLock: Pointer lock.
    os.attached_device_info: OS attached device info.
    os.bluetooth_peripherals_info: OS bluetooth peripherals info.
    os.diagnostics: OS diagnostics.
    os.diagnostics.network_info_mlab: OS network info MLAB diagnostics.
    os.events: OS events.
    os.management.audio: OS management audio.
    os.telemetry: OS telemetry.
    os.telemetry.serial_number: OS serial number telemetry.
    os.telemetry.network_info: OS network info telemetry.
    accessibilityFeatures.modify: Accessibility features modify.
    accessibilityFeatures.read: Accessibility features read.
    accessibilityPrivate: Accessibility private.
    accessibilityServicePrivate: Accessibility service private.
    activityLogPrivate: Activity log private.
    autofillPrivate: Autofill private.
    autotestPrivate: Autotest private.
    background: Background.
    bookmarks: Bookmarks.
    brailleDisplayPrivate: Braille display private.
    browsingData: Browsing data.
    chromePrivate: Chrome private.
    chromeosInfoPrivate: ChromeOS info private.
    commandLinePrivate: Command line private.
    commands.accessibility: Commands accessibility.
    contentSettings: Content settings.
    crashReportPrivate: Crash report private.
    devtools: Devtools.
    debugger: Debugger.
    developerPrivate: Developer private.
    declarativeContent: Declarative content.
    downloads: Downloads.
    downloads.open: Downloads open.
    downloads.shelf: Downloads shelf.
    downloads.ui: Downloads UI.
    enterprise.networkingAttributes: Enterprise networking attributes.
    enterprise.hardwarePlatform: Enterprise hardware platform.
    enterprise.kioskInput: Enterprise kiosk input.
    enterprise.platformKeys: Enterprise platform keys.
    enterprise.platformKeysPrivate: Enterprise platform keys private.
    enterprise.reportingPrivate: Enterprise reporting private.
    experimentalAiData: Experimental AI data.
    favicon: Favicon.
    fileManagerPrivate: File manager private.
    fontSettings: Font settings.
    sharedStoragePrivate: Shared storage private.
    history: History.
    identity.email: Identity email.
    idltest: IDL test.
    input: Input.
    imageLoaderPrivate: Image loader private.
    inputMethodPrivate: Input method private.
    languageSettingsPrivate: Language settings private.
    lockWindowFullscreenPrivate: Lock window fullscreen private.
    login: Login.
    loginScreenStorage: Login screen storage.
    loginScreenUi: Login screen UI.
    loginState: Login state.
    webcamPrivate: Webcam private.
    management: Management.
    mediaPlayerPrivate: Media player private.
    mdns: Multicast domain name system.
    echoPrivate: Echo private.
    pageCapture: Page capture.
    passwordsPrivate: Passwords private.
    pdfViewerPrivate: PDF viewer private.
    plugin: Plugin.
    printing: Printing.
    printingMetrics: Printing metrics.
    privacy: Privacy.
    processes: Processes.
    imageWriterPrivate: Image writer private.
    readingList: Reading list.
    resourcesPrivate: Resources private.
    rtcPrivate: RTC private.
    safeBrowsingPrivate: Safe browsing private.
    scripting: Scripting.
    search: Search.
    sessions: Sessions.
    settingsPrivate: Settings private.
    sidePanel: Side panel.
    smartCardProviderPrivate: Smart card provider private.
    speechRecognitionPrivate: Speech recognition private.
    systemLog: System log.
    systemPrivate: System private.
    tabGroups: Tab groups.
    tabs: Tabs.
    tabCapture: Tab capture.
    terminalPrivate: Terminal private.
    topSites: Top sites.
    transientBackground: Transient background.
    ttsEngine: Text to speech engine.
    usersPrivate: Users private.
    wallpaper: Wallpaper.
    webAuthenticationProxy: Web authentication proxy.
    webNavigation: Web navigation.
    webrtcAudioPrivate: WebRTC audio private.
    webrtcDesktopCapturePrivate: WebRTC desktop capture private.
    webrtcLoggingPrivate: WebRTC logging private.
    webrtcLoggingPrivate.audioDebug: WebRTC logging private.
    webstorePrivate: Webstore private.
    wmDesksPrivate: WM desks private.
  blockedHosts: TYPE_LIST
    Sets extension hosts that should be blocked.
  allowedHosts: TYPE_LIST
    Sets extension hosts that should be allowed. Allowed hosts override blocked hosts.

chrome.users.apps.SkipDocumentScanConfirmation: Allows the app to skip the confirmation dialog when using the Document Scan API.
  skipDocumentScanConfirmation: TYPE_BOOL
    Controls whether a Chrome Application can skip the confirmation dialog when using the Document Scan API.

chrome.users.apps.SkipPrintConfirmation: Allows the app to skip the confirmation dialog when sending print jobs via the Chrome Printing API.
  skipPrintConfirmation: TYPE_BOOL
    Controls whether a Chrome Application can skip the confirmation dialog when sending print jobs via the Chrome Printing API.

chrome.users.appsconfig.AdHocCodeSigningForPwasEnabled: Ad hoc code signing for PWA shims.
  adHocCodeSigningForPwasEnabled: TYPE_ENUM
    UNSET: Use the Chrome default setting.
    FALSE: Do not use ad hoc code signatures for Progressive Web App shims.
    TRUE: Use ad hoc code signatures for Progressive Web App shims.

chrome.users.appsconfig.AllowedAppTypes: Allowed types of apps and extensions.
  extensionAllowedTypes: TYPE_LIST
    extension: Extension.
    theme: Theme.
    user_script: Google Apps Script.
    hosted_app: Hosted app.
    legacy_packaged_app: Legacy packaged app.
    platform_app: Chrome packaged app.

chrome.users.appsconfig.AllowedInstallSources: Allows setting of the allowed install sources for apps. Note these must be set together.
  playStoreInstallSources: TYPE_ENUM
    ALLOW_ALL_APPS: All apps allowed, admin manages blocklist.
    BLOCK_ALL_APPS: All apps blocked, admin manages allowlist.
  chromeWebStoreInstallSources: TYPE_ENUM
    ALLOW_ALL_APPS: All apps allowed, admin manages blocklist.
    BLOCK_ALL_APPS: All apps blocked, admin manages allowlist.
    BLOCK_ALL_APPS_USER_EXTENSION_REQUESTS_ALLOWED: All apps blocked, admin manages allowlist, users may request extensions.

chrome.users.appsconfig.AllowInsecureUpdates: Allow insecure extension packaging.
  extensionAllowInsecureUpdates: TYPE_BOOL
    true: Allow insecurely packaged extensions.
    false: Do not allow insecurely packaged extensions.

chrome.users.appsconfig.AndroidAppsEnabled: Android apps on Chrome devices.
  arcEnabled: TYPE_BOOL
    true: Allow users to install Android apps on ChromeOS devices.
    false: Do not allow users to install Android apps on a ChromeOS devices.
  ackNoticeForArcEnabledSetToTrue: TYPE_BOOL
    This field must be set to true to acknowledge the notice message associated with the field 'arc_enabled' set to value 'true'. Please sse the notices listed with this policy for more information.

chrome.users.appsconfig.AppExtensionInstallSources: App and extension install sources.
  extensionInstallSources: TYPE_LIST
    Sources URL patterns. Chrome will offer to install app and extension packages from URLs that match the listed patterns.

chrome.users.appsconfig.BlockExtensionsByPermission: Permissions and URLs.
  extensionBlockedPermissions: TYPE_LIST
    accessibilityPrivate: Accessibility private.
    accessibilityServicePrivate: Accessibility service private.
    accessibilityFeatures.modify: Modify accessibility features.
    accessibilityFeatures.read: Read accessibility features.
    activityLogPrivate: Activity log private.
    activeTab: Active tab.
    app.window.alpha: Alpha.
    app.window.alwaysOnTop: Always on top.
    alarms: Alarms.
    appview: App view.
    arcAppsPrivate: Arc apps private.
    audio: Audio.
    audioCapture: Audio capture.
    autofillPrivate: Autofill private.
    autotestPrivate: Autotest private.
    background: Background.
    bluetoothPrivate: Bluetooth private.
    bookmarks: Bookmarks.
    brailleDisplayPrivate: Braille display private.
    browser: Browser.
    browsingData: Browsing data.
    cecPrivate: CEC private.
    certificateProvider: Certificate provider.
    chromePrivate: Chrome private.
    chromeosInfoPrivate: ChromeOS info private.
    clipboard: Clipboard.
    clipboardRead: Clipboard read.
    clipboardWrite: Clipboard write.
    commandLinePrivate: Command line private.
    commands.accessibility: Commands accessibility.
    contentSettings: Content settings.
    contextMenus: Context menus.
    cookies: Cookies.
    crashReportPrivate: Crash report private.
    debugger: Debugger.
    declarativeContent: Declarative content.
    declarativeNetRequest: Declarative net request.
    declarativeNetRequestWithHostAccess: Declarative net request with host access.
    declarativeNetRequestFeedback: Declarative net request feedback.
    declarativeWebRequest: Declarative web request.
    desktopCapture: Desktop capture.
    developerPrivate: Developer private.
    devtools: Devtools.
    diagnostics: Diagnostics.
    dns: Domain name system.
    documentScan: Document scan.
    downloads: Downloads.
    downloads.open: Downloads open.
    downloads.shelf: Downloads shelf.
    downloads.ui: Downloads UI.
    echoPrivate: Echo private.
    enterprise.deviceAttributes: Enterprise device attributes.
    enterprise.hardwarePlatform: Enterprise hardware platform.
    enterprise.kioskInput: Enterprise kiosk input.
    enterprise.networkingAttributes: Enterprise networking attributes.
    enterprise.platformKeys: Enterprise platform keys.
    enterprise.platformKeysPrivate: Enterprise platform keys private.
    enterprise.remoteApps: Enterprise remote apps.
    enterprise.reportingPrivate: Enterprise reporting private.
    experimentalAiData: Experimental AI data.
    experimental: Experimental APIs.
    externally_connectable.all_urls: All URLs externally connectable.
    favicon: Favicon.
    feedbackPrivate: Feedback private.
    fileManagerPrivate: File manager private.
    fileSystem.directory: File system directory.
    fileSystem.retainEntries: File system retain entries.
    fileSystem.write: File system write.
    fileSystem.requestFileSystem: File system request file system.
    firstRunPrivate: First run private.
    app.window.ime: IME.
    fontSettings: Font settings.
    app.window.fullscreen: Fullscreen apps.
    fileBrowserHandler: File browser handler.
    fileSystem: File system.
    fileSystemProvider: File system provider.
    hid: HID.
    history: History.
    idle: Detect idle.
    identity: Identity.
    identity.email: Identity email.
    idltest: IDL test.
    imageLoaderPrivate: Image loader private.
    imageWriterPrivate: Image writer private.
    input: Input.
    inputMethodPrivate: Input method private.
    app.window.fullscreen.overrideEsc: Override fullscreen escape.
    gcm: Google Cloud Messaging.
    geolocation: Geo location.
    languageSettingsPrivate: Language settings private.
    lockScreen: Lock screen.
    lockWindowFullscreenPrivate: Lock window fullscreen private.
    login: Login.
    loginScreenStorage: Login screen storage.
    loginScreenUi: Login screen UI.
    loginState: Login state.
    management: Management.
    mdns: Multicast domain name system.
    mediaPerceptionPrivate: Media perception private.
    mediaPlayerPrivate: Media player private.
    metricsPrivate: Metrics private.
    mediaGalleries: Media galleries.
    mediaGalleries.allAutodetected: All autodetected media galleries.
    mediaGalleries.copyTo: Copy to media galleries.
    mediaGalleries.delete: Delete media galleries.
    mediaGalleries.read: Read media galleries.
    mediaGalleries.scan: Scan media galleries.
    nativeMessaging: Native messaging.
    networking.config: Captive portal authenticator.
    notifications: Notifications.
    os.attached_device_info: OS attached device info.
    os.bluetooth_peripherals_info: OS bluetooth peripherals info.
    os.diagnostics: OS diagnostics.
    os.diagnostics.network_info_mlab: OS network info MLAB diagnostics.
    os.events: OS events.
    os.management.audio: OS management audio.
    os.telemetry: OS telemetry.
    os.telemetry.serial_number: OS serial number telemetry.
    os.telemetry.network_info: OS network info telemetry.
    pageCapture: Page capture.
    passwordsPrivate: Passwords private.
    pdfViewerPrivate: PDF viewer private.
    platformKeys: Platform keys.
    plugin: Plugin.
    pointerLock: Pointer lock.
    power: Power.
    printerProvider: Printers.
    printing: Printing.
    printingMetrics: Printing metrics.
    privacy: Privacy.
    processes: Processes.
    readingList: Reading list.
    resourcesPrivate: Resources private.
    rtcPrivate: RTC private.
    safeBrowsingPrivate: Safe browsing private.
    scripting: Scripting.
    search: Search.
    serial: Serial.
    sessions: Sessions.
    proxy: Set proxy.
    settingsPrivate: Settings private.
    sidePanel: Side panel.
    smartCardProviderPrivate: Smart card provider private.
    speechRecognitionPrivate: Speech recognition private.
    storage: Storage.
    syncFileSystem: Sync file system.
    systemLog: System log.
    systemPrivate: System private.
    system.cpu: CPU metadata.
    system.memory: Memory metadata.
    system.network: Network metadata.
    networking.onc: Networking open network configuration.
    networkingPrivate: Networking private.
    odfsConfigPrivate: ODFS config private.
    offscreen: Offscreen.
    system.display: Display metadata.
    runtime: Runtime.
    sharedStoragePrivate: Shared storage private.
    socket: Socket.
    app.window.shape: Shape.
    system.storage: Storage metadata.
    tabCapture: Tab capture.
    tabGroups: Tab groups.
    tabs: Tabs.
    terminalPrivate: Terminal private.
    tts: Text to speech.
    ttsEngine: Text to speech engine.
    topSites: Top sites.
    transientBackground: Transient background.
    unlimitedStorage: Unlimited storage.
    usb: USB.
    usbDevices: USB devices.
    u2fDevices: U2F devices.
    userScripts: User scripts.
    usersPrivate: Users private.
    videoCapture: Video capture.
    vpnProvider: VPN provider.
    virtualKeyboard: Virtual keyboard.
    virtualKeyboardPrivate: Virtual keyboard private.
    wallpaper: Wallpaper.
    webAuthenticationProxy: Web authentication proxy.
    webcamPrivate: Webcam private.
    webNavigation: Web navigation.
    webview: Web view.
    webRequest: Web requests.
    webRequestBlocking: Block web requests.
    webRequestAuthProvider: Auth provider web requests.
    webrtcAudioPrivate: WebRTC audio private.
    webrtcDesktopCapturePrivate: WebRTC desktop capture private.
    webrtcLoggingPrivate: WebRTC logging private.
    webrtcLoggingPrivate.audioDebug: WebRTC audio debug logging private.
    webstorePrivate: Webstore private.
    wmDesksPrivate: WM desks private.
  runtimeBlockedHosts: TYPE_LIST
    Runtime blocked hosts. This is a list of patterns for matching against hostnames. URLs that match one of these patterns cannot be modified by apps and extensions. This includes injecting Javascript, altering and viewing webRequests / webNavigation, viewing and altering cookies, exceptions to the same-origin policy, etc. The format is similar to full URL patterns except no paths may be defined. e.g. "*://*.example.com". Maximum of 100 URLs.
  runtimeAllowedHosts: TYPE_LIST
    Runtime allowed hosts. Hosts that an extension can interact with regardless of whether they are listed in "Runtime blocked hosts". This is the same format as "Runtime blocked hosts". Maximum of 100 URLs.

chrome.users.appsconfig.BlockExternalExtensions: External extensions.
  blockExternalExtensions: TYPE_BOOL
    true: Block external extensions from being installed.
    false: Allow external extensions to be installed.

chrome.users.appsconfig.ChromeAppsEnabled: Extend support for Chrome Apps.
  chromeAppsEnabled: TYPE_BOOL
    true: Chrome Apps will be allowed to run on Windows, Mac, and Linux.
    false: Chrome Apps may not be allowed to run, depending on the status of the deprecation rollout.

chrome.users.appsconfig.ChromeWebStoreAnnouncement: Announcement.
  cwsHomepageAnnouncementEnabled: TYPE_BOOL
    true: Add announcement on Web Store.
    false: No announcement on Web Store.
  cwsHomepageAnnouncementText: TYPE_STRING
    Announcement text. The announcement text to display on the Chrome Web Store.
  cwsHomepageAnnouncementButtonText: TYPE_STRING
    Announcement button text. The announcement button text to display on the Chrome Web Store.
  cwsHomepageAnnouncementButtonLink: TYPE_STRING
    Announcement button link. The announcement button link to use on the Chrome Web Store.

chrome.users.appsconfig.ChromeWebStoreBranding: Org name & logo.
  cwsBrandingEnabled: TYPE_BOOL
    true: Customize org name and logo.
    false: Don't customize org name and logo.
  cwsBrandingOrgName: TYPE_STRING
    Organization name displayed. Name to be displayed on your users' custom Web Store.
  cwsBrandingOrgLogo
    downloadUri: TYPE_STRING

chrome.users.appsconfig.ChromeWebStoreHomepage: Chrome Web Store homepage.
  cwsHomePage: TYPE_ENUM
    DEFAULT: Use the default homepage.
    COLLECTION: Use the Chrome Web Store collection.
    CUSTOM: Use a custom page.
  cwsHomePageCollectionName: TYPE_STRING
    Collection name. Specifies the name of the collection of apps on the Chrome Web Store homepage.
  cwsHomePageCustomUrl: TYPE_STRING
    Collection URL. Specifies the URL of the collection of apps on the Chrome Web Store homepage.
  cwsHomePageCollectionIncludePrivateApps: TYPE_BOOL
    true: Include all private apps from this domain.
    false: Choose which apps are included in this collection.

chrome.users.appsconfig.ChromeWebStoreHomepageBanner: Homepage banner.
  cwsExtensionHomepageBannerSetting: TYPE_ENUM
    USE_DEFAULT: Use the default homepage banner.
    USE_CUSTOM: Customize homepage banner.
    USE_NONE: Show no banner on the Web Store.
  cwsExtensionHomepageBannerImage
    downloadUri: TYPE_STRING
  cwsExtensionHomepageBannerBackgroundColor: TYPE_STRING
    Banner background color. Enter a valid hex color, for instance #FFFFFF.
  cwsExtensionHomepageBannerTextColor: TYPE_STRING
    Banner text color. Enter a valid hex color, for instance #FFFFFF.
  cwsExtensionHomepageBannerHeadlineText: TYPE_STRING
    Headline text. The headline text to display on the banner.
  cwsExtensionHomepageBannerDescriptionText: TYPE_STRING
    Description text. The description text to display on the banner.

chrome.users.appsconfig.ChromeWebStorePagesAndContent: Pages & content.
  cwsPagesContentCustomizationEnabled: TYPE_BOOL
    true: Customize Web Store pages and content.
    false: Use default Web Store pages and content.
  cwsPagesContentDiscoverPageEnabled: TYPE_BOOL
    true: Show Discover page.
    false: Hide Discover page.
  cwsPagesContentEnabledPreviews: TYPE_LIST
    recommended: Show the recommended extensions preview.
    private: Show the private extensions preview.
  cwsPagesContentCategories: TYPE_LIST
    COMMUNICATION: Communication.
    DEVELOPER_TOOLS: Developer Tools.
    EDUCATION: Education.
    TOOLS: Tools.
    WORKFLOW_AND_PLANNING: Workflow & Planning.
    EXTENSIONS_ART_AND_DESIGN: Art & Design.
    EXTENSIONS_ENTERTAINMENT: Entertainment.
    GAMES: Games.
    HOUSEHOLD: Household.
    JUST_FOR_FUN: Just for Fun.
    NEWS_AND_WEATHER: News & Weather.
    SHOPPING: Shopping.
    SOCIAL_NETWORKING: Social Networking.
    TRAVEL: Travel.
    WELL_BEING: Well-being.
    ACCESSIBILITY: Accessibility.
    FUNCTIONALITY_AND_UI: Functionality & UI.
    PRIVACY_AND_SECURITY: Privacy & Security.

chrome.users.appsconfig.ChromeWebStorePermissions: Chrome Web Store permissions.
  allowWebstorePublish: TYPE_BOOL
    true: Allow users to publish private apps that are restricted to your domain on Chrome Web Store.
    false: Do not allow users to publish private apps that are restricted to your domain on Chrome Web Store.
  allowWebstorePublishUnverified: TYPE_BOOL
    true: Allow users to publish private hosted apps even if the domain name of the app's {print "launch_web_url"} or {print "app_url"} is not owned by the organization.
    false: Do not allow users to publish private hosted apps if the domain name of the app's {print "launch_web_url"} or {print "app_url"} is not owned by the organization.

chrome.users.appsconfig.ExtensionInstallTypeBlocklist: Blocklist for install types of extensions.
  extensionInstallTypeBlocklist: TYPE_LIST
    command_line: Command line.

chrome.users.appsconfig.ExtensionUnpublishedAvailability: Chrome Web Store unpublished extensions.
  extensionUnpublishedAvailability: TYPE_ENUM
    ALLOW_UNPUBLISHED: Allow unpublished extensions.
    DISABLE_UNPUBLISHED: Disable unpublished extensions.

chrome.users.appsconfig.FullRestoreEnabled: Restore apps on startup.
  fullRestoreEnabled: TYPE_BOOL
    true: Restore all apps and app windows.
    false: Only restore Chrome browser.
  fullRestoreMode: TYPE_ENUM
    ASK_EVERY_TIME: Ask user every time.
    ALWAYS: Always restore.
    DO_NOT_RESTORE: Do not restore.

chrome.users.appsconfig.GhostWindowEnabled: Android ghost windows.
  ghostWindowEnabled: TYPE_BOOL
    true: Create ghost windows while restoring Android apps.
    false: Do not create ghost windows while restoring Android apps.

chrome.users.appsconfig.HideWebStoreIcon: Chrome Web Store app icon.
  hideWebStoreIcon: TYPE_BOOL
    true: Do not show the Chrome Web Store icon in the ChromeOS launcher or on the new tab page.
    false: Show the Chrome Web Store icon in the ChromeOS launcher and on the new tab page.

chrome.users.appsconfig.PinCreateApps: Pin Create apps.
  pinCreateApps: TYPE_LIST
    canvas: Canvas.
    cursive: Cursive.
    projector: Screencast.
    media: Gallery.
    camera: Camera.

chrome.users.appsconfig.ReportAndroidStatus: Android reporting for users and devices.
  reportArcStatusEnabled: TYPE_BOOL
    true: Enable Android reporting.
    false: Disable Android reporting.

chrome.users.appsconfig.UnaffiliatedDeviceArcAllowed: Android apps on unaffiliated devices.
  unaffiliatedDeviceArcAllowed: TYPE_BOOL
    true: Allow users on unaffiliated devices to use Android apps.
    false: Do not allow users on unaffiliated devices to use Android apps.

chrome.users.AppStoreRatingEnabled: iOS App Store Rating promo.
  appStoreRatingEnabled: TYPE_BOOL
    true: Allow the App Store Rating promo to be displayed.
    false: Do not allow the App Store Rating promo to be displayed.

chrome.users.ArcAppToWebAppSharingEnabled: Sharing from Android apps to Web apps.
  arcAppToWebAppSharingEnabled: TYPE_BOOL
    true: Enable Android to Web Apps sharing.
    false: Disable Android to Web Apps sharing.

chrome.users.ArcOpenLinksInBrowserByDefault: Open links in Chrome browser by default.
  arcOpenLinksInBrowserByDefault: TYPE_BOOL
    true: Open links in Chrome browser by default.
    false: Open links in Android apps by default.

chrome.users.ArcVmDataMigrationStrategy: Android VM Update.
  arcVmDataMigrationStrategy: TYPE_ENUM
    DO_NOT_PROMPT: Do not allow users to manually update Android apps.
    PROMPT: Allow users to manually update Android apps.

chrome.users.AssistantWebEnabled: Allow using Google Assistant on the web.
  assistantWebEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not allow using Google Assistant on the web.
    TRUE: Allow using Google Assistant on the web.

chrome.users.AudioCaptureAllowedUrls: Audio input allowed URLs.
  audioCaptureAllowedUrls: TYPE_LIST
    URL patterns to allow. URLs that will be granted access to the audio input device without a prompt. Prefix domain with [*.] to include subdomains.

chrome.users.AudioInput: Audio input (microphone).
  audioCaptureAllowed: TYPE_BOOL
    true: Prompt user to allow each time.
    false: Disable audio input.

chrome.users.AudioOutput: Audio output.
  audioOutputAllowed: TYPE_BOOL
    true: Enable audio output.
    false: Disable audio output.

chrome.users.AudioProcessHighPriorityEnabled: Audio process priority.
  audioProcessHighPriorityEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Use normal priority for the Chrome audio process.
    TRUE: Use high priority for the Chrome audio process.

chrome.users.AudioSandboxEnabled: Audio sandbox.
  audioSandboxEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Never sandbox the audio process.
    TRUE: Always sandbox the audio process.

chrome.users.AuthAndroidNegotiateAccountType: Account type for HTTP Negotiate authentication.
  authAndroidNegotiateAccountType: TYPE_STRING
    Account type. Specifies the account type of the accounts provided by the Android authentication app that supports HTTP Negotiate authentication. If no setting is provided, HTTP Negotiate authentication is disabled on Android.

chrome.users.AuthenticationServerAllowlist: Integrated authentication servers.
  authServerAllowlist: TYPE_LIST
    Allowed authentication servers. Enter a list of servers for integrated authentication.

chrome.users.AuthenticationServerDelegationAllowlist: Kerberos delegation servers.
  authNegotiateDelegateAllowlist: TYPE_LIST
    Allowed servers for delegation. Enter a list of servers that Chrome may delegate to for Kerberos authentication.

chrome.users.AuthSchemes: Supported authentication schemes.
  authSchemes: TYPE_LIST
    basic: Basic.
    digest: Digest.
    ntlm: NTLM.
    negotiate: Negotiate.

chrome.users.AutoclickEnabled: Auto-click enabled.
  autoclickEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable auto-click.
    TRUE: Enable auto-click.

chrome.users.AutofillAddressEnabled: Address form autofill.
  autofillAddressEnabled: TYPE_BOOL
    true: Allow user to configure.
    false: Never Autofill address forms.

chrome.users.AutofillCreditCardEnabled: Credit card form autofill.
  autofillCreditCardEnabled: TYPE_BOOL
    true: Allow user to configure.
    false: Never Autofill credit card forms.

chrome.users.AutofillPredictionSettings: Autofill with AI.
  autofillPredictionSettings: TYPE_ENUM
    ALLOWED: Allow autofill prediction and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow autofill prediction without improving AI models.
    DISABLED: Do not allow autofill prediction.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.AutomaticFullscreen: Automatic fullscreen.
  automaticFullscreenAllowedForUrls: TYPE_LIST
    Allow automatic fullscreen on these sites. Supersedes users' personal settings and allows matching origins to call the API without a prior user gesture.
  automaticFullscreenBlockedForUrls: TYPE_LIST
    Block automatic fullscreen on these sites. Supersedes users' personal settings and blocks matching origins from calling the API without a prior user gesture.

chrome.users.AutoOpen: Auto open downloaded files.
  autoOpenAllowedForUrls: TYPE_LIST
    Auto open URLs. If this policy is set, only downloads that match these URLs and have an auto open type will be auto opened. If this policy is left unset, all downloads matching an auto open type will be auto opened. Wildcards ("*") are allowed when appended to a URL, but cannot be entered alone.
  autoOpenFileTypes: TYPE_LIST
    Auto open files types. Do not include the leading separator when listing the type. For example, use "txt", not ".txt".

chrome.users.AutoplayAllowlist: Autoplay video.
  autoplayAllowlist: TYPE_LIST
    Allowed URLs. URL patterns allowed to autoplay. Prefix domain with [*.] to include all subdomains. Use * to allow all domains.

chrome.users.AutoUpdateCheckPeriodNew: Auto-update check period.
  autoUpdateCheckPeriodMinutesNew: TYPE_INT64

chrome.users.AutoUpdateCheckPeriodNewV2: Auto-update check period.
  autoUpdateCheckPeriodMinutesNew: TYPE_INT64

chrome.users.Avatar: Custom avatar.
  userAvatarImage
    downloadUri: TYPE_STRING

chrome.users.BackForwardCacheEnabled: Back-forward cache.
  backForwardCacheEnabled: TYPE_BOOL
    true: Enable the back-forward cache.
    false: Disable the back-forward cache.

chrome.users.BackgroundModeEnabled: Background mode.
  backgroundModeEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable background mode.
    TRUE: Enable background mode.
  backgroundModeEnabledCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.BasicAuthOverHttpEnabled: Allow Basic authentication for HTTP.
  basicAuthOverHttpEnabled: TYPE_BOOL
    true: Basic authentication scheme is allowed on HTTP connections.
    false: HTTPS is required to use Basic authentication scheme.

chrome.users.BatterySaverModeAvailability: Battery Saver Mode.
  batterySaverModeAvailability: TYPE_ENUM
    DISABLED: Disable Battery Saver Mode.
    ENABLED_BELOW_THRESHOLD: Enable when the device is on battery power and battery level is low.
    ENABLED_ON_BATTERY: (deprecated) Enable when the device is on battery power.
    UNSET: End user can control this setting.
  batterySaverModeAvailabilitySettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.BeforeunloadEventCancelByPreventDefaultEnabled: Behavior of event.preventDefault() for beforeunload event.
  beforeunloadEventCancelByPreventDefaultEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not show cancel dialog when event.preventDefault() is called for beforeunload event.
    TRUE: Show cancel dialog when event.preventDefault() is called for beforeunload event.

chrome.users.BlockTruncatedCookies: Block truncated cookies.
  blockTruncatedCookies: TYPE_BOOL
    true: Block truncated cookies.
    false: Allow truncated cookies.

chrome.users.BookmarkBarEnabled: Bookmark bar.
  bookmarkBarEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable bookmark bar.
    TRUE: Enable bookmark bar.
  bookmarkBarPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.BookmarkEditing: Bookmark editing.
  editBookmarksEnabled: TYPE_BOOL
    true: Enable bookmark editing.
    false: Disable bookmark editing.

chrome.users.BoundSessionCredentialsEnabled: Device Bound Session Credentials.
  boundSessionCredentialsEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable Device Bound Session Credentials.
    TRUE: Enable Device Bound Session Credentials.

chrome.users.BrowserAddPersonEnabled: Add profiles.
  browserAddPersonEnabled: TYPE_BOOL
    true: Enable adding new profiles.
    false: Disable adding new profiles.

chrome.users.BrowserGuestModeEnabled: Browser guest mode.
  browserGuestModeEnabled: TYPE_BOOL
    true: Allow guest browser logins.
    false: Prevent guest browser logins.
  browserGuestModeEnforced: TYPE_BOOL
    true: Only allow guest browser logins.
    false: Allow guest browser logins and profile logins.

chrome.users.BrowserHistory: Browser history.
  savingBrowserHistoryDisabled: TYPE_BOOL
    true: Never save browser history.
    false: Always save browser history.

chrome.users.BrowserIdleTimeout: Browser idle timeout.
  idleTimeout: TYPE_INT64
  idleTimeoutActions: TYPE_LIST
    close_browsers: Close Browsers.
    show_profile_picker: Show Profile Picker.
    clear_browsing_history: Clear Browsing History.
    clear_download_history: Clear Download History.
    clear_cookies_and_other_site_data: Clear Cookies and Other Site Data.
    clear_cached_images_and_files: Clear Cached Images and Files.
    clear_password_signin: Clear Password Signin.
    clear_autofill: Clear Autofill.
    clear_site_settings: Clear Site Settings.
    clear_hosted_app_data: Clear Hosted App Data.
    reload_pages: Reload Pages.

chrome.users.BrowserLabsEnabled: Browser experiments icon in toolbar.
  browserLabsEnabled: TYPE_BOOL
    true: Allow users to access browser experimental features through an icon in the toolbar.
    false: Do not show browser experimental features icon in the toolbar.

chrome.users.BrowserLegacyExtensionPointsBlocked: Browser Legacy Extension Points.
  browserLegacyExtensionPointsBlocked: TYPE_BOOL
    true: Block legacy extension points in the Browser process.
    false: Do not block legacy extension points in the Browser process.

chrome.users.BrowserNetworkTimeQueriesEnabled: Google time service.
  browserNetworkTimeQueriesEnabled: TYPE_BOOL
    true: Allow queries to a Google server to retrieve an accurate timestamp.
    false: Do not allow queries to Google servers to retrieve timestamps.

chrome.users.BrowserSignin: Browser sign-in settings.
  browserSignin: TYPE_ENUM
    DISABLE: Disable browser sign-in.
    ENABLE: Enable browser sign-in.
    FORCE: Force users to sign-in to use the browser.

chrome.users.BrowserSwitcher: Legacy Browser Support.
  browserSwitcherEnabled: TYPE_BOOL
    true: Enable Legacy Browser Support.
    false: Disable Legacy Browser Support.

chrome.users.BrowserSwitcherChromeParameters: Chrome parameters.
  browserSwitcherChromeParameters: TYPE_LIST
    Command-line parameters. Windows-only. Parameters for launching Chrome from the alternative browser. If a parameter contains {"${url}"}, it gets replaced with the URL. Otherwise, the URL is appended at the end of the command line.

chrome.users.BrowserSwitcherChromePath: Chrome path.
  browserSwitcherChromePath: TYPE_STRING
    Path to the Chrome executable. Windows-only. Path to the Chrome executable to launch when switching from the alternative browser to Chrome. If unset, the alternative browser will auto-detect the path to Chrome.

chrome.users.BrowserSwitcherDelayDuration: Delay before launching alternative browser.
  browserSwitcherDelayDuration: TYPE_INT64

chrome.users.BrowserSwitcherDelayDurationV2: Delay before launching alternative browser.
  browserSwitcherDelayDuration: TYPE_INT64

chrome.users.BrowserSwitcherExternalGreylistUrl: URL to list of websites to open in either browser.
  browserSwitcherExternalGreylistUrl: TYPE_STRING
    URL to site list XML file. Specifies the URL to an XML file that contains a list of sites that can be opened in either Chrome or the alternative browser for Legacy Browser Support.

chrome.users.BrowserSwitcherExternalSitelistUrl: Legacy Browser Support site list.
  browserSwitcherExternalSitelistUrl: TYPE_STRING
    URL to site list XML file. Specifies the URL to an XML file that contains a list of sites to be used with Legacy Browser Support.

chrome.users.BrowserSwitcherKeepLastChromeTab: Keep last Chrome tab.
  browserSwitcherKeepLastChromeTab: TYPE_BOOL
    true: Keep at least one Chrome tab open.
    false: Close Chrome completely.

chrome.users.BrowserSwitcherParsingMode: Sitelist parsing mode.
  browserSwitcherParsingMode: TYPE_ENUM
    DEFAULT: Default.
    IE_SITE_LIST_MODE: Enterprise Mode IE/Edge compatible.

chrome.users.BrowserSwitcherUrlGreylist: Websites to open in either browser.
  browserSwitcherUrlGreylist: TYPE_LIST
    URLs to websites to open in either browser. Specifies the list of websites that can be opened in either Chrome or the alternative browser.

chrome.users.BrowserSwitcherUrlList: Websites to open in alternative browser.
  browserSwitcherUrlList: TYPE_LIST
    URLs to websites to open in alternative browser. Specifies the list of websites that should be opened in the alternative browser.

chrome.users.BrowserSwitcherUseIeSitelist: Use Internet Explorer site list.
  browserSwitcherUseIeSitelist: TYPE_BOOL
    true: Use Internet Explorer's SiteList policy as a source of rules.
    false: Do not use Internet Explorer's SiteList policy as a source of rules.

chrome.users.BrowserThemeColor: Custom theme color.
  browserThemeColor: TYPE_STRING
    Hex color. Enter a valid hex color, for instance #FFFFFF.

chrome.users.BrowsingDataLifetime: Browsing Data Lifetime.
  browsingHistoryTtl: TYPE_INT64
  downloadHistoryTtl: TYPE_INT64
  cookiesAndOtherSiteDataTtl: TYPE_INT64
  cachedImagesAndFilesTtl: TYPE_INT64
  passwordSigninTtl: TYPE_INT64
  autofillTtl: TYPE_INT64
  siteSettingsTtl: TYPE_INT64
  hostedAppDataTtl: TYPE_INT64

chrome.users.BrowsingDataLifetimeV2: Browsing Data Lifetime.
  browsingHistoryTtl: TYPE_INT64
  downloadHistoryTtl: TYPE_INT64
  cookiesAndOtherSiteDataTtl: TYPE_INT64
  cachedImagesAndFilesTtl: TYPE_INT64
  passwordSigninTtl: TYPE_INT64
  autofillTtl: TYPE_INT64
  siteSettingsTtl: TYPE_INT64
  hostedAppDataTtl: TYPE_INT64

chrome.users.BuiltInDnsClientEnabled: Built-in DNS client.
  builtInDnsClientEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never use the built-in DNS client.
    TRUE: Always use the built-in DNS client if available.

chrome.users.CaCertificateManagementAllowed: User management of installed CA certificates.
  caCertificateManagementAllowed: TYPE_ENUM
    ALL: Allow users to manage all certificates.
    USER_ONLY: Allow users to manage user certificates.
    NONE: Disallow users from managing certificates.

chrome.users.CalendarIntegrationEnabled: Google Calendar Integration.
  calendarIntegrationEnabled: TYPE_BOOL
    true: Enable Google Calendar Integration.
    false: Disable Google Calendar Integration.

chrome.users.CaPlatformIntegrationEnabled: Use user-added TLS certificates from platform trust stores for server authentication.
  caPlatformIntegrationEnabled: TYPE_BOOL
    true: Include user-added TLS server certificates.
    false: Do not include user-added TLS server certificates.

chrome.users.CaptivePortalAuthenticationIgnoresProxy: Ignore proxy on captive portals.
  captivePortalAuthenticationIgnoresProxy: TYPE_BOOL
    true: Ignore policies for captive portal pages.
    false: Keep policies for captive portal pages.

chrome.users.CaretHighlightEnabled: Caret highlight.
  caretHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable caret highlight.
    TRUE: Enable caret highlight.

chrome.users.Cecpq2Enabled: CECPQ2 post-quantum key-agreement for TLS.
  cecpq2Enabled: TYPE_BOOL
    true: Enable default CECPQ2 rollout process.
    false: Disable CECPQ2.

chrome.users.CertificateSynchronization: Certificate synchronization.
  arcCertificatesSyncMode: TYPE_ENUM
    SYNC_DISABLED: Disable usage of ChromeOS CA Certificates in Android apps.
    COPY_CA_CERTS: Enable usage of ChromeOS CA Certificates in Android apps.

chrome.users.CertificateTransparencyEnforcementDisabledForUrls: Allowed certificate transparency URLs.
  certificateTransparencyEnforcementDisabledForUrls: TYPE_LIST
    Allowed certificate transparency URLs. Any URL listed will be exempt from Certificate Transparency enforcement. Learn more at https://cloud.google.com/docs/chrome-enterprise/policies/?policy=CertificateTransparencyEnforcementDisabledForUrls.

chrome.users.CertTransparencyCas: Certificate transparency CA allowlist.
  certificateTransparencyEnforcementDisabledForCas: TYPE_LIST
    Certificate transparency CA allowlist. Any subjectPublicKeyInfo hashes listed will be exempt from Certificate Transparency enforcement. These hashes must be listed in a particular format. Learn more at https://cloud.google.com/docs/chrome-enterprise/policies/?policy=CertificateTransparencyEnforcementDisabledForCas.

chrome.users.CertTransparencyLegacyCas: Certificate transparency legacy CA allowlist.
  certificateTransparencyEnforcementDisabledForLegacyCas: TYPE_LIST
    Certificate transparency legacy CA allowlist. Any subjectPublicKeyInfo hashes listed will be exempt from Certificate Transparency enforcement. These hashes must be listed in a particular format and must match a recognized Legacy Certificate Authority. Enter Learn more at https://cloud.google.com/docs/chrome-enterprise/policies/?policy=CertificateTransparencyEnforcementDisabledForLegacyCas.

chrome.users.ChromeAppsWebViewPermissiveBehaviorAllowed: Restore permissive Chrome Apps behavior.
  chromeAppsWebViewPermissiveBehaviorAllowed: TYPE_BOOL
    true: Allow permissive behavior.
    false: Use default navigation protections.

chrome.users.ChromeBrowserDmtokenDeletionEnabled: Device Token Management.
  chromeBrowserDmtokenDeletionEnabled: TYPE_BOOL
    true: Delete Token.
    false: Invalidate Token.

chrome.users.ChromeBrowserUpdates: Chrome browser updates.
  rollbackToTargetVersionEnabled: TYPE_ENUM
    ROLLBACK_TO_TARGET_VERSION_DISABLED: Do not rollback to target version.
    ROLLBACK_TO_TARGET_VERSION_ENABLED: Rollback to target version.
  targetVersionPrefixSetting: TYPE_STRING
    Target version prefix. Specifies which version the Chrome browser should be updated to. When a value is set, Chrome will be updated to the version prefixed with this value. For example, if the value is '55.', Chrome will be updated to any minor version of 55 (e.g. 55.24.34.0 or 55.60.2.10). If the value is '55.2.', Chrome will be updated to any minor version of 55.2 (e.g. 55.2.34.100 or 55.2.2.1). If the value is '55.24.34.1', Chrome will be updated to that specific version only. Chrome may stop updating or not rollback if the specified version is more than three major milestones old.
  updateSetting: TYPE_ENUM
    UPDATES_ENABLED: Allow updates.
    AUTOMATIC_UPDATES_ONLY: Allow updates when Chrome checks for them automatically.
    MANUAL_UPDATES_ONLY: Allow updates when the user checks for them manually.
    UPDATES_DISABLED: Disable updates.
  targetChannelSetting: TYPE_ENUM
    STABLE: Stable channel.
    DEV: Dev channel.
    BETA: Beta channel.
    EXTENDED_STABLE: Extended stable channel.

chrome.users.ChromeCleanupEnabled: Chrome Cleanup.
  chromeCleanupEnabled: TYPE_BOOL
    true: Allow Chrome Cleanup to periodically scan the system and allow manual scans.
    false: Prevent Chrome Cleanup from periodical scans and disallow manual scans.
  chromeCleanupReportingEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Results from a Chrome Cleanup are never shared with Google.
    TRUE: Results from a Chrome Cleanup are always shared with Google.

chrome.users.ChromeForTestingAllowed: Chrome for Testing.
  chromeForTestingAllowed: TYPE_BOOL
    true: Allow use of the Chrome for Testing.
    false: Do not allow use of the Chrome for Testing.

chrome.users.ChromeOnIos: Chrome on iOS.
  enableIosChromePolicies: TYPE_BOOL
    true: Apply supported user settings to Chrome on iOS.
    false: Do not apply supported user settings to Chrome on iOS.

chrome.users.ChromeRootStoreEnabled: Chrome Root Store and certificate verifier.
  chromeRootStoreEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not use the Chrome Root Store.
    TRUE: Use the Chrome Root Store.

chrome.users.ClearBrowserHistory: Clear browser history.
  allowDeletingBrowserHistory: TYPE_BOOL
    true: Allow clearing history in settings menu.
    false: Do not allow clearing history in settings menu.

chrome.users.ClickToCall: Click to Call.
  clickToCallEnabledTristate: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not allow users to send phone numbers from Chrome to their phone.
    TRUE: Allow users to send phone numbers from Chrome to their phone.

chrome.users.ClientCertificateManagementAllowed: User management of installed client certificates.
  clientCertificateManagementAllowed: TYPE_ENUM
    ALL: Allow users to manage all certificates.
    USER_ONLY: Allow users to manage user certificates.
    NONE: Disallow users from managing certificates.

chrome.users.ClientCertificates: Client certificates.
  autoSelectCertificateForUrls: TYPE_LIST
    Automatically select for these sites. If a site matching a pattern specified here requests a client certificate, Chrome will automatically select one for it. More information and example values can be found in https://support.google.com/chrome/a/answer/2657289#AutoSelectCertificateForUrls.

chrome.users.ClipboardSettings: Clipboard.
  defaultClipboardSetting: TYPE_ENUM
    BLOCK_CLIPBOARD: Do not allow any site to use the clipboard site permission.
    ASK_CLIPBOARD: Allow sites to ask the user to grant the clipboard site permission.
    UNSET: Allow the user to decide.
  clipboardAllowedForUrls: TYPE_LIST
    Allow these sites to access the clipboard. Urls to allow clipboard access.
  clipboardBlockedForUrls: TYPE_LIST
    Block these sites from accessing the clipboard. Urls to block clipboard access.

chrome.users.CloudApAuthEnabled: Azure Cloud Authentication.
  cloudApAuthEnabled: TYPE_ENUM
    DISABLED: Disable Azure cloud authentication.
    ENABLED: Enable Azure cloud authentication.

chrome.users.CloudProfileReportingEnabled: Managed profile reporting.
  cloudProfileReportingEnabled: TYPE_BOOL
    true: Enable managed profile reporting for managed users.
    false: Disable managed profile reporting for managed users.

chrome.users.CloudReporting: Managed browser reporting.
  cloudReportingEnabled: TYPE_BOOL
    true: Enable managed browser cloud reporting.
    false: Disable managed browser cloud reporting.

chrome.users.CloudReportingUploadFrequency: Managed browser reporting upload frequency.
  cloudReportingUploadFrequency: TYPE_INT64

chrome.users.CloudReportingUploadFrequencyV2: Managed browser reporting upload frequency.
  cloudReportingUploadFrequency: TYPE_INT64

chrome.users.CloudUserPolicyMerge: User cloud policy merge.
  cloudUserPolicyMerge: TYPE_BOOL
    true: Merge user cloud policies with machine policies.
    false: Do not merge user cloud policies with machine policies.

chrome.users.ColorCorrectionEnabled: Color Correction.
  colorCorrectionEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable color correction accessibility.
    TRUE: Enable color correction accessibility.
  colorCorrectionEnabledSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.CommandLineFlagSecurityWarningsEnabled: Command-line flags.
  commandLineFlagSecurityWarningsEnabled: TYPE_BOOL
    true: Show security warnings when potentially dangerous command-line flags are used.
    false: Hide security warnings when potentially dangerous command-line flags are used.

chrome.users.ComponentUpdates: Component updates.
  componentUpdatesEnabled: TYPE_BOOL
    true: Enable updates for all components.
    false: Disable updates for components.

chrome.users.CompressionDictionaryTransportEnabled: Compression dictionary transport support.
  compressionDictionaryTransportEnabled: TYPE_BOOL
    true: Allow to use previous responses as compression dictionaries for future requests.
    false: Do not allow to use compression dictionary transport.

chrome.users.ConnectorsEnabled: Allow enterprise connectors.
  connectorsEnabled: TYPE_BOOL
    true: Allow users to enable Enterprise Connectors.
    false: Do not allow  users to enable Enterprise Connectors.

chrome.users.ContextMenuPhotoSharingSettings: Google Photos in iOS context menu.
  contextMenuPhotoSharingSettings: TYPE_ENUM
    ENABLED: Allow sharing to Google Photos in the context menu.
    DISABLED: Prevent sharing to Google Photos in the context menu.

chrome.users.ContextualGoogleIntegrationsEnabled: Contextual integrations of Google services.
  contextualGoogleIntegrationsEnabled: TYPE_BOOL
    true: Allow integrations.
    false: Disable integrations.
  contextualGoogleIntegrationsConfiguration: TYPE_LIST
    GoogleCalendar: Google Calendar.
    GoogleClassroom: Google Classroom.
    GoogleTasks: Google Tasks.

chrome.users.ContextualSearchEnabled: Touch to search.
  contextualSearchEnabled: TYPE_BOOL
    true: Allow users to use touch to search.
    false: Disable touch to search.

chrome.users.Cookies: Cookies.
  cookiesAllowedForUrls: TYPE_LIST
    Allow cookies for URL patterns. Urls to allow cookies.
  defaultCookiesSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_COOKIES: Allow cookies.
    BLOCK_COOKIES: Block cookies.
    SESSION_ONLY: Session only.
  cookiesBlockedForUrls: TYPE_LIST
    Block Cookies for URL Patterns. Urls to block cookies.
  cookiesSessionOnlyForUrls: TYPE_LIST
    Allow session-only cookies for URL patterns. Urls to allow session-only cookies.

chrome.users.CorsNonWildcardRequestHeadersSupport: CORS non-wildcard request headers support.
  corsNonWildcardRequestHeadersSupport: TYPE_BOOL
    true: Support CORS non-wildcard request headers.
    false: Do not support CORS non-wildcard request headers.

chrome.users.CpuTaskScheduler: CPU task scheduler.
  schedulerConfiguration: TYPE_ENUM
    USER_CHOICE: Allow the user to decide.
    CONSERVATIVE: Optimize for stability.
    PERFORMANCE: Optimize for performance.
  cpuTaskSchedulerPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.CreatePasskeysInICloudKeychain: iCloud Keychain.
  createPasskeysInICloudKeychain: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Default to creating passkeys in other stores (such as the Google Chrome profile).
    TRUE: Default to creating passkeys in iCloud Keychain when possible.

chrome.users.CreateThemesSettings: Create themes with AI.
  createThemesSettings: TYPE_ENUM
    ALLOWED: Allow create themes and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow create themes without improving AI models.
    DISABLED: Do not allow create themes.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.CredentialProviderPromoEnabled: Credential provider extension promo.
  credentialProviderPromoEnabled: TYPE_BOOL
    true: Allow the Credential Provider Extension promo to be displayed.
    false: Do not allow the Credential Provider Extension promo to be displayed.

chrome.users.CrossOriginAuthentication: Cross-origin authentication.
  allowCrossOriginAuthPrompt: TYPE_BOOL
    true: Allow cross-origin authentication.
    false: Block cross-origin authentication.

chrome.users.CrossOriginWebAssemblyModuleSharingEnabled: Allow WebAssembly cross-origin.
  crossOriginWebAssemblyModuleSharingEnabled: TYPE_BOOL
    true: Allow WebAssembly modules to be sent cross-origin.
    false: Prevent WebAssembly modules to be sent cross-origin.

chrome.users.CssCustomStateDeprecatedSyntaxEnabled: CSS custom state deprecated syntax.
  cssCustomStateDeprecatedSyntaxEnabled: TYPE_BOOL
    true: Allow deprecated syntax.
    false: Do not allow deprecated syntax.

chrome.users.CursorHighlightEnabled: Cursor highlight.
  cursorHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable cursor highlight.
    TRUE: Enable cursor highlight.

chrome.users.CustomTermsOfService: Custom terms of service.
  termsOfServiceUrl
    downloadUri: TYPE_STRING

chrome.users.DataCompressionProxy: Data compression proxy.
  dataCompressionProxyEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Always disable data compression proxy.
    TRUE: Always enable data compression proxy.

chrome.users.DataLeakPreventionReportingEnabled: Data controls reporting.
  dataLeakPreventionReportingEnabled: TYPE_BOOL
    true: Enable reporting of data control events.
    false: Disable reporting of data control events.

chrome.users.DataUrlInSvgUseEnabled: Data URL support for SVGUseElement.
  dataUrlInSvgUseEnabled: TYPE_BOOL
    true: Enable Data URL support in SVGUseElement.
    false: Disable Data URL support in SVGUseElement.

chrome.users.DataUrlWhitespacePreservationEnabled: Data URL whitespace preservation for all media types.
  dataUrlWhitespacePreservationEnabled: TYPE_BOOL
    true: Keep whitespace for all mime-types.
    false: Only keep whitespace for text and xml mime-types.

chrome.users.DefaultBrowserSettingEnabled: Default browser check.
  defaultBrowserSettingEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Prevent Chrome from checking if it is the default browser and turn off user controls to make it the default browser.
    TRUE: Attempt to register Chrome as the default browser during startup if it is not already.

chrome.users.DefaultInsecureContentSetting: Control use of insecure content exceptions.
  defaultInsecureContentSetting: TYPE_ENUM
    BLOCK_INSECURE_CONTENT: Do not allow any site to load blockable mixed content.
    ALLOW_EXCEPTIONS_INSECURE_CONTENT: Allow users to add exceptions to allow blockable mixed content.

chrome.users.DefaultPrintColor: Default color printing mode.
  printingColorDefault: TYPE_ENUM
    COLOR: Color.
    MONOCHROME: Black and white.

chrome.users.DefaultPrintDuplexMode: Default page sides.
  printingDuplexDefault: TYPE_ENUM
    SIMPLEX: One-sided.
    SHORT_EDGE_DUPLEX: Short-edge two-sided printing.
    LONG_EDGE_DUPLEX: Long-edge two-sided printing.

chrome.users.DefaultPrinters: Print preview default.
  specifyDefaultPrinter: TYPE_BOOL
    true: Define the default printer.
    false: Use default print behavior.
  printerTypes: TYPE_ENUM
    CLOUD_AND_LOCAL: Cloud and local.
    CLOUD: Cloud only.
    LOCAL: Local only.
  printerMatching: TYPE_ENUM
    MATCH_BY_NAME: Match by name.
    MATCH_BY_ID: Match by ID.
  defaultPrinterPattern: TYPE_STRING
    Default printer. Enter a regular expression that matches the desired default printer selection. The print preview will default to the first printer to match the regular expression. For example, to match a printer named "Initech Lobby", use "Initech Lobby". To match any of {print "initech-lobby-1"}, {print "initech-lobby-2"}, etc. you could use {print "initech-lobby-.$"}. To match {print "initech-lobby-guest"} or {print "initech-partner-guest"}, you could use {print "initech-.*-guest"}.

chrome.users.DefaultSensorsSetting: Sensors.
  defaultSensorsSetting: TYPE_ENUM
    ALLOW_SENSORS: Allow sites to access sensors.
    BLOCK_SENSORS: Do not allow any site to access sensors.
    UNSET: Allow the user to decide if a site may access sensors.
  sensorsAllowedForUrls: TYPE_LIST
    Allow access to sensors on these sites. For detailed information on valid url patterns, please see https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  sensorsBlockedForUrls: TYPE_LIST
    Block access to sensors on these sites. For detailed information on valid url patterns, please see https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns Note: using only the "*" wildcard is not valid.

chrome.users.DeleteKeyModifier: Control the shortcut used to trigger the Delete "six pack" key.
  deleteKeyModifier: TYPE_ENUM
    NONE: Setting a shortcut for the "Delete" action is disabled.
    ALT: Delete shortcut setting uses the shortcut that contains the alt modifier.
    SEARCH: Delete shortcut setting uses the shortcut that contains the search modifier.
  deleteKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.DeletePrintJobHistoryAllowed: Print job history deletion.
  deletePrintJobHistoryAllowed: TYPE_BOOL
    true: Allow print job history to be deleted.
    false: Do not allow print job history to be deleted.

chrome.users.DeletingUndecryptablePasswordsEnabled: Delete undecryptable passwords.
  deletingUndecryptablePasswordsEnabled: TYPE_BOOL
    true: Enable deleting undecryptable passwords.
    false: Disable deleting undecryptable passwords.

chrome.users.DeskApi: Desk API for third-party ChromeOS desk control.
  deskApiThirdPartyAccessEnabled: TYPE_BOOL
    true: Enable Desk API for third-party ChromeOS desk control.
    false: Do not enable Desk API for third-party ChromeOS desk control.
  deskApiThirdPartyAllowlist: TYPE_LIST
    Enable Desk API for a list of third-party domains. Specifies an allowlist of third-party domains for which Desk API is enabled.

chrome.users.DesktopSharingHubEnabled: Desktop sharing in the omnibox and 3-dot menu.
  desktopSharingHubEnabled: TYPE_BOOL
    true: Enable desktop sharing hub.
    false: Disable desktop sharing hub.

chrome.users.DeveloperTools: Developer tools.
  developerToolsAvailability: TYPE_ENUM
    ALWAYS_ALLOW_DEVELOPER_TOOLS: Always allow use of built-in developer tools.
    ALLOW_DEVELOPER_TOOLS_EXCEPT_FORCE_INSTALLED: Allow use of built-in developer tools except for force-installed extensions and component extensions.
    NEVER_ALLOW_DEVELOPER_TOOLS: Never allow use of built-in developer tools.
  extensionDeveloperModeSettings: TYPE_ENUM
    UNSET: Use 'developer tools availability' selection.
    ALLOW: Allow use of developer tools on extensions page.
    DISALLOW: Do not allow use of developer tools on extensions page.

chrome.users.DeviceEnrollment: Device enrollment.
  autoDevicePlacementEnabled: TYPE_BOOL
    true: Place Chrome device in user organization.
    false: Keep Chrome device in current location.

chrome.users.DevicePowerAdaptiveChargingEnabled: Adaptive charging model.
  devicePowerAdaptiveChargingEnabled: TYPE_BOOL
    true: Enable adaptive charging model.
    false: Disable adaptive charging model.

chrome.users.DevToolsGenAiSettings: DevTools AI features.
  devToolsGenAiSettings: TYPE_ENUM
    ALLOWED: Allow DevTools Generative AI features and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow DevTools Generative AI features without improving AI models.
    DISABLED: Do not allow DevTools Generative AI features.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.DictationEnabled: Dictation.
  dictationEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable dictation.
    TRUE: Enable dictation.

chrome.users.DisableSafeBrowsingProceedAnyway: Disable bypassing Safe Browsing warnings.
  disableSafeBrowsingProceedAnyway: TYPE_BOOL
    true: Do not allow user to bypass Safe Browsing warning.
    false: Allow user to bypass Safe Browsing warning.

chrome.users.DiskCacheDir: Disk cache directory.
  diskCacheDir: TYPE_STRING
    Disk cache directory. Sets the disk cache directory.

chrome.users.DiskCacheSize: Disk cache size.
  diskCacheSize: TYPE_INT64
    Disk cache size in bytes. Sets the disk cache size in bytes.

chrome.users.DisplayCapturePermissionsPolicyEnabled: Insecure Media Capture.
  displayCapturePermissionsPolicyEnabled: TYPE_BOOL
    true: Deny insecure requests to access display.
    false: Allow requests to access display from non-allowlisted contexts.

chrome.users.DnsInterceptionChecksEnabled: DNS interception checks enabled.
  dnsInterceptionChecksEnabled: TYPE_BOOL
    true: Perform DNS interception checks.
    false: Do not perform DNS interception checks.

chrome.users.DnsOverHttps: DNS over HTTPS.
  dnsOverHttpsMode: TYPE_ENUM
    OFF: Disable DNS over HTTPS.
    AUTOMATIC: Prefer DNS over HTTPS, allow insecure fallback.
    SECURE: Require DNS over HTTPS.
    UNSET: Use system default behavior.
  dnsOverHttpsTemplates: TYPE_LIST
    DNS over HTTPS templates. URI templates of desired DNS over HTTPS resolvers. If the URI template contains a '{?dns}' variable, requests to the resolver will use GET; otherwise requests will use POST.

chrome.users.DnsOverHttpsDomainConfig: DNS over HTTPS included and excluded domains.
  dnsOverHttpsExcludedDomains: TYPE_LIST
    DNS over HTTPS excluded domains. List of fully qualified domain names (FQDN) or domain suffixes noted using a special wildcard prefix '*' to be resolved without using DNS over HTTPS.
  dnsOverHttpsIncludedDomains: TYPE_LIST
    DNS over HTTPS included domains. List of fully qualified domain names (FQDN) or domain suffixes noted using a special wildcard prefix '*' to be resolved using DNS over HTTPS.

chrome.users.DnsOverHttpsTemplatesWithIdentifiers: DNS-over-HTTPS with identifiers.
  dnsOverHttpsSalt: TYPE_STRING
    Salt for hashing identifiers in the URI templates. Salt used for hashing user and device identifiers in the template URIs. Optional starting Chrome version 114.
  dnsOverHttpsTemplatesWithIdentifiers: TYPE_LIST
    DNS-over-HTTPS templates with identifiers. URI templates of desired DNS-over-HTTPS resolvers which contain user or device identifiers. If the URI template contains a '{?dns}' variable, requests to the resolver will use GET; otherwise requests will use POST. If both DNS-over-HTTPS templates and DNS-over-HTTPS templates with identifiers are set, ChromeOS will default to DNS-over-HTTPS templates with identifiers.

chrome.users.DomainReliabilityAllowed: Allow reporting of domain reliability related data.
  domainReliabilityAllowed: TYPE_BOOL
    true: Domain Reliability data may be sent to Google depending on Chrome User Metrics (UMA) policy.
    false: Never send domain reliability data to Google.
  domainReliabilityAllowedSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.DownloadBubbleEnabled: Download bubble.
  downloadBubbleEnabled: TYPE_BOOL
    true: Enable download bubble.
    false: Disable download bubble.

chrome.users.DownloadManagerSaveToDriveSettings: Save files directly to Google Drive.
  downloadManagerSaveToDriveSettings: TYPE_ENUM
    ENABLED: The download manager will have an option to save files to Google Drive.
    DISABLED: The download manager will not have an option to save files to Google Drive.

chrome.users.DownloadPreference: Cacheable URLs.
  downloadPreference: TYPE_ENUM
    NO_PREFERENCE: No preference.
    CACHEABLE: Attempt to provide cache-friendly download URLs.

chrome.users.DownloadRestrictions: Download restrictions.
  safeBrowsingDownloadRestrictions: TYPE_ENUM
    NO_SPECIAL_RESTRICTIONS: No special restrictions.
    BLOCK_ALL_MALICIOUS_DOWNLOAD: Block malicious downloads.
    BLOCK_DANGEROUS_DOWNLOAD: Block malicious downloads and dangerous file types.
    BLOCK_POTENTIALLY_DANGEROUS_DOWNLOAD: Block malicious downloads, uncommon or unwanted downloads and dangerous file types.
    BLOCK_ALL_DOWNLOAD: Block all downloads.
  downloadRestrictionsPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.DriveFileSyncAvailable: ChromeOS file sync.
  driveFileSyncAvailable: TYPE_ENUM
    DISABLED: Do not show the ChromeOS file sync feature.
    VISIBLE: Show the ChromeOS file sync feature.

chrome.users.DynamicCodeSettings: Dynamic Code.
  dynamicCodeSettings: TYPE_ENUM
    DEFAULT: Use the default Chrome setting.
    DISABLED_FOR_BROWSER: Do not create dynamic code.

chrome.users.EcheAllowed: App Streaming.
  echeAllowed: TYPE_BOOL
    true: Allow users to launch App Streaming.
    false: Do not allow users to launch App Streaming.

chrome.users.EmojiPickerGifSupportEnabled: GIF Support in Emoji Picker.
  emojiPickerGifSupportEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow GIFs to be selected in the Emoji picker.
    TRUE: Allow GIFs to be selected in the Emoji picker.

chrome.users.EmojiSuggestionEnabled: Emoji suggestions.
  emojiSuggestionEnabled: TYPE_BOOL
    true: Enable emoji suggestions when users type.
    false: Disable emoji suggestions when users type.

chrome.users.EnableCaptureAllowedSettings: Screen video capture allowed by sites.
  screenCaptureAllowedByOrigins: TYPE_LIST
    Allow tab, window, and desktop video capture by these sites. Sites set in this list will be ignored in the 'screenCaptureAllowed' field.
  windowCaptureAllowedByOrigins: TYPE_LIST
    Allow tab and window video capture by these sites. Sites set in this list will be ignored in the 'screenCaptureAllowedByOrigins' and 'screenCaptureAllowed' fields.
  tabCaptureAllowedByOrigins: TYPE_LIST
    Allow tab video capture by these sites. Sites set in this list will be ignored in the 'windowCaptureAllowedByOrigins', 'screenCaptureAllowedByOrigins', and 'screenCaptureAllowed' fields.
  sameOriginTabCaptureAllowedByOrigins: TYPE_LIST
    Allow tab video capture (same site only) by these sites. Sites set in this list will be ignored in the 'tabCaptureAllowedByOrigins', 'windowCaptureAllowedByOrigins', 'screenCaptureAllowedByOrigins', and 'screenCaptureAllowed' fields.

chrome.users.EnableDeprecatedPrivetPrinting: Deprecated privet printing.
  enableDeprecatedPrivetPrinting: TYPE_BOOL
    true: Enable deprecated privet printing.
    false: Disable deprecated privet printing.

chrome.users.EncryptedClientHelloEnabled: TLS encrypted ClientHello.
  encryptedClientHelloEnabled: TYPE_BOOL
    true: Enable the TLS Encrypted ClientHello experiment.
    false: Disable the TLS Encrypted ClientHello experiment.

chrome.users.EnforceLocalAnchorConstraintsEnabled: Enforce local anchor constraints.
  enforceLocalAnchorConstraintsEnabled: TYPE_BOOL
    true: Enforce constraints in locally added trust anchors.
    false: Do not enforce constraints in locally added trust anchors.

chrome.users.EnhancedNetworkVoicesInSelectToSpeakAllowed: Select-to-speak.
  enhancedNetworkVoicesInSelectToSpeakAllowed: TYPE_BOOL
    true: Allow sending text to Google servers for enhanced Select-to-speak.
    false: Do not allow sending text to Google servers for enhanced Select-to-speak.

chrome.users.EnrollPermission: Enrollment permissions.
  deviceEnrollPermission: TYPE_ENUM
    ALLOW_ENROLL_RE_ENROLL: Allow users in this organization to enroll new or re-enroll existing devices.
    ALLOW_RE_ENROLL: Only allow users in this organization to re-enroll existing devices (cannot enroll new or deprovisioned devices).
    DISALLOW_ENROLL_RE_ENROLL: Do not allow users in this organization to enroll new or re-enroll existing devices.

chrome.users.EnterpriseCustomLabel: Organization name.
  enterpriseCustomLabel: TYPE_STRING
    Organization name shown in the toolbar chip. A label used to brand your managed browsers. It will be shown in the toolbar and in the management menu. This label is not localized and will be truncated with an ellipsis after 16 characters.

chrome.users.EnterpriseHardwarePlatformApiEnabled: Enterprise Hardware Platform API.
  enterpriseHardwarePlatformApiEnabled: TYPE_BOOL
    true: Allow managed extensions to use the Enterprise Hardware Platform API.
    false: Do not allow managed extensions to use the Enterprise Hardware Platform API.

chrome.users.EnterpriseLogoUrl: Organization Icon URL.
  enterpriseLogoUrl: TYPE_STRING
    A URL to an icon used to brand your managed browsers and profiles. A URL to an image that will be used to brand your managed profiles and browsers. This icon will be used in various places in the browser to customize it for your organization. A 48x48 icon with a transparent background is recommended. Accepted formats include png, jpg, ico. Please test Chrome UI before deploying.

chrome.users.EnterpriseProfileBadgeToolbarSettings: Enterprise profile badge toolbar settings.
  enterpriseProfileBadgeToolbarSettings: TYPE_ENUM
    SHOW_ENTERPRISE_TOOLBAR_BADGE: Show expanded enterprise toolbar badge.
    HIDE_ENTERPRISE_TOOLBAR_BADGE: Hide expanded enterprise toolbar badge.

chrome.users.EventPathEnabled: Re-enable the Event.path API until Chrome 115.
  eventPathEnabled: TYPE_ENUM
    UNSET: Enable Event.path API until Chrome 108.
    FALSE: Disable Event.path API.
    TRUE: Enable Event.path API until Chrome 115.

chrome.users.ExplicitlyAllowedNetworkPorts: Allowed network ports.
  explicitlyAllowedNetworkPorts: TYPE_LIST
    554: port 554 (expires 2021/10/15).
    989: port 989 (expires 2022/02/01).
    990: port 990 (expires 2022/02/01).
    6566: port 6566 (expires 2021/10/15).
    10080: port 10080 (expires 2022/04/01).

chrome.users.ExtensibleEnterpriseSsoBlocklist: Extensible Enterprise SSO blocking.
  extensibleEnterpriseSsoBlocklist: TYPE_LIST
    all: All identity providers.
    microsoft: Microsoft cloud identity provider.

chrome.users.ExtensionExtendedBackgroundLifetimeForPortConnectionsToUrls: Extended background lifetime.
  extensionExtendedBackgroundLifetimeForPortConnectionsToUrls: TYPE_LIST
    Origins that grant extended background lifetime to connecting extensions. Enter a list of origins. Extensions that connect to one of these origins will be be kept running as long as the port is connected. One URL per line.

chrome.users.ExtensionManifestVTwoAvailability: Manifest V2 extension availability.
  extensionManifestVTwoAvailability: TYPE_ENUM
    DEFAULT: Default browser behavior.
    DISABLE: Disable manifest V2 extensions.
    ENABLE: Enable manifest V2 extensions.
    ENABLE_FOR_FORCED_EXTENSIONS: Enable force-installed manifest V2 extensions.

chrome.users.ExternalProtocolDialogShowAlwaysOpenCheckbox: Show "Always open" checkbox in external protocol dialog.
  externalProtocolDialogShowAlwaysOpenCheckbox: TYPE_BOOL
    true: User may select "Always allow" to skip all future confirmation prompts.
    false: User may not select "Always allow" and will be prompted each time.

chrome.users.ExternalStorage: External storage devices.
  externalStorageDevices: TYPE_ENUM
    READ_WRITE: Allow read and write access to all external storage devices.
    READ_ONLY: Allow read only access to all external storage devices.
    DISALLOW: Do not allow read and write access to external storage devices.
  externalStorageAllowlist: TYPE_LIST
    Specify devices to always have read and write access. USB devices which are allowlisted for read and write access. To identify a specific device, enter colon separated hexadecimal pairs of USB Vendor Identifier and Product Identifier.

chrome.users.FastPairEnabled: Fast Pair (fast Bluetooth pairing).
  fastPairEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable Fast Pair.
    TRUE: Enable Fast Pair.

chrome.users.FeedbackSurveysEnabled: Google Chrome surveys.
  feedbackSurveysEnabled: TYPE_BOOL
    true: Enable in-product surveys.
    false: Disable in-product surveys.

chrome.users.FElevenKeyModifier: Control the shortcut used to trigger F11.
  fElevenKeyModifier: TYPE_ENUM
    DISABLED: F11 settings are disabled.
    ALT: F11 settings use the shortcut that contains the alt modifier.
    SHIFT: F11 settings use the shortcut that contains the shift modifier.
    CTRL_SHIFT: F11 settings use the shortcut that contains the modifiers ctrl and shift.
  fElevenKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.FetchKeepaliveDurationSecondsOnShutdown: Keepalive duration.
  fetchKeepaliveDurationSecondsOnShutdown: TYPE_INT64

chrome.users.FetchKeepaliveDurationSecondsOnShutdownV2: Keepalive duration.
  fetchKeepaliveDurationSecondsOnShutdown: TYPE_INT64

chrome.users.FileOrDirectoryPickerWithoutGestureAllowedForOrigins: File/directory picker without user gesture.
  fileOrDirectoryPickerWithoutGestureAllowedForOrigins: TYPE_LIST
    Allow file or directory picker APIs to be called without prior user gesture. Urls to allow file or directory pickers without user gesture.

chrome.users.FilePickerChooseFromDriveSettings: Google Drive in file selection menu.
  filePickerChooseFromDriveSettings: TYPE_ENUM
    ENABLED: Show Google Drive option.
    DISABLED: Hide Google Drive option.

chrome.users.FileSystemRead: File system read access.
  defaultFileSystemReadGuardSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ASK_FILE_SYSTEM_READ: Allow sites to ask the user to grant read access to files and directories.
    BLOCK_FILE_SYSTEM_READ: Do not allow sites to request read access to files and directories.
  fileSystemReadAskForUrls: TYPE_LIST
    Allow file system read access on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  fileSystemReadBlockedForUrls: TYPE_LIST
    Block read access on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.

chrome.users.FileSystemSyncAccessHandleAsyncInterfaceEnabled: File System Access API async interface.
  fileSystemSyncAccessHandleAsyncInterfaceEnabled: TYPE_BOOL
    true: Re-enable the deprecated async interface for FileSystemSyncAccessHandle.
    false: Disable the deprecated async interface for FileSystemSyncAccessHandle.

chrome.users.FileSystemWrite: File system write access.
  defaultFileSystemWriteGuardSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ASK_FILE_SYSTEM_WRITE: Allow sites to ask the user to grant write access to files and directories.
    BLOCK_FILE_SYSTEM_WRITE: Do not allow sites to request write access to files and directories.
  fileSystemWriteAskForUrls: TYPE_LIST
    Allow write access to files and directories on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  fileSystemWriteBlockedForUrls: TYPE_LIST
    Block write access to files and directories on these sites. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.

chrome.users.FirstPartySetsEnabled: First-Party Sets.
  firstPartySetsEnabled: TYPE_BOOL
    true: Enable First-Party Sets for all affected users.
    false: Disable First-Party Sets for all affected users.

chrome.users.FocusModeSoundsEnabled: Sounds in Focus Mode.
  focusModeSoundsEnabled: TYPE_ENUM
    ENABLED: All sounds play in Focus Mode.
    FOCUS_SOUNDS: Only Focus Sounds play in Focus Mode.
    DISABLED: Disable all sounds in Focus Mode.

chrome.users.ForcedLanguages: Preferred languages.
  forcedLanguages: TYPE_LIST
    af: Afrikaans.
    sq: Albanian - ‪shqip‬.
    am: Amharic - ‪አማርኛ‬.
    ar: Arabic - ‫العربية‬.
    an: Aragonese.
    hy: Armenian - ‪հայերեն‬.
    as: Assamese - ‪অসমীয়া‬.
    ast: Asturian - ‪asturianu‬.
    az: Azerbaijani - ‪azərbaycan‬.
    bn: Bangla - ‪বাংলা‬.
    eu: Basque - ‪euskara‬.
    be: Belarusian - ‪беларуская‬.
    bs: Bosnian - ‪bosanski‬.
    br: Breton - ‪brezhoneg‬.
    bg: Bulgarian - ‪български‬.
    my: Burmese - ‪မြန်မာ‬.
    ca: Catalan - ‪català‬.
    ceb: Cebuano.
    ckb: Central Kurdish - ‫کوردیی ناوەندی‬.
    chr: Cherokee - ‪ᏣᎳᎩ‬.
    zh: Chinese - ‪中文‬.
    zh-HK: Chinese (Hong Kong) - ‪中文（香港）‬.
    zh-CN: Chinese (Simplified) - ‪简体中文‬.
    zh-TW: Chinese (Traditional) - ‪繁體中文‬.
    co: Corsican.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en: English.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-IN: English (India).
    en-NZ: English (New Zealand).
    en-ZA: English (South Africa).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    eo: Esperanto.
    et: Estonian - ‪eesti‬.
    fo: Faroese - ‪føroyskt‬.
    fil: Filipino.
    fi: Finnish - ‪Suomi‬.
    fr: French - ‪Français‬.
    fr-CA: French (Canada) - ‪Français (Canada)‬.
    fr-FR: French (France) - ‪Français (France)‬.
    fr-CH: French (Switzerland) - ‪Français (Suisse)‬.
    gl: Galician - ‪galego‬.
    ka: Georgian - ‪ქართული‬.
    de: German - ‪Deutsch‬.
    de-AT: German (Austria) - ‪Deutsch (Österreich)‬.
    de-DE: German (Germany) - ‪Deutsch (Deutschland)‬.
    de-LI: German (Liechtenstein) - ‪Deutsch (Liechtenstein)‬.
    de-CH: German (Switzerland) - ‪Deutsch (Schweiz)‬.
    el: Greek - ‪Ελληνικά‬.
    gn: Guarani.
    gu: Gujarati - ‪ગુજરાતી‬.
    ht: Haitian Creole - ‪Créole haïtien‬.
    ha: Hausa.
    haw: Hawaiian - ‪ʻŌlelo Hawaiʻi‬.
    iw: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hmn: Hmong.
    hu: Hungarian - ‪magyar‬.
    is: Icelandic - ‪íslenska‬.
    ig: Igbo.
    id: Indonesian - ‪Indonesia‬.
    ia: Interlingua - ‪interlingua‬.
    ga: Irish - ‪Gaeilge‬.
    it: Italian - ‪Italiano‬.
    it-IT: Italian (Italy) - ‪Italiano (Italia)‬.
    it-CH: Italian (Switzerland) - ‪Italiano (Svizzera)‬.
    ja: Japanese - ‪日本語‬.
    jv: Javanese - ‪Jawa‬.
    kn: Kannada - ‪ಕನ್ನಡ‬.
    kk: Kazakh - ‪қазақ тілі‬.
    km: Khmer - ‪ខ្មែរ‬.
    rw: Kinyarwanda - ‪Ikinyarwanda‬.
    kok: Konkani - ‪कोंकणी‬.
    ko: Korean - ‪한국어‬.
    ku: Kurdish - ‪kurdî [kurmancî]‬.
    ky: Kyrgyz - ‪кыргызча‬.
    lo: Lao - ‪ລາວ‬.
    la: Latin.
    lv: Latvian - ‪latviešu‬.
    ln: Lingala - ‪lingála‬.
    lt: Lithuanian - ‪lietuvių‬.
    lb: Luxembourgish - ‪Lëtzebuergesch‬.
    mk: Macedonian - ‪македонски‬.
    mg: Malagasy.
    ms: Malay - ‪Melayu‬.
    ml: Malayalam - ‪മലയാളം‬.
    mt: Maltese - ‪Malti‬.
    mi: Māori.
    mr: Marathi - ‪मराठी‬.
    mn: Mongolian - ‪монгол‬.
    ne: Nepali - ‪नेपाली‬.
    no: Norwegian - ‪norsk‬.
    nn: Norwegian Nynorsk - ‪norsk nynorsk‬.
    ny: Nyanja.
    oc: Occitan - ‪occitan‬.
    or: Odia - ‪ଓଡ଼ିଆ‬.
    om: Oromo - ‪Oromoo‬.
    ps: Pashto - ‫پښتو‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt: Portuguese - ‪Português‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    pa: Punjabi - ‪ਪੰਜਾਬੀ‬.
    qu: Quechua - ‪Runasimi‬.
    ro: Romanian - ‪română‬.
    rm: Romansh - ‪rumantsch‬.
    ru: Russian - ‪Русский‬.
    sm: Samoan.
    gd: Scottish Gaelic - ‪Gàidhlig‬.
    sr: Serbian - ‪српски‬.
    sn: Shona - ‪chiShona‬.
    sd: Sindhi - ‫سنڌي‬.
    si: Sinhala - ‪සිංහල‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    so: Somali - ‪Soomaali‬.
    st: Southern Sotho - ‪Sesotho‬.
    es: Spanish - ‪Español‬.
    es-AR: Spanish (Argentina) - ‪Español (Argentina)‬.
    es-CL: Spanish (Chile) - ‪Español (Chile)‬.
    es-CO: Spanish (Colombia) - ‪Español (Colombia)‬.
    es-CR: Spanish (Costa Rica) - ‪Español (Costa Rica)‬.
    es-HN: Spanish (Honduras) - ‪Español (Honduras)‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es-MX: Spanish (Mexico) - ‪Español (México)‬.
    es-PE: Spanish (Peru) - ‪Español (Perú)‬.
    es-ES: Spanish (Spain) - ‪Español (España)‬.
    es-US: Spanish (United States) - ‪Español (Estados Unidos)‬.
    es-UY: Spanish (Uruguay) - ‪Español (Uruguay)‬.
    es-VE: Spanish (Venezuela) - ‪Español (Venezuela)‬.
    su: Sundanese - ‪Basa Sunda‬.
    sw: Swahili - ‪Kiswahili‬.
    sv: Swedish - ‪Svenska‬.
    tg: Tajik - ‪тоҷикӣ‬.
    ta: Tamil - ‪தமிழ்‬.
    tt: Tatar - ‪татар‬.
    te: Telugu - ‪తెలుగు‬.
    th: Thai - ‪ไทย‬.
    ti: Tigrinya - ‪ትግርኛ‬.
    to: Tongan - ‪lea fakatonga‬.
    tn: Tswana - ‪Setswana‬.
    tr: Turkish - ‪Türkçe‬.
    tk: Turkmen - ‪türkmen dili‬.
    uk: Ukrainian - ‪Українська‬.
    ur: Urdu - ‫اردو‬.
    ug: Uyghur - ‫ئۇيغۇرچە‬.
    uz: Uzbek - ‪o‘zbek‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    wa: Walloon.
    cy: Welsh - ‪Cymraeg‬.
    fy: Western Frisian - ‪Frysk‬.
    wo: Wolof.
    xh: Xhosa - ‪IsiXhosa‬.
    yi: Yiddish - ‫ייִדיש‬.
    yo: Yoruba - ‪Èdè Yorùbá‬.
    zu: Zulu - ‪isiZulu‬.

chrome.users.ForceEnablePepperVideoDecoderDevApi: PPB_VideoDecoder(Dev) API support.
  forceEnablePepperVideoDecoderDevApi: TYPE_BOOL
    true: Enable PPB_VideoDecoder(Dev) API.
    false: Let the browser decide.

chrome.users.ForceEphemeralMode: Force ephemeral mode.
  forceEphemeralProfiles: TYPE_BOOL
    true: Erase all local user data.
    false: Do not erase local user data.

chrome.users.ForceMajorVersionToMinorPositionInUserAgent: Freeze User-Agent string version.
  forceMajorVersionToMinorPositionInUserAgent: TYPE_ENUM
    DEFAULT: Default to browser settings for User-Agent string.
    FORCE_DISABLED: Do not freeze the major version.
    FORCE_ENABLED: Freeze the major version as 99.

chrome.users.ForceMaximizeOnFirstRun: Maximize window on first run.
  forceMaximizeOnFirstRun: TYPE_BOOL
    true: Maximize the first browser window on first run.
    false: Default system behavior (depends on screen size).

chrome.users.ForcePermissionPolicyUnloadDefaultEnabled: Unload event handlers.
  forcePermissionPolicyUnloadDefaultEnabled: TYPE_BOOL
    true: Enable unload event handlers.
    false: Do not enable unload event handlers.

chrome.users.FTwelveKeyModifier: Control the shortcut used to trigger F12.
  fTwelveKeyModifier: TYPE_ENUM
    DISABLED: F12 settings are disabled.
    ALT: F12 settings use the shortcut that contains the alt modifier.
    SHIFT: F12 settings use the shortcut that contains the shift modifier.
    CTRL_SHIFT: F12 settings use the shortcut that contains the modifiers ctrl and shift.
    UNSET: Allow the user to decide.
  fTwelveKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.FullscreenAlertEnabled: Fullscreen alert.
  fullscreenAlertEnabled: TYPE_BOOL
    true: Enable fullscreen alert when waking the device.
    false: Disable fullscreen alert when waking the device.

chrome.users.FullscreenAllowed: Fullscreen mode.
  fullscreenAllowed: TYPE_BOOL
    true: Allow fullscreen mode.
    false: Do not allow fullscreen mode.

chrome.users.GaiaLockScreenOfflineSigninTimeLimitDays: Google online unlock frequency.
  gaiaLockScreenOfflineSigninTimeLimitDays: TYPE_INT64

chrome.users.GaiaOfflineSigninTimeLimitDays: Google online login frequency.
  gaiaOfflineSigninTimeLimitDays: TYPE_INT64

chrome.users.GeminiSettings: Gemini integration.
  geminiSettings: TYPE_ENUM
    ENABLED: Allow Gemini integrations.
    DISABLED: Do not allow Gemini integrations.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.GenAiDefaultSettings: Generative AI policy defaults.
  genAiDefaultSettings: TYPE_ENUM
    ALLOWED: Allow GenAI features and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow GenAI features without improving AI models.
    DISABLED: Do not allow GenAI features.

chrome.users.GenAiLocalFoundationalModelSettings: Local foundational model settings.
  genAiLocalFoundationalModelSettings: TYPE_ENUM
    ALLOWED: Download model automatically.
    DISABLED: Do not download model.

chrome.users.GenAiVcBackgroundSettings: Video conference background settings.
  genAiVcBackgroundSettings: TYPE_ENUM
    ALLOWED: Allow Generative AI VC background and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow Generative AI VC background without improving AI models.
    DISABLED: Do not allow Generative AI VC background.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.GenAiWallpaperSettings: Wallpaper settings.
  genAiWallpaperSettings: TYPE_ENUM
    ALLOWED: Allow Generative AI wallpaper and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow Generative AI wallpaper without improving AI models.
    DISABLED: Do not allow Generative AI wallpaper.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.Geolocation: Geolocation.
  defaultGeolocationSetting: TYPE_ENUM
    ALLOW_GEOLOCATION: Allow sites to detect users' geolocation.
    BLOCK_GEOLOCATION: Do not allow sites to detect users' geolocation.
    ASK_GEOLOCATION: Always ask the user if a site wants to detect their geolocation.
    USER_CHOICE: Allow the user to decide.

chrome.users.GloballyScopeHttpAuthCacheEnabled: Globally scoped HTTP authentication cache.
  globallyScopeHttpAuthCacheEnabled: TYPE_BOOL
    true: HTTP authentication credentials entered in the context of one site will automatically be used in the context of another.
    false: HTTP authentication credentials are scoped to top-level sites.

chrome.users.GoogleCast: Cast.
  showCastIconInToolbar: TYPE_BOOL
    true: Always show the Cast icon in the toolbar.
    false: Do not show the Cast icon in the toolbar by default, but let users choose.
  enableMediaRouter: TYPE_BOOL
    true: Allow users to Cast.
    false: Do not allow users to Cast.
  mediaRouterCastAllowAllIps: TYPE_ENUM
    UNSET: Enable restrictions, unless the CastAllowAllIPs feature is turned on.
    FALSE: Enable restrictions.
    TRUE: Disable restrictions (allow all IP addresses).

chrome.users.GoogleDriveSyncing: Google Drive syncing.
  driveDisabledBool: TYPE_BOOL
    true: Disable Google Drive syncing.
    false: Enable Google Drive syncing.

chrome.users.GoogleDriveSyncingOverCellular: Google Drive syncing over cellular.
  driveDisabledOverCellular: TYPE_BOOL
    true: Disable Google Drive syncing over cellular connections.
    false: Enable Google Drive syncing over cellular connections.

chrome.users.GoogleSearchSidePanelEnabled: Side Panel search.
  googleSearchSidePanelEnabled: TYPE_BOOL
    true: Enable Side Panel search on all web pages.
    false: Disable Side Panel search on all web pages.

chrome.users.GssapiLibraryName: GSSAPI library name.
  gssapiLibraryName: TYPE_STRING
    Library name or full path. Specify which GSSAPI library to use for HTTP authentication. You can set either just a library name, or a full path. Leave empty for default.

chrome.users.HardwareAccelerationModeEnabled: GPU.
  hardwareAccelerationModeEnabled: TYPE_BOOL
    true: Enable graphics acceleration.
    false: Disable graphics acceleration.

chrome.users.HelpMeReadSettings: Help me read.
  helpMeReadSettings: TYPE_ENUM
    ALLOWED: Allow help me read and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow help me read without improving AI models.
    DISABLED: Do not allow help me read.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.HelpMeWriteSettings: Help me write.
  helpMeWriteSettings: TYPE_ENUM
    ALLOWED: Allow help me write and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow help me write without improving AI models.
    DISABLED: Do not allow help me write.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.HighContrastEnabled: High contrast.
  highContrastEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable high contrast.
    TRUE: Enable high contrast.

chrome.users.HighEfficiencyModeEnabled: High efficiency mode.
  highEfficiencyModeEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable high efficiency mode.
    TRUE: Enable high efficiency mode.

chrome.users.HistorySearchSettings: History search settings.
  historySearchSettings: TYPE_ENUM
    ALLOWED: Allow AI history search and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow AI history search without improving AI models.
    DISABLED: Do not allow AI history search.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.HomeAndEndKeysModifier: Control the shortcut used to trigger the Home/End "six pack" keys.
  homeAndEndKeysModifier: TYPE_ENUM
    NONE: Home/End settings are disabled.
    ALT: Home/End settings use the shortcut that contains the alt modifier.
    SEARCH: Home/End settings use the shortcut that contains the search modifier.
  homeAndEndKeysModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.HomeButton: Home button.
  showHomeButton: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never show "Home" button.
    TRUE: Always show "Home" button.
  homeButtonPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.Homepage: Homepage.
  homepageIsNewTabPage: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Homepage is always the URL set in 'homepageLocation'.
    TRUE: Homepage is always the new tab page.
  homepageLocation: TYPE_STRING
    Homepage URL. Specifies the URL that should be used as the home page in managed Chrome.
  homepagePolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.HstsPolicyBypassList: HSTS policy bypass list.
  hstsPolicyBypassList: TYPE_LIST
    List of hostnames that will bypass the HSTS policy check . Enter a list of hostnames that will be exempt from the HSTS policy check.

chrome.users.HttpAllowlist: HTTP Allowlist.
  httpAllowlist: TYPE_LIST
    Allowed HTTP URLs. Configures support of HTTPS allowlist.

chrome.users.HttpsOnlyMode: Allow HTTPS-Only Mode to be enabled.
  httpsOnlyMode: TYPE_ENUM
    USER_CHOICE: Allow users to enable HTTPS-Only Mode.
    DISALLOWED: Do not allow users to enable HTTPS-Only Mode.
    FORCE_ENABLED: Force enable HTTPS-Only Mode.

chrome.users.HttpsUpgradesEnabled: Automatic HTTPS upgrades.
  httpsUpgradesEnabled: TYPE_BOOL
    true: Allow HTTPS upgrades.
    false: Do not allow HTTPS upgrades.

chrome.users.IdleSettingsExtended: Idle settings.
  lidCloseAction: TYPE_ENUM
    SLEEP: Sleep.
    LOGOUT: Logout.
    SHUTDOWN: Shutdown.
    DO_NOTHING: Do nothing.
  idleDelayAc: TYPE_INT64
  idleWarningDelayAc: TYPE_INT64
  idleActionAc: TYPE_ENUM
    SLEEP: Sleep.
    LOGOUT: Logout.
    SHUTDOWN: Shut down.
    DO_NOTHING: Do nothing.
  screenDimDelayAc: TYPE_INT64
  screenOffDelayAc: TYPE_INT64
  screenLockDelayAc: TYPE_INT64
  idleDelayBattery: TYPE_INT64
  idleWarningDelayBattery: TYPE_INT64
  idleActionBattery: TYPE_ENUM
    SLEEP: Sleep.
    LOGOUT: Logout.
    SHUTDOWN: Shut down.
    DO_NOTHING: Do nothing.
  screenDimDelayBattery: TYPE_INT64
  screenOffDelayBattery: TYPE_INT64
  screenLockDelayBattery: TYPE_INT64
  lockOnSleepOrLidClose: TYPE_ENUM
    UNSET: Allow user to configure.
    FALSE: Don't lock screen.
    TRUE: Lock screen.

chrome.users.Images: Images.
  defaultImagesSettings: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_IMAGES: Allow all sites to show all images.
    BLOCK_IMAGES: Do not allow any site to show images.
  imagesAllowedForUrls: TYPE_LIST
    Show images on these sites. Urls to allow images.
  imagesBlockedForUrls: TYPE_LIST
    Block images on these sites. Urls to block images.

chrome.users.ImportAutofillFormData: Import autofill data.
  importAutofillFormData: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable imports of autofill data.
    TRUE: Enable imports of autofill data.
  importAutofillFormDataCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.ImportBookmarks: Import bookmarks.
  importBookmarks: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable imports of bookmarks.
    TRUE: Enable imports of bookmarks.
  importBookmarksCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.ImportHistory: Import browsing history.
  importHistory: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable imports of browsing history.
    TRUE: Enable imports of browsing history.
  importHistoryCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.ImportHomepage: Import homepage.
  importHomepage: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable imports of homepage.
    TRUE: Enable imports of homepage.

chrome.users.ImportSavedPasswords: Import saved passwords.
  importSavedPasswords: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable imports of saved passwords.
    TRUE: Enable imports of saved passwords.
  importSavedPasswordsCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.ImportSearchEngine: Import search engines.
  importSearchEngine: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable imports of search engines.
    TRUE: Enable imports of search engines.
  importSearchEngineCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.InactiveBrowserDeletion: Inactive period for browser deletion.
  inactiveBrowserTtlDays: TYPE_INT64
    Number of days. Shortening this period can cause more enrolled browsers to be considered inactive and, therefore, be irreversibly deleted. Before lowering the value of this policy, make sure you understand the impact. The allowable range is 28-730 days.

chrome.users.InactivePeriodForProfileDeletion: Inactive period for profile deletion.
  inactiveProfileTtlDays: TYPE_INT64
    Inactive period for profile deletion. Shortening this period can cause more managed profiles to be considered inactive and, therefore, be deleted. Before lowering the value of this policy, make sure you understand the impact. The allowable range is 28-730 days.

chrome.users.IncognitoMode: Incognito mode.
  incognitoModeAvailability: TYPE_ENUM
    AVAILABLE: Allow incognito mode.
    UNAVAILABLE: Disallow incognito mode.
    FORCED: Force incognito mode.

chrome.users.InsecureContentAllowedForUrls: Allow insecure content on these sites.
  insecureContentAllowedForUrls: TYPE_LIST
    URL patterns to allow. Specifies which sites should allow insecure (HTTP) content to be shown.

chrome.users.InsecureContentBlockedForUrls: Block insecure content on these sites.
  insecureContentBlockedForUrls: TYPE_LIST
    URL patterns to block. Specifies which sites should block insecure (HTTP) content from being shown.

chrome.users.InsecureFormsWarningsEnabled: Insecure forms.
  insecureFormsWarningsEnabled: TYPE_BOOL
    true: Show warnings and disable autofill on insecure forms.
    false: Do not show warnings or disable autofill on insecure forms.

chrome.users.InsecureHashesInTlsHandshakesEnabled: Insecure hashes in TLS handshakes.
  insecureHashesInTlsHandshakesEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow insecure hashes in TLS handshakes.
    TRUE: Allow insecure hashes in TLS handshakes.

chrome.users.InsecurePrivateNetworkRequestsAllowed: Requests from insecure websites to more-private network endpoints.
  insecurePrivateNetworkRequestsAllowed: TYPE_BOOL
    true: Insecure websites are allowed to make requests to any network endpoint.
    false: Allow the user to decide.
  insecurePrivateNetworkRequestsAllowedForUrls: TYPE_LIST
    URL patterns to allow. Network requests to more-private endpoints, from insecure origins not covered by the patterns specified here, will use the global default value.

chrome.users.InsertKeyModifier: Control the shortcut used to trigger the Insert "six pack" key.
  insertKeyModifier: TYPE_ENUM
    NONE: Setting a shortcut for the "Insert" action is disabled.
    SEARCH: Insert shortcut setting uses the shortcut that contains the search modifier.
  insertKeyModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.InstantTetheringAllowed: Instant Tethering.
  instantTetheringAllowed: TYPE_BOOL
    true: Allow users to use Instant Tethering.
    false: Do not allow users to use Instant Tethering.

chrome.users.IntegratedWebAuthenticationAllowed: Login credentials for network authentication.
  integratedWebAuthenticationAllowed: TYPE_BOOL
    true: Use login credentials for network authentication to a managed proxy.
    false: Don't use login credentials for network authentication.

chrome.users.IntensiveWakeUpThrottlingEnabled: Javascript IntensiveWakeUpThrottling.
  intensiveWakeUpThrottlingEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Force no throttling of background JavaScript timers.
    TRUE: Force throttling of background JavaScript timers.

chrome.users.IntranetRedirectBehavior: Intranet Redirection Behavior.
  intranetRedirectBehavior: TYPE_ENUM
    DEFAULT: Use default browser behavior.
    DISABLE_INTERCEPTION_CHECKS_DISABLE_INFOBAR: Disable DNS interception checks and did-you-mean "http://intranetsite/" infobars.
    DISABLE_INTERCEPTION_CHECKS_ENABLE_INFOBAR: Disable DNS interception checks; allow did-you-mean "http://intranetsite/" infobars.
    ENABLE_INTERCEPTION_CHECKS_ENABLE_INFOBAR: Allow DNS interception checks and did-you-mean "http://intranetsite/" infobars.

chrome.users.IpVersionSixReachabilityOverride: IPv6 reachability check override.
  ipVersionSixReachabilityOverride: TYPE_BOOL
    true: Override the IPv6 reachability check.
    false: Do not override the IPv6 reachability check.

chrome.users.Javascript: JavaScript.
  defaultJavascriptSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_JAVASCRIPT: Allow sites to run JavaScript.
    BLOCK_JAVASCRIPT: Do not allow any site to run JavaScript.
  javascriptAllowedForUrls: TYPE_LIST
    Allow these sites to run JavaScript. Urls to allow JavaScript.
  javascriptBlockedForUrls: TYPE_LIST
    Block JavaScript on these sites. Urls to block JavaScript.

chrome.users.JavaScriptJitSettings: JavaScript JIT.
  defaultJavaScriptJitSetting: TYPE_ENUM
    ALLOW_JAVA_SCRIPT_JIT: Allow sites to run JavaScript JIT.
    BLOCK_JAVA_SCRIPT_JIT: Do not allow sites to run JavaScript JIT.
  javaScriptJitAllowedForSites: TYPE_LIST
    Allow JavaScript to use JIT on these sites. Specifies the site allowlist for JavaScript to use JIT.
  javaScriptJitBlockedForSites: TYPE_LIST
    Block JavaScript from using JIT on these sites. Specifies the site blocklist for JavaScript to be blocked from using JIT.

chrome.users.KeepFullscreenWithoutNotificationUrlAllowList: Fullscreen after unlock.
  keepFullscreenWithoutNotificationUrlAllowList: TYPE_LIST
    Keep full screen after unlock without warning for the following URLs. Enter a list of URL patterns, one per line.

chrome.users.KerberosAddAccountsAllowed: Kerberos accounts.
  kerberosAddAccountsAllowed: TYPE_BOOL
    true: Allow users to add Kerberos accounts.
    false: Do not allow users to add Kerberos accounts.

chrome.users.KerberosCustomPrefilledConfigSettingGroup: Kerberos ticket default configuration.
  kerberosCustomPrefilledConfig: TYPE_STRING
    Custom configuration. Kerberos ticket prefilled config.
  kerberosUseCustomPrefilledConfig: TYPE_BOOL
    true: Customize Kerberos configuration.
    false: Use recommended Kerberos configuration.

chrome.users.KerberosDomainAutocomplete: Autocomplete Kerberos domain.
  kerberosDomainAutocomplete: TYPE_STRING
    Kerberos domain. Autocomplete Kerberos domain.

chrome.users.KerberosRememberPasswordEnabled: Remember Kerberos passwords.
  kerberosRememberPasswordEnabled: TYPE_BOOL
    true: Allow users to remember Kerberos passwords.
    false: Do not allow users to remember Kerberos passwords.

chrome.users.KerberosServicePrincipalName: Kerberos service principal name.
  disableAuthNegotiateCnameLookup: TYPE_BOOL
    true: Use original name entered.
    false: Use canonical DNS name.

chrome.users.KerberosSpnPort: Kerberos SPN port.
  enableAuthNegotiatePort: TYPE_BOOL
    true: Include non-standard port.
    false: Do not include non-standard port.

chrome.users.KerberosTicketDelegation: Kerberos ticket delegation.
  authNegotiateDelegateByKdcPolicy: TYPE_BOOL
    true: Respect KDC policy.
    false: Ignore KDC policy.

chrome.users.KerberosTickets: Kerberos tickets.
  kerberosEnabled: TYPE_BOOL
    true: Enable kerberos.
    false: Disable kerberos.
  kerberosPrincipal: TYPE_STRING
    Principal name. Define a Kerberos account to be added on behalf of user. The following placeholders are supported: - ${LOGIN_ID}: Username part of principal, e.g. "user" if the user logs in as "user@REALM"- ${LOGIN_EMAIL}: Full principal, e.g. "user@REALM" if the user logs in as "user@REALM".
  kerberosConfiguration: TYPE_LIST
    Kerberos configuration.
  kerberosAutoAccountEnabled: TYPE_BOOL
    true: Automatically add a Kerberos account.
    false: Do not automatically add a Kerberos account.
  kerberosCustomConfigurationEnabled: TYPE_BOOL
    true: Customize Kerberos configuration.
    false: Use default Kerberos configuration.

chrome.users.KeyboardFocusableScrollersEnabled: Keyboard focusable scrollers.
  keyboardFocusableScrollersEnabled: TYPE_BOOL
    true: Allow scrollers to be focusable by default.
    false: Do not allow scrollers to be focusable by default.

chrome.users.KeyboardFocusHighlightEnabled: Keyboard focus highlighting.
  keyboardFocusHighlightEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable keyboard focus highlighting.
    TRUE: Enable keyboard focus highlighting.

chrome.users.KeyboardFunctionKeys: Keyboard.
  keyboardDefaultToFunctionKeys: TYPE_BOOL
    true: Treat top-row keys as function keys, but allow user to change.
    false: Treat top-row keys as media keys, but allow user to change.

chrome.users.LargeCursorEnabled: Large cursor.
  largeCursorEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable large cursor.
    TRUE: Enable large cursor.

chrome.users.LegacySameSiteCookieBehaviorEnabled: Default legacy SameSite cookie behavior.
  legacySameSiteCookieBehaviorEnabled: TYPE_ENUM
    DEFAULT_TO_LEGACY_SAME_SITE_COOKIE_BEHAVIOR: Revert to legacy SameSite behavior for cookies on all sites.
    DEFAULT_TO_SAME_SITE_BY_DEFAULT_COOKIE_BEHAVIOR: Use SameSite-by-default behavior for cookies on all sites.
    DEFAULT_TO_USER_PERSONAL_CONFIGURATION: Use the user's personal configuration for SameSite features.

chrome.users.LegacySameSiteCookieBehaviorEnabledForDomainList: Per-site legacy SameSite cookie behavior.
  legacySameSiteCookieBehaviorEnabledForDomainList: TYPE_LIST
    Revert to legacy SameSite cookie behavior on these sites. Prefix domain with [*.] to include all subdomains.

chrome.users.LegacyTechReportAllowlist: Legacy technology reporting.
  legacyTechReportAllowlist: TYPE_LIST
    Add URLs for insights . Controls if a page that use legacy technologies will be reported based on its URL. When policy is set, the URLs whose prefix match an allowlist entry will be used to generated report and uploaded. Unmatched URLs will be ignored. When policy is not set or set to an empty list, no report will be generated. The matching patterns use a similar format to those for the 'URLBlocklist' policy, which are documented at https://support.google.com/chrome/a?p=url_blocklist_filter_format. With a few exceptions below: * No wildcard '*' support. * Schema, port and query are ignored. * subdomain must always be specified to be matched. * At most 100 URLs can be added into the allowlist.

chrome.users.LensCameraAssistedSearchEnabled: Google Lens camera assisted search.
  lensCameraAssistedSearchEnabled: TYPE_BOOL
    true: Allow enterprise user to use Google Lens camera assisted search.
    false: Do not allow enterprise user to use Google Lens camera assisted search.

chrome.users.LensDesktopNtpSearchEnabled: New Tab page Google Lens button.
  lensDesktopNtpSearchEnabled: TYPE_BOOL
    true: Show the Google Lens button in the search box on the New Tab page.
    false: Do not show the Google Lens button in the search box on the New Tab page.

chrome.users.LensOnGalleryEnabled: Lens Gallery App integration.
  lensOnGalleryEnabled: TYPE_BOOL
    true: Enable Lens integration.
    false: Disable Lens integration.
  lensOnGalleryEnabledSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.LensOverlaySettings: Google Lens Overlay.
  lensOverlaySettings: TYPE_ENUM
    ENABLED: Enable Google Lens overlay.
    DISABLED: Disable Google Lens overlay.

chrome.users.LensRegionSearchEnabled: Google Lens region search.
  lensRegionSearchEnabled: TYPE_BOOL
    true: Enable Google Lens region search.
    false: Disable Google Lens region search.

chrome.users.ListenToThisPageEnabled: Read aloud for web pages.
  listenToThisPageEnabled: TYPE_BOOL
    true: Allow read aloud.
    false: Block read aloud.

chrome.users.LiveTranslateEnabled: Live translate.
  liveTranslateEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable Live Translate.
    TRUE: Enable Live Translate.
  liveTranslateEnabledSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.LoadCryptoTokenExtension: Re-enable CryptoToken component extension until Chrome 107.
  loadCryptoTokenExtension: TYPE_BOOL
    true: Enable the CryptoToken component extension until Chrome 107.
    false: Enable the CryptoToken component extension until Chrome 105.

chrome.users.LocalUserFilesAllowed: Local storage configuration.
  localUserFilesAllowed: TYPE_BOOL
    true: Allow users to store and read local data.
    false: Do not allow users to store and read local data.
  localUserFilesMigrationDestination: TYPE_ENUM
    GOOGLE_DRIVE: Migrate existing local files to Google Drive.
    MICROSOFT_ONEDRIVE: Migrate existing local files to OneDrive.
    READ_ONLY: Keep existing local files in read-only mode.
    DELETE: Delete existing local files.

chrome.users.LockIconInAddressBarEnabled: Lock icon in the omnibox for secure connections.
  lockIconInAddressBarEnabled: TYPE_BOOL
    true: Use the lock icon for secure connections.
    false: Use default icons for secure connections.

chrome.users.LockScreen: Lock screen.
  allowScreenLock: TYPE_BOOL
    true: Allow locking screen.
    false: Do not allow locking screen.

chrome.users.LockScreenAutoStartOnlineReauth: Lock screen online reauthentication.
  lockScreenAutoStartOnlineReauth: TYPE_BOOL
    true: Show users the online reauthentication screen.
    false: Show users interstitial screens prior to online reauthentication.

chrome.users.LockScreenMediaPlaybackEnabled: Lock screen media playback.
  lockScreenMediaPlaybackEnabled: TYPE_BOOL
    true: Allow users to play media when the device is locked.
    false: Do not allow users to play media when the device is locked.

chrome.users.LoginDisplayPasswordButtonEnabled: Display password button.
  loginDisplayPasswordButtonEnabled: TYPE_BOOL
    true: Show the display password button on the login and lock screen.
    false: Do not show the display password button on the login and lock screen.

chrome.users.LookalikeWarningAllowlistDomains: Suppress lookalike domain warnings on domains.
  lookalikeWarningAllowlistDomains: TYPE_LIST
    Allowlisted Domains. Enter list of domains where Chrome should prevent the display of lookalike URL warnings.

chrome.users.ManagedAccountsSigninRestriction: Separate profile for managed Google Identity.
  managedAccountsSigninRestriction: TYPE_ENUM
    PRIMARY_ACCOUNT: Force separate profile.
    PRIMARY_ACCOUNT_STRICT: Force separate profile and forbid secondary managed accounts.
    NONE: Do not force separate profile.
    PRIMARY_ACCOUNT_KEEP_EXISTING_DATA: Let users choose to have a separate profile.
    PRIMARY_ACCOUNT_STRICT_KEEP_EXISTING_DATA: Let users choose to have a separate profile but forbid secondary managed accounts.

chrome.users.ManagedBookmarksSetting: Managed bookmarks.
  managedBookmarks
    bookmarks
      folder
        name: TYPE_STRING
        entries
      link
        name: TYPE_STRING
        url: TYPE_STRING
    toplevelName: TYPE_STRING

chrome.users.MaxConnectionsPerProxy: Max connections per proxy.
  maxConnectionsPerProxy: TYPE_INT64
    Maximum number of concurrent connections to the proxy server. Specifies the maximal number of simultaneous connections to the proxy server. The value of this policy should be lower than 100 and higher than 6 and the default value is 32.

chrome.users.MaxInvalidationFetchDelay: Policy fetch delay.
  maxInvalidationFetchDelay: TYPE_INT64

chrome.users.MaxInvalidationFetchDelayV2: Policy fetch delay.
  maxInvalidationFetchDelay: TYPE_INT64

chrome.users.MediaRecommendationsEnabled: Media Recommendations.
  mediaRecommendationsEnabled: TYPE_BOOL
    true: Show personalized media recommendations.
    false: Do not show personalized media recommendations.

chrome.users.MemorySaverModeSavings: Memory saver.
  memorySaverModeSavings: TYPE_ENUM
    MODERATE: Apply moderate memory savings.
    BALANCED: Apply balanced memory savings.
    MAXIMUM: Apply maximum memory savings.
    UNSET: Allow the user to decide.

chrome.users.MetricsReportingEnabled: Metrics reporting.
  metricsReportingEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not send anonymous reports of usage and crash-related data to Google.
    TRUE: Send anonymous reports of usage and crash-related data to Google.
  metricsReportingEnabledCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.MicrosoftOfficeDocuments: Microsoft Office documents.
  microsoftOfficeCloudUpload: TYPE_ENUM
    AUTOMATED: Enable automatic upload and file handling.
    ALLOWED: Allow users to enable automatic upload and file handling.
    DISALLOWED: Disable automatic upload and file handling.
  googleWorkspaceCloudUpload: TYPE_ENUM
    AUTOMATED: Enable automatic upload and file handling.
    ALLOWED: Allow users to enable automatic upload and file handling.
    DISALLOWED: Disable automatic upload and file handling.
  quickOfficeForceFileDownloadEnabled: TYPE_BOOL
    true: Disable preview and download directly (recommended).
    false: Preview in basic editor in the browser.

chrome.users.MicrosoftOneDrive: Microsoft OneDrive integration.
  microsoftOneDriveMount: TYPE_ENUM
    AUTOMATED: Automatically integrate Microsoft OneDrive into Files app.
    ALLOWED: Allow users to set up Microsoft OneDrive integration.
    DISALLOWED: Disable Microsoft OneDrive Files app integration.
  microsoftOneDriveAccountRestrictions: TYPE_LIST
    Specify the Microsoft domain within which OneDrive will be used. Restrict which accounts can be used with the Microsoft OneDrive integration.

chrome.users.MixedContentAutoupgradeEnabled: Mixed content autoupgrading.
  mixedContentAutoupgradeEnabled: TYPE_BOOL
    true: Enable mixed content autoupgrading.
    false: Disable mixed content autoupgrading.

chrome.users.MobileManagement: Chrome on Android.
  enableMobileChromePolicies: TYPE_BOOL
    true: Apply supported user settings to Chrome on Android.
    false: Do not apply supported user settings to Chrome on Android.

chrome.users.MonoAudioEnabled: Mono audio.
  monoAudioEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable mono audio.
    TRUE: Enable mono audio.

chrome.users.MultipleSignInAccess: Multiple sign-in access.
  newChromeOsMultiProfileUserBehavior: TYPE_ENUM
    PRIMARY_ONLY: Managed user must be the primary user (secondary users are allowed).
    UNRESTRICTED: Unrestricted user access (allow any user to be added to any other user's session).
    NOT_ALLOWED: Block multiple sign-in access for users in this organization.

chrome.users.MultiScreenCaptureAllowedForUrls: URLs allowed for multi-screen capture .
  multiScreenCaptureAllowedForUrls: TYPE_LIST
    URLs allowed for multi-screen capture . The getAllScreensMedia API allows isolated web applications to capture multiple surfaces at once without additional user permission.

chrome.users.MutationEventsEnabled: Mutation Events.
  mutationEventsEnabled: TYPE_BOOL
    true: Temporarily re-enable mutation events.
    false: Mutation events stop firing after the removal date.

chrome.users.NativeClientForceAllowed: Allow Native Client (NaCl).
  nativeClientForceAllowed: TYPE_BOOL
    true: Allow Native Client to run even if it is disabled by default.
    false: Use default behavior.

chrome.users.NativeHostsExecutablesLaunchDirectly: Native messaging hosts.
  nativeHostsExecutablesLaunchDirectly: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Force Windows native messaging hosts to launch via Command Prompt.
    TRUE: Directly launch executable native messaging hosts on Windows.

chrome.users.NativeMessagingAllowed: Native Messaging allowed hosts.
  nativeMessagingAllowlist: TYPE_LIST
    Native Messaging hosts not subject to the blocklist. Domains to allow native messaging.

chrome.users.NativeMessagingBlocked: Native Messaging blocked hosts.
  nativeMessagingBlocklist: TYPE_LIST
    Prohibited Native Messaging hosts. Domains to block native messaging. A pattern of "*" will block all hosts not specified in the allowlist.

chrome.users.NativeMessagingUserHosts: Native Messaging user-level hosts.
  nativeMessagingUserLevelHosts: TYPE_BOOL
    true: Allow usage of Native Messaging hosts installed at the user level.
    false: Only allow usage of Native Messaging hosts installed at the system level.

chrome.users.NearbyShareAllowed: Nearby Share.
  nearbyShareAllowed: TYPE_BOOL
    true: Allow users to enable Nearby Share.
    false: Prevent users from enabling Nearby Share.

chrome.users.NetworkFileShares: Network file shares.
  networkFileSharesAllowed: TYPE_BOOL
    true: Allow network file shares.
    false: Block network file shares.
  netBiosShareDiscoveryEnabled: TYPE_BOOL
    true: Use NetBIOS discovery.
    false: Do not allow NetBIOS discovery.
  ntlmShareAuthenticationEnabled: TYPE_BOOL
    true: Use NTLM authentication.
    false: Do not use NTLM authentication.
  networkFileSharesPreconfiguredShares
    preconfiguredFiles
      mode: TYPE_ENUM
        DROP_DOWN:
        PRE_MOUNT:
      shareUrl: TYPE_STRING

chrome.users.NetworkPrediction: Network prediction.
  networkPredictionOptions: TYPE_ENUM
    NETWORK_PREDICTION_ALLOW_USER: Allow the user to decide.
    PREDICT_NETWORK_ACTIONS: Predict network actions.
    DO_NOT_PREDICT_NETWORK_ACTIONS: Do not predict network actions.

chrome.users.NetworkServiceSandboxEnabled: Network service sandbox.
  networkServiceSandboxEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable the network service sandbox.
    TRUE: Enable the network service sandbox.

chrome.users.NewBaseUrlInheritanceBehaviorAllowed: Enable the feature NewBaseUrlInheritanceBehavior.
  newBaseUrlInheritanceBehaviorAllowed: TYPE_BOOL
    true: NewBaseUrlInheritanceBehavior feature available.
    false: NewBaseUrlInheritanceBehavior feature disabled.

chrome.users.NewTabPageLocation: New tab page.
  newTabPageLocation: TYPE_STRING
    New tab URL (leave empty for default). Specifies the URL of the page that should load when Chrome opens a new tab.

chrome.users.Notifications: Notifications.
  defaultNotificationsSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_NOTIFICATIONS: Allow sites to show desktop notifications.
    BLOCK_NOTIFICATIONS: Do not allow sites to show desktop notifications.
    ASK_NOTIFICATIONS: Always ask the user if a site can show desktop notifications.
  notificationsAllowedForUrls: TYPE_LIST
    Allow these sites to show notifications. Urls to allow notifications. Prefix domain with [*.] to include all subdomains.Maximum of 1000 URLs. .
  notificationsBlockedForUrls: TYPE_LIST
    Block notifications on these sites. Urls to block notifications. Prefix domain with [*.] to include all subdomains.Maximum of 1000 URLs. .

chrome.users.NtlmV2Enabled: NTLMv2 authentication.
  ntlmV2Enabled: TYPE_BOOL
    true: Enable NTLMv2 authentication.
    false: Disable NTLMv2 authentication.

chrome.users.NtpCardsVisible: Show cards on the New Tab Page.
  ntpCardsVisible: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not show cards on the New Tab Page.
    TRUE: Show cards on the New Tab Page if content is available.

chrome.users.NtpContentSuggestionsEnabled: New Tab page content suggestions.
  ntpContentSuggestionsEnabled: TYPE_BOOL
    true: Show content suggestions on the New Tab page.
    false: Do not show content suggestions on the New Tab page.

chrome.users.NtpCustomBackgroundEnabled: New Tab page background.
  ntpCustomBackgroundEnabled: TYPE_BOOL
    true: Allow users to customize the background on the New Tab page.
    false: Do not allow users to customize the background on the New Tab page.

chrome.users.NtpMiddleSlotAnnouncementVisible: Middle slot announcement on the New Tab Page.
  ntpMiddleSlotAnnouncementVisible: TYPE_BOOL
    true: Show the middle slot announcement on the New Tab Page if it is available.
    false: Do not show the middle slot announcement on the New Tab Page even if it is available.

chrome.users.NtpOutlookCardVisible: New Tab page Outlook card.
  ntpOutlookCardVisible: TYPE_BOOL
    true: Enable New Tab page Outlook calendar card.
    false: Disable New Tab page Outlook calendar card.

chrome.users.NtpSharepointCardVisible: New Tab page Sharepoint and OneDrive card.
  ntpSharepointCardVisible: TYPE_BOOL
    true: Enable New Tab page Sharepoint and OneDrive files card.
    false: Disable New Tab page Sharepoint and OneDrive files card.

chrome.users.OffsetParentNewSpecBehaviorEnabled: Enable legacy HTMLElement offset behavior.
  offsetParentNewSpecBehaviorEnabled: TYPE_BOOL
    true: Use new offset behavior.
    false: Use legacy offset behavior.

chrome.users.OnlineRevocationChecks: Online revocation checks.
  enableOnlineRevocationChecks: TYPE_BOOL
    true: Perform online OCSP/CRL checks.
    false: Do not perform online OCSP/CRL checks.

chrome.users.OopPrintDriversAllowed: Out-of-process print drivers.
  oopPrintDriversAllowed: TYPE_BOOL
    true: Use a separate service process for platform printing calls.
    false: Use the browser process for platform printing calls.

chrome.users.OptimizationGuideFetchingEnabled: Optimization Guide Fetching.
  optimizationGuideFetchingEnabled: TYPE_BOOL
    true: Enable fetching of page load metadata and machine learning models to enhance the browsing experience.
    false: Disable fetching of page load metadata and machine learning models that enhance the browsing experience.

chrome.users.OriginAgentClusterDefaultEnabled: Origin-keyed agent clustering.
  originAgentClusterDefaultEnabled: TYPE_BOOL
    true: Use origin-keyed agent clusters.
    false: Use site-keyed agent clusters.

chrome.users.OsColorMode: ChromeOS color mode.
  osColorMode: TYPE_ENUM
    LIGHT: Recommend the light theme.
    DARK: Recommend the dark theme.
    AUTO: Recommend auto mode.

chrome.users.OutOfProcessSystemDnsResolutionEnabled: Network process system DNS resolution.
  outOfProcessSystemDnsResolutionEnabled: TYPE_ENUM
    UNSET: Run system DNS resolution in, out of, or partially in and partially out of the network process.
    FALSE: Run system DNS resolution in the network process.
    TRUE: Run system DNS resolution in or out of the network process.

chrome.users.OverrideSecurityRestrictionsOnInsecureOrigin: Override insecure origin restrictions.
  overrideSecurityRestrictionsOnInsecureOrigin: TYPE_LIST
    Origin or hostname patterns to ignore insecure origins security restrictions. Specifies the origin or hostname patterns for which restrictions on insecure origins should not apply.

chrome.users.PageUpAndPageDownKeysModifier: Control the shortcut used to trigger the PageUp/PageDown "six pack" keys.
  pageUpAndPageDownKeysModifier: TYPE_ENUM
    NONE: PageUp/PageDown settings are disabled.
    ALT: PageUp/PageDown settings use the shortcut that contains the alt modifier.
    SEARCH: PageUp/PageDown settings use the shortcut that contains the search modifier.
  pageUpAndPageDownKeysModifierSettingGroupPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.ParcelTrackingEnabled: Parcel tracking.
  parcelTrackingEnabled: TYPE_BOOL
    true: Allow Parcel Tracking on Chrome.
    false: Do not allow Parcel Tracking on Chrome.

chrome.users.PasswordAlert: Password alert.
  passwordProtectionWarningTrigger: TYPE_ENUM
    NO_WARNING: No password protection warning.
    WARN_ON_PASSWORD_REUSE: Trigger on password reuse.
    WARN_ON_PHISHING_REUSE: Trigger on password reuse on phishing page.
  passwordProtectionChangePasswordUrl: TYPE_STRING
    URL for password change. Enter the URL of the webpage where users can change their password.
  passwordProtectionLoginUrls: TYPE_LIST
    Login URLs. Enter list of enterprise login URLs where password protection service should capture fingerprint of password.

chrome.users.PasswordDismissCompromisedAlertEnabled: Compromised password alerts.
  passwordDismissCompromisedAlertEnabled: TYPE_BOOL
    true: Allow dismissing compromised password alerts.
    false: Prevent dismissing compromised password alerts.

chrome.users.PasswordLeakDetection: Enable leak detection for entered credentials.
  passwordLeakDetection: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable Leak detection for entered credentials.
    TRUE: Enable Leak detection for entered credentials.

chrome.users.PasswordManager: Password manager.
  passwordManagerEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never allow use of password manager.
    TRUE: Always allow use of password manager.
  passwordManagerPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.PasswordManagerPasskeysEnabled: Passkeys.
  passwordManagerPasskeysEnabled: TYPE_BOOL
    true: Allow the user to save passkeys using the password manager.
    false: Do not allow the user to save passkeys using the password manager.

chrome.users.PaymentMethodQueryEnabled: Payment methods.
  paymentMethodQueryEnabled: TYPE_BOOL
    true: Allow websites to check if the user has payment methods saved.
    false: Always tell websites that no payment methods are saved.

chrome.users.PdfAnnotationsEnabled: PDF Annotations.
  pdfAnnotationsEnabled: TYPE_BOOL
    true: Allow the PDF viewer to annotate PDFs.
    false: Do not allow the PDF viewer to annotate PDFs.

chrome.users.PdfLocalFileAccessAllowedForDomains: Local file access to file:// URLs in the PDF Viewer.
  pdfLocalFileAccessAllowedForDomains: TYPE_LIST
    Allowed URLs. List of file URLs with local access enabled in the PDF viewer.

chrome.users.PdfUseSkiaRendererEnabled: Renderer for PDF files.
  pdfUseSkiaRendererEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Use AGG renderer for PDF files.
    TRUE: Use Skia renderer for PDF files.

chrome.users.PdfViewerOutOfProcessIframeEnabled: PDF viewer.
  pdfViewerOutOfProcessIframeEnabled: TYPE_BOOL
    true: PDF viewer uses out-of-process iframe.
    false: PDF viewer uses guest view.

chrome.users.PersistentQuotaEnabled: Persistent quota for webkitRequestFileSystem.
  persistentQuotaEnabled: TYPE_BOOL
    true: Enable persistent quota.
    false: Disable persistent quota.

chrome.users.PhoneHub: Phone Hub.
  phoneHubAllowed: TYPE_BOOL
    true: Allow Phone Hub to be enabled.
    false: Do not allow Phone Hub to be enabled.
  phoneHubNotificationsAllowed: TYPE_BOOL
    true: Allow Phone Hub notifications to be enabled.
    false: Do not allow Phone Hub notifications to be enabled.
  phoneHubTaskContinuationAllowed: TYPE_BOOL
    true: Allow Phone Hub task continuation to be enabled.
    false: Do not allow Phone Hub task continuation to be enabled.

chrome.users.PhysicalKeyboardAutocorrect: Physical keyboard autocorrect.
  physicalKeyboardAutocorrect: TYPE_BOOL
    true: Enable physical keyboard autocorrect.
    false: Disable physical keyboard autocorrect.

chrome.users.PhysicalKeyboardPredictiveWriting: Physical keyboard predictive writing.
  physicalKeyboardPredictiveWriting: TYPE_BOOL
    true: Enable physical keyboard predictive writing.
    false: Disable physical keyboard predictive writing.

chrome.users.PinSettings: Lock screen PIN.
  pinUnlockMinimumLength: TYPE_INT64
    Minimum PIN length. Sets the minimum length of the lock screen PIN.
  pinUnlockMaximumLength: TYPE_INT64
    Maximum PIN length. If unset or set to zero, the PIN length is unlimited.
  pinUnlockWeakPinsAllowed: TYPE_ENUM
    UNSET: Allow users to set a weak PIN, but show a warning.
    FALSE: Do not allow users to set a weak PIN.
    TRUE: Allow users to set a weak PIN.

chrome.users.PinUnlockAutosubmitEnabled: PIN auto-submit.
  pinUnlockAutosubmitEnabled: TYPE_BOOL
    true: Enable PIN auto-submit on the lock and login screen.
    false: Disable PIN auto-submit on the lock and login screen.
  pinUnlockAutosubmitEnabledCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.PluginVmAllowed: Parallels Desktop.
  pluginVmAllowed: TYPE_BOOL
    true: Allow users to use Parallels Desktop.
    false: Do not allow users to use Parallels Desktop.
  ackNoticeForPluginVmAllowedSetToTrue: TYPE_BOOL
    This field must be set to true to acknowledge the notice message associated with the field 'plugin_vm_allowed' set to value 'true'. Please sse the notices listed with this policy for more information.

chrome.users.PluginVmDataCollection: Diagnostic information.
  pluginVmDataCollectionAllowed: TYPE_BOOL
    true: Enable sharing diagnostics data to Parallels.
    false: Disable sharing diagnostics data to Parallels.

chrome.users.PluginVmImage: Parallels Desktop Windows image.
  pluginVmImageUrl: TYPE_STRING
    Specifies the URL for the Windows image for plugin virtual machine.
  pluginVmImageHash: TYPE_STRING
    SHA-256 hash. Enter the SHA-256 hash of the Windows image for Parallels Desktop.

chrome.users.PluginVmRequiredDiskSpace: Required disk space.
  pluginVmRequiredFreeDiskSpace: TYPE_INT64
    Required free disk space (GB). Sets the minimum free space needed to run PluginVM app.

chrome.users.PolicyMergelist: Policy mergelist.
  policyMergelist: TYPE_LIST
    On-device policy names. The values of each policy will be merged when set from different sources.

chrome.users.PolicyPrecedence: Policy precedence.
  policyPrecedence: TYPE_ENUM
    PRECEDENCE_DEFAULT: Machine > Machine cloud > OS user > Chrome profile.
    PRECEDENCE_CLOUD_MACHINE: Machine cloud > Machine > OS user > Chrome profile.
    PRECEDENCE_CLOUD_USER: Machine > Chrome profile > Machine cloud > OS user.
    PRECEDENCE_BOTH: Chrome profile > Machine cloud > Machine > OS user.

chrome.users.Popups: Pop-ups.
  defaultPopupsSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    ALLOW_POPUPS: Allow all pop-ups.
    BLOCK_POPUPS: Block all pop-ups.
  popupsAllowedForUrls: TYPE_LIST
    Allow pop-ups on these sites. Urls to allow pop-ups.
  popupsBlockedForUrls: TYPE_LIST
    Block pop-ups on these sites. Urls to block pop-ups.

chrome.users.PostQuantumKeyAgreementEnabled: Post-quantum TLS.
  postQuantumKeyAgreementEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not allow post-quantum key agreement in TLS connections.
    TRUE: Allow post-quantum key agreement in TLS connections.

chrome.users.PowerManagementUsesAudioActivity: Power management uses audio activity.
  powerManagementUsesAudioActivity: TYPE_BOOL
    true: Disallow idle action when audio is playing.
    false: Allow idle action when audio is playing.

chrome.users.PowerManagementUsesVideoActivity: Power management uses video activity.
  powerManagementUsesVideoActivity: TYPE_BOOL
    true: Disallow idle action when video is playing.
    false: Allow idle action when video is playing.

chrome.users.PpapiSharedImagesForVideoDecoderAllowed: Allow Pepper to use shared images for video decoding.
  ppapiSharedImagesForVideoDecoderAllowed: TYPE_BOOL
    true: Allow new implementation.
    false: Force old implementation.

chrome.users.PpApiSharedImagesSwapChainAllowed: Modern buffer allocation for Graphics3D APIs PPAPI plugin.
  ppApiSharedImagesSwapChainAllowed: TYPE_BOOL
    true: Allow new implementation.
    false: Force old implementation.

chrome.users.PrefixedStorageInfoEnabled: Re-enable window.webkitStorageInfo API.
  prefixedStorageInfoEnabled: TYPE_BOOL
    true: Enable window.webkitStorageInfo.
    false: Disable window.webkitStorageInfo.

chrome.users.PrefixedVideoFullscreenApiAvailability: Prefixed video fullscreen API.
  prefixedVideoFullscreenApiAvailability: TYPE_ENUM
    RUNTIME_ENABLED: Use the default Chrome setting.
    DISABLED: Disable prefixed video fullscreen API.
    ENABLED: Enable prefixed video fullscreen API.

chrome.users.PrimaryMouseButtonSwitch: Primary mouse button.
  primaryMouseButtonSwitch: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Left button is primary.
    TRUE: Right button is primary.

chrome.users.PrinterTypeDenyList: Blocked printer types.
  printerTypeDenyList: TYPE_LIST
    privet: Privet zeroconf-based protocol (deprecated).
    extension: Extension-based.
    pdf: Save as PDF.
    local: Local printer.
    cloud: Google Cloud Print (deprecated).

chrome.users.PrintHeaderFooter: Print headers and footers.
  printHeaderFooter: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never print headers and footers.
    TRUE: Always print headers and footers.
  printHeaderFooterCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.PrintingAllowedBackgroundGraphicsModes: Background graphics printing restriction.
  printingAllowedBackgroundGraphicsModes: TYPE_ENUM
    ANY: Allow the user to decide.
    ENABLED: Always require printing of background images.
    DISABLED: Do not allow printing of background images.

chrome.users.PrintingAllowedPinModes: Restrict PIN printing mode.
  printingAllowedPinModes: TYPE_ENUM
    ANY_PIN_PRINTING_MODE: Do not restrict PIN printing mode.
    PIN_PRINTING_ONLY: Always require PIN printing.
    NON_PIN_PRINTING_ONLY: Do not allow PIN printing.

chrome.users.PrintingBackgroundGraphicsDefault: Background graphics printing default.
  printingBackgroundGraphicsDefault: TYPE_ENUM
    DISABLED: Disable background graphics printing mode by default.
    ENABLED: Enable background graphics printing mode by default.

chrome.users.PrintingLpacSandboxEnabled: Printing LPAC Sandbox.
  printingLpacSandboxEnabled: TYPE_BOOL
    true: Run printing services in LPAC sandbox when available.
    false: Run printing services in a less secure sandbox.

chrome.users.PrintingMaxSheetsAllowed: Maximum sheets.
  printingMaxSheetsAllowedNullable: TYPE_INT64

chrome.users.PrintingPaperSizeDefault: Default printing page size.
  printingPaperSizeEnum: TYPE_ENUM
    UNSET: No policy set.
    NA_LETTER_8_5X11IN: Letter.
    NA_LEGAL_8_5X14IN: Legal.
    ISO_A4_210X297MM: A4.
    NA_LEDGER_11X17IN: Tabloid.
    ISO_A3_297X420MM: A3.
    CUSTOM: Custom.
  printingPaperSizeWidth: TYPE_STRING
    Page width (in millimeters). Sets a custom page width (in millimeters).
  printingPaperSizeHeight: TYPE_STRING
    Page height (in millimeters). Sets a custom page height (in millimeters).

chrome.users.PrintingPinDefault: Default PIN printing mode.
  printingPinDefault: TYPE_ENUM
    DEFAULT_TO_PIN_PRINTING: With PIN.
    DEFAULT_TO_NOT_PIN_PRINTING: Without PIN.

chrome.users.PrintingSendUsernameAndFilenameEnabled: CUPS Print job information.
  printingSendUsernameAndFilenameEnabled: TYPE_BOOL
    true: Include user account and filename in print job.
    false: Do not include user account and filename in print job.

chrome.users.PrintJobHistoryExpirationPeriodNew: Print job history retention period.
  printJobHistoryExpirationPeriodDaysNew: TYPE_INT64

chrome.users.PrintJobHistoryExpirationPeriodNewV2: Print job history retention period.
  printJobHistoryExpirationPeriodDaysNew: TYPE_INT64

chrome.users.PrintPdfAsImage: Print PDF as image.
  printPdfAsImageAvailability: TYPE_BOOL
    true: Allow users to print PDF documents as images.
    false: Do not allow users to print PDF documents as images.
  printRasterizePdfDpi: TYPE_INT64
  printPdfAsImageDefault: TYPE_BOOL
    true: Default to printing PDFs as images when available.
    false: Default to printing PDFs without being rasterized.

chrome.users.PrintPostScriptMode: PostScript printer mode.
  printPostScriptMode: TYPE_ENUM
    DEFAULT: Default.
    TYPE_42: Type 42.

chrome.users.PrintPreview: Print preview.
  disablePrintPreview: TYPE_BOOL
    true: Always use the system print dialog instead of print preview.
    false: Allow using print preview.

chrome.users.PrintPreviewUseSystemDefaultPrinter: System Default Printer.
  printPreviewUseSystemDefaultPrinter: TYPE_BOOL
    true: Use the system default printer as the default choice in Print Preview.
    false: Use the most recently used printer as the default choice in Print Preview.
  printPreviewUseSystemDefaultPrinterCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.PrintRasterizationMode: Print rasterization mode.
  printRasterizationMode: TYPE_ENUM
    FULL: Full.
    FAST: Fast.

chrome.users.PrivacySandboxPromptEnabled: Privacy Sandbox.
  privacySandboxPromptEnabled: TYPE_BOOL
    true: Allow Google Chrome to determine whether to show the Privacy Sandbox prompt.
    false: Do not show the Privacy Sandbox prompt to users.
  privacySandboxAdTopicsEnabled: TYPE_BOOL
    true: Allow users to turn on or off the Privacy Sandbox Ad topics setting on their device.
    false: Disable Privacy Sandbox Ad topics setting for your users.
  privacySandboxSiteEnabledAdsEnabled: TYPE_BOOL
    true: Allow users to turn on or off the Privacy Sandbox Site-suggested ads setting on their device.
    false: Disable Privacy Sandbox Site-suggested ads setting for your users.
  privacySandboxAdMeasurementEnabled: TYPE_BOOL
    true: Allow users to turn on or off the Privacy Sandbox Ad measurement setting on their device.
    false: Disable Privacy Sandbox Ad measurement setting for your users.

chrome.users.PrivacyScreenEnabled: Privacy screen.
  privacyScreenEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Always disable the privacy screen.
    TRUE: Always enable the privacy screen.

chrome.users.PrivateNetworkAccessRestrictionsEnabled: Private Network Access restrictions.
  privateNetworkAccessRestrictionsEnabled: TYPE_BOOL
    true: Apply restrictions to requests to more-private network endpoints.
    false: Use default behavior when determining if websites can make requests to network endpoints.

chrome.users.ProfilePickerOnStartupAvailability: Profile picker availability on browser startup.
  profilePickerOnStartupAvailability: TYPE_ENUM
    ENABLED: Allow the user to decide.
    DISABLED: Do not show profile picker at browser startup.
    FORCED: Always show profile picker at browser startup.

chrome.users.ProfileSeparationDataMigrationSettings: Profile separation data migration.
  profileSeparationDataMigrationSettings: TYPE_ENUM
    USER_OPT_IN_DATA: Let users decide to bring existing browsing data into their managed profile.
    USER_OPT_OUT_DATA: Suggest to users to bring their existing data in the managed profile and give them a choice not to.
    ALWAYS_SEPARATE_DATA: Users cannot bring existing browsing data in their managed profile.

chrome.users.ProfileSeparationDomainExceptionList: Profile separation exemptions.
  profileSeparationDomainExceptionList: TYPE_LIST
    List of domains exempted from profile separation. List of domains exempted from profile separation. Sign in from a domain not listed will require the creation of a separate profile. If empty, no signin will require a separate profile.

chrome.users.ProfileSeparationSettings: Enterprise profile separation.
  profileSeparationSettings: TYPE_ENUM
    SUGGESTED: Suggest profile separation.
    ENFORCED: Enforce profile separation.
    DISABLED: Disable profile separation.

chrome.users.ProjectorEnabled: Screencast.
  projectorEnabled: TYPE_BOOL
    true: Allow users to create and view screencasts.
    false: Do not allow users to create and view screencasts.

chrome.users.PromotionalTabsEnabled: Promotional content.
  promotionalTabsEnabled: TYPE_BOOL
    true: Enable showing full-tab promotional content.
    false: Disable showing full-tab promotional content.

chrome.users.PromptForDownloadLocation: Download location prompt.
  promptForDownloadLocation: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Do not ask the user (downloads start immediately).
    TRUE: Ask the user where to save the file before downloading.

chrome.users.PromptOnMultipleMatchingCertificates: Prompt when multiple certificates match.
  promptOnMultipleMatchingCertificates: TYPE_BOOL
    true: Prompt the user to select the client certificate whenever the auto-selection policy matches multiple certificates.
    false: Only prompt the user when no certificate matches the auto-selection.

chrome.users.QrCodeGeneratorEnabled: QR Code Generator.
  qrCodeGeneratorEnabled: TYPE_BOOL
    true: Enable QR Code Generator.
    false: Disable QR Code Generator.

chrome.users.QuickAnswersEnabled: Quick Answers.
  quickAnswersEnabled: TYPE_BOOL
    true: Enable Quick Answers.
    false: Disable Quick Answers.
  quickAnswersDefinitionEnabled: TYPE_BOOL
    true: Enable Quick Answers definition.
    false: Disable Quick Answers definition.
  quickAnswersTranslationEnabled: TYPE_BOOL
    true: Enable Quick Answers translation.
    false: Disable Quick Answers translation.
  quickAnswersUnitConversionEnabled: TYPE_BOOL
    true: Enable Quick Answers unit conversion.
    false: Disable Quick Answers unit conversion.

chrome.users.QuickUnlockModeAllowlist: Quick unlock.
  quickUnlockModeAllowlist: TYPE_LIST
    PIN: PIN.
    FINGERPRINT: Fingerprint.

chrome.users.QuicProtocol: QUIC protocol.
  quicAllowed: TYPE_BOOL
    true: Enable.
    false: Disable.

chrome.users.RecoveryFactorBehavior: Account recovery.
  recoveryFactorBehavior: TYPE_ENUM
    UNSET: Defer activation of account recovery until migration phase (see help center).
    ACTIVATE_ACCOUNT_RECOVERY: Activate account recovery.
    ACTIVATE_ACCOUNT_RECOVERY_RECOMMENDED: Activate account recovery and allow users to override.
    DEACTIVATE_ACCOUNT_RECOVERY: Deactivate account recovery.

chrome.users.RegisteredProtocolHandlersSetting: Custom Protocol Handlers.
  registeredProtocolHandlers
    protocols
      scheme: TYPE_STRING
      handler: TYPE_STRING

chrome.users.RelaunchNotificationWithDuration: Relaunch notification.
  relaunchNotificationEnum: TYPE_ENUM
    NO_NOTIFICATION: No relaunch notification.
    RECOMMENDED: Show notification recommending relaunch.
    REQUIRED: Force relaunch after a period.
  relaunchNotificationPeriodDuration: TYPE_INT64
  relaunchInitialQuietPeriodDuration: TYPE_INT64
  relaunchWindowStartTime
    timeOfDay
      hours: TYPE_INT32
      minutes: TYPE_INT32
      seconds: TYPE_INT32
      nanos: TYPE_INT32
  relaunchWindowDurationMin: TYPE_INT64

chrome.users.RelaunchNotificationWithDurationV2: Relaunch notification.
  relaunchNotificationEnum: TYPE_ENUM
    NO_NOTIFICATION: No relaunch notification.
    RECOMMENDED: Show notification recommending relaunch.
    REQUIRED: Force relaunch after a period.
  relaunchNotificationPeriodDuration: TYPE_INT64
  relaunchInitialQuietPeriodDuration: TYPE_INT64
  relaunchWindowStartTime
    timeOfDay
      hours: TYPE_INT32
      minutes: TYPE_INT32
      seconds: TYPE_INT32
      nanos: TYPE_INT32
  relaunchWindowDurationMin: TYPE_INT64

chrome.users.RemoteAccessHostAllowEnterpriseRemoteSupportConnections: Enterprise remote support connections.
  remoteAccessHostAllowEnterpriseRemoteSupportConnections: TYPE_BOOL
    true: Allow remote support connections from enterprise admins.
    false: Prevent remote support connections from enterprise admins.

chrome.users.RemoteAccessHostAllowRemoteSupportConnections: Remote support connections.
  remoteAccessHostAllowRemoteSupportConnections: TYPE_BOOL
    true: Allow remote support connections.
    false: Prevent remote support connections.

chrome.users.RemoteAccessHostClientDomainList: Remote access clients.
  remoteAccessHostClientDomainList: TYPE_LIST
    Remote access client domain. Configure the required domain names for remote access clients.

chrome.users.RemoteAccessHostClipboardSizeBytes: Clipboard sync max size.
  remoteAccessHostClipboardSizeBytes: TYPE_INT64

chrome.users.RemoteAccessHostDomainList: Remote access hosts.
  remoteAccessHostDomainList: TYPE_LIST
    Remote access host domain. Configure the required domain names for remote access hosts.

chrome.users.RemoteAccessHostFirewallTraversal: Firewall traversal.
  remoteAccessHostFirewallTraversal: TYPE_BOOL
    true: Enable firewall traversal.
    false: Disable firewall traversal.
  remoteAccessHostAllowRelayedConnection: TYPE_BOOL
    true: Enable the use of relay servers.
    false: Disable the use of relay servers.
  remoteAccessHostUdpPortRange: TYPE_STRING
    UDP port range. Format: minimum-maximum (e.g. 12400-12409). If unset, any port may be used.

chrome.users.RemoteDebuggingAllowed: Allow remote debugging.
  remoteDebuggingAllowed: TYPE_BOOL
    true: Allow use of the remote debugging.
    false: Do not allow use of the remote debugging.

chrome.users.RendererAppContainerEnabled: Renderer App Container.
  rendererAppContainerEnabled: TYPE_BOOL
    true: Enable the Renderer App Container sandbox.
    false: Disable the Renderer App Container sandbox.

chrome.users.RendererCodeIntegrityEnabled: Enable renderer code integrity.
  rendererCodeIntegrityEnabled: TYPE_BOOL
    true: Renderer code integrity enabled.
    false: Renderer code integrity disabled.

chrome.users.ReportAppUsage: App usage reporting.
  reportAppUsage: TYPE_LIST
    chrome_apps_and_extensions: Chrome apps and extensions.
    progressive_web_apps: Progressive Web Apps.
    android_apps: Android apps.
    linux_apps: Linux apps.
    system_apps: System apps.
    games: Linux games.
    browser: Chrome Browser.

chrome.users.RequireOnlineRevocationChecksForLocalAnchors: Require online OCSP/CRL checks for local trust anchors.
  requireOnlineRevocationChecksForLocalAnchors: TYPE_BOOL
    true: Perform revocation checking for successfully validated server certificates signed by locally installed CA certificates.
    false: Use existing online revocation-checking settings.

chrome.users.RestrictAccountsToPatterns: Visible Accounts.
  restrictAccountsToPatterns: TYPE_LIST
    Restrict accounts that are visible in Chrome to those matching one of the patterns specified. Use the wildcard character '*' to match zero or more arbitrary characters. The escape character is '', so to match actual '*' or '' characters, put a '' in front of them.

chrome.users.RestrictPrintColor: Restrict color printing mode.
  printingAllowedColorModes: TYPE_ENUM
    ANY_COLOR_MODE: Do not restrict color printing mode.
    COLOR_ONLY: Color only.
    MONOCHROME_ONLY: Black and white only.

chrome.users.RestrictPrintDuplexMode: Restrict page sides.
  printingAllowedDuplexModes: TYPE_ENUM
    ANY_DUPLEX_MODE: Do not restrict duplex printing mode.
    SIMPLEX_ONLY: One-sided only.
    DUPLEX_ONLY: Two-sided only.

chrome.users.RestrictSigninToPattern: Restrict sign-in to pattern.
  restrictSigninToPattern: TYPE_STRING
    Pattern. A regular expression which is used to determine which Google accounts can be set as browser primary accounts in Google Chrome (i.e. the account that is chosen during the Sync opt-in flow). For example, the value .*@example.com would restrict sign in to accounts in the example.com domain.

chrome.users.RsaKeyUsageForLocalAnchorsEnabled: Check RSA key usage.
  rsaKeyUsageForLocalAnchorsEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable RSA key usage checking.
    TRUE: Enable RSA key usage checking.

chrome.users.SafeBrowsingAllowlistDomain: Safe Browsing allowed domains.
  safeBrowsingAllowlistDomains: TYPE_LIST
    Allowed domains. Enter the list of domains that you want to be excluded from Safe Browsing checks.

chrome.users.SafeBrowsingDeepScanningEnabled: Allow download deep scanning for Safe Browsing-enabled users.
  safeBrowsingDeepScanningEnabled: TYPE_BOOL
    true: Enable Safe Browsing download deep scans.
    false: Disable Safe Browsing download deep scans.

chrome.users.SafeBrowsingExtendedReporting: Help improve Safe Browsing.
  safeBrowsingExtendedReportingEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable sending extra information to help improve Safe Browsing.
    TRUE: Enable sending extra information to help improve Safe Browsing.

chrome.users.SafeBrowsingForTrustedSourcesEnabled: Safe Browsing for trusted sources.
  safeBrowsingForTrustedSourcesEnabled: TYPE_BOOL
    true: Perform Safe Browsing checks on all downloaded files.
    false: Skip Safe Browsing checks for files downloaded from trusted sources.

chrome.users.SafeBrowsingProtectionLevel: Safe Browsing protection.
  safeBrowsingProtectionLevel: TYPE_ENUM
    USER_CHOICE: Allow the user to decide.
    NO_PROTECTION: Safe Browsing is never active.
    STANDARD_PROTECTION: Safe Browsing is active in the standard mode.
    ENHANCED_PROTECTION: Safe Browsing is active in the enhanced mode. This mode provides better security, but requires sharing more browsing information with Google.
  safeBrowsingProxiedRealTimeChecksAllowed: TYPE_BOOL
    true: Allow real time proxied checks.
    false: Don't allow real time proxied checks.
  safeBrowsingProtectionLevelCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.SafeBrowsingSurveysEnabled: Safe Browsing Surveys.
  safeBrowsingSurveysEnabled: TYPE_BOOL
    true: Allow Safe Browsing surveys to be sent to users.
    false: Disable Safe Browsing surveys.

chrome.users.SafeSearchRestrictedMode: SafeSearch and Restricted Mode.
  forceGoogleSafeSearch: TYPE_BOOL
    true: Always use SafeSearch for Google Search queries.
    false: Do not enforce SafeSearch for Google Search queries.
  forceYoutubeRestrictedMode: TYPE_ENUM
    OFF: Do not enforce Restricted Mode on YouTube.
    MODERATE: Enforce at least Moderate Restricted Mode on YouTube.
    STRICT: Enforce Strict Restricted Mode on YouTube.

chrome.users.SafeSitesFilterBehavior: SafeSites URL filter.
  safeSitesFilterBehavior: TYPE_ENUM
    SAFE_SITES_FILTER_DISABLED: Do not filter sites for adult content.
    SAFE_SITES_FILTER_ENABLED: Filter sites for adult content.

chrome.users.SamlLockScreenOfflineSigninTimeLimitDays: SAML single sign-on unlock frequency.
  samlLockScreenOfflineSigninTimeLimitDays: TYPE_INT64

chrome.users.SamlLockScreenReauthenticationEnabled: SAML single sign-on password synchronization flows.
  samlLockScreenReauthenticationEnabled: TYPE_BOOL
    true: Enforce online logins on the login and lock screen.
    false: Only enforce online logins on the login screen.

chrome.users.SandboxExternalProtocolBlocked: iframe navigation.
  sandboxExternalProtocolBlocked: TYPE_BOOL
    true: Do not allow navigation to external protocols inside a sandboxed iframe.
    false: Allow navigation to external protocols inside a sandboxed iframe.

chrome.users.ScreenBrightnessPercent: Screen brightness.
  brightnessEnabled: TYPE_BOOL
    true: Set initial screen brightness.
    false: Do not set initial screen brightness.
  brightnessAc: TYPE_INT64
    Screen brightness (ac power). Specifies the screen brightness percent when running on AC power.
  brightnessBattery: TYPE_INT64
    Screen brightness (battery power). Specifies the screen brightness percent when running on battery power.

chrome.users.ScreenCaptureAllowed: Screen video capture.
  screenCaptureAllowed: TYPE_BOOL
    true: Allow sites to prompt the user to share a video stream of their screen.
    false: Do not allow sites to prompt the user to share a video stream of their screen.

chrome.users.ScreenCaptureLocation: Screenshot location.
  screenCaptureLocation: TYPE_ENUM
    LOCAL_FOLDER_DEFAULT: Set local Downloads folder as default, but allow user to change.
    GOOGLE_DRIVE_DEFAULT: Set Google Drive as default, but allow user to change.
    GOOGLE_DRIVE_FORCED: Force Google Drive.
    ONEDRIVE_DEFAULT: Set OneDrive as default, but allow user to change.
    ONEDRIVE_FORCED: Force OneDrive.

chrome.users.ScreenCaptureWithoutGestureAllowedForOrigins: Media picker without user gesture.
  screenCaptureWithoutGestureAllowedForOrigins: TYPE_LIST
    Allow screen capture without prior user gesture. Urls to allow screencapture without user gesture.

chrome.users.ScreenMagnifierType: Screen magnifier.
  screenMagnifierType: TYPE_ENUM
    UNSET: Allow the user to decide.
    DISABLED: Disable screen magnifier.
    FULL_SCREEN: Enable full-screen magnifier.
    DOCKED: Enable docked magnifier.

chrome.users.Screenshot: Screenshot.
  disableScreenshots: TYPE_BOOL
    true: Do not allow users to take screenshots or video recordings.
    false: Allow users to take screenshots and video recordings.

chrome.users.ScrollToTextFragmentEnabled: Scroll to text fragment.
  scrollToTextFragmentEnabled: TYPE_BOOL
    true: Allow sites to scroll to specific text fragments via URL.
    false: Do not allow sites to scroll to specific text fragments via URL.

chrome.users.SearchSuggest: Search suggest.
  searchSuggestEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never allow users to use Search Suggest.
    TRUE: Always allow users to use Search Suggest.
  searchSuggestPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.SecondaryGoogleAccountSignin: Sign-in to secondary accounts.
  secondaryGoogleAccountSigninAllowed: TYPE_ENUM
    UNSET: Allow users to sign in to any secondary Google Accounts.
    FALSE: Block users from signing in to or out of secondary Google Accounts.
    TRUE: Allow users to only sign in to the Google Workspace domains set in 'allowedDomainsForApps'.
  allowedDomainsForApps: TYPE_LIST
    Whether the OS version updates will be set to a version defined in the manifest of a kiosk app.

chrome.users.SecondaryGoogleAccountUsage: Managed account as secondary account.
  secondaryGoogleAccountUsage: TYPE_ENUM
    ALL: All usages of managed accounts are allowed.
    PRIMARY_ACCOUNT_SIGNIN: Block addition of a managed account as secondary account (in-session).

chrome.users.SecurityKeyAttestation: Security key attestation.
  securityKeyPermitAttestation: TYPE_LIST
    Enter URL or domain. Specifies URLs and domains for which no prompt will be shown when attestation certificates from security keys are requested. Additionally, a signal will be sent to the security key indicating that individual attestation may be used. Without this, users will be prompted in Chrome 65+ when sites request attestation of security keys. URLs (like "https://example.com/some/path") will only match as U2F AppIDs. Domains (like "example.com") only match as WebAuthn RP IDs. Thus, to cover both U2F and WebAuthn APIs for a given site, both the AppID URL and domain would need to be listed.

chrome.users.SecurityTokenSessionSettings: Security token removal.
  securityTokenSessionBehavior: TYPE_ENUM
    IGNORE: Nothing.
    LOGOUT: Log the user out.
    LOCK: Lock the current session.
  securityTokenSessionNotificationSeconds: TYPE_INT64

chrome.users.SecurityTokenSessionSettingsV2: Security token removal.
  securityTokenSessionBehavior: TYPE_ENUM
    IGNORE: Nothing.
    LOGOUT: Log the user out.
    LOCK: Lock the current session.
  securityTokenSessionNotificationSeconds: TYPE_INT64

chrome.users.SelectToSpeakEnabled: Select to speak.
  selectToSpeakEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable select to speak.
    TRUE: Enable select to speak.

chrome.users.SendMouseEventsDisabledFormControlsEnabled: Disabled element MouseEvents.
  sendMouseEventsDisabledFormControlsEnabled: TYPE_BOOL
    true: Dispatch most MouseEvents from disabled control elements.
    false: Do not dispatch MouseEvents from disabled control elements.

chrome.users.SerialAllowUsbDevicesForUrls: Web Serial API allowed devices.
  serialAllowUsbDevicesForUrls
    webOrigin
      url: TYPE_STRING
      device: TYPE_LIST

chrome.users.ServiceWorkerToControlSrcdocIframeEnabled: Service worker control of srcdoc iframes.
  serviceWorkerToControlSrcdocIframeEnabled: TYPE_BOOL
    true: Allow service workers to control srcdoc iframes.
    false: Block service workers from controlling srcdoc iframes.

chrome.users.SessionLength: Maximum user session length.
  sessionDurationLimit: TYPE_INT64

chrome.users.SessionLengthV2: Maximum user session length.
  sessionDurationLimit: TYPE_INT64

chrome.users.SetTimeoutWithoutOneMsClampEnabled: Javascript setTimeout() minimum.
  setTimeoutWithoutOneMsClampEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Javascript setTimeout() with a timeout of 0ms will clamp to 1ms.
    TRUE: Javascript setTimeout() with a timeout of 0ms will not clamp to 1ms.

chrome.users.SharedArrayBufferUnrestrictedAccessAllowed: SharedArrayBuffer.
  sharedArrayBufferUnrestrictedAccessAllowed: TYPE_BOOL
    true: Allow sites that are not cross-origin isolated to use SharedArrayBuffers.
    false: Prevent sites that are not cross-origin isolated from using SharedArrayBuffers.

chrome.users.SharedClipboardEnabled: Shared clipboard.
  sharedClipboardEnabled: TYPE_BOOL
    true: Enable the shared clipboard feature.
    false: Disable the shared clipboard feature.

chrome.users.SharedWorkerBlobUrlFixEnabled: SharedWorker.
  sharedWorkerBlobUrlFixEnabled: TYPE_BOOL
    true: SharedWorker blob URL inherits controller.
    false: SharedWorker blob URL does not inherit controller.

chrome.users.ShelfAlign: Shelf position.
  shelfAlignment: TYPE_ENUM
    USER_CHOICE: Allow the user to decide.
    BOTTOM: Bottom.
    LEFT: Left.
    RIGHT: Right.

chrome.users.ShelfAutoHideBehavior: Shelf auto-hiding.
  shelfAutoHideBehavior: TYPE_ENUM
    USER_CHOICE: Allow the user to decide.
    ALWAYS_AUTO_HIDE_SHELF: Always auto-hide the shelf.
    NEVER_AUTO_HIDE_SHELF: Never auto-hide the shelf.

chrome.users.ShoppingListEnabled: Shopping list.
  shoppingListEnabled: TYPE_BOOL
    true: Enable the shopping list feature.
    false: Disable the shopping list feature.

chrome.users.ShortcutCustomizationAllowed: Customization of system shortcuts.
  shortcutCustomizationAllowed: TYPE_BOOL
    true: Allow the user to customize system shortcuts.
    false: Disallow the user to customize system shortcuts.

chrome.users.ShowAccessibilityOptionsInSystemTrayMenu: Accessibility options in the system tray menu.
  showAccessibilityOptionsInSystemTrayMenu: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Hide accessibility options in the system tray menu.
    TRUE: Show accessibility options in the system tray menu.

chrome.users.ShowAiIntroScreenEnabled: AI feature introduction during sign-in.
  showAiIntroScreenEnabled: TYPE_ENUM
    UNSET: Use the default Chrome behavior.
    FALSE: Do not display the AI introduction screen during sign-in.
    TRUE: Display the AI introduction screen during sign-in.

chrome.users.ShowAppsShortcutInBookmarkBar: Apps shortcut in the bookmark bar.
  showAppsShortcutInBookmarkBar: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Hide the apps shortcut from the bookmark bar.
    TRUE: Show the apps shortcut in the bookmark bar.

chrome.users.ShowCastSessionsStartedByOtherDevices: Show media controls for Google Cast sessions started by other devices on the local network.
  showCastSessionsStartedByOtherDevices: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not show media controls for Google Cast sessions started by other devices.
    TRUE: Show media controls for Google Cast sessions started by other devices.

chrome.users.ShowDisplaySizeScreenEnabled: Display size setting during sign-in.
  showDisplaySizeScreenEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Do not display the display size setting screen during sign-in.
    TRUE: Display the display size setting screen during sign-in.

chrome.users.ShowFullUrlsInAddressBar: URLs in the address bar.
  showFullUrlsInAddressBar: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Display the default URL.
    TRUE: Display the full URL.
  showFullUrlsInAddressBarCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.ShowGeminiIntroScreenEnabled: Gemini introduction during sign-in.
  showGeminiIntroScreenEnabled: TYPE_ENUM
    UNSET: Use the default Chrome behavior.
    FALSE: Do not display the Gemini introduction screen during sign-in.
    TRUE: Display the Gemini introduction screen during sign-in.

chrome.users.ShowLogoutButton: Show sign-out button in tray.
  showLogoutButtonInTray: TYPE_BOOL
    true: Show sign-out button in tray.
    false: Do not show sign-out button in tray.

chrome.users.ShowTouchpadScrollScreenEnabled: Touchpad scroll setting during sign-in.
  showTouchpadScrollScreenEnabled: TYPE_BOOL
    true: Display the touchpad scroll direction screen during sign-in.
    false: Do not display the touchpad scroll direction screen during sign-in.

chrome.users.SideSearchEnabled: Side Panel search history.
  sideSearchEnabled: TYPE_BOOL
    true: Enable showing the most recent Google Search results in a Browser side panel.
    false: Disable showing the most recent Google Search results in a Browser side panel.

chrome.users.SignedHttpExchangeEnabled: Signed HTTP Exchange (SXG) support.
  signedHttpExchangeEnabled: TYPE_BOOL
    true: Accept web content served as Signed HTTP Exchanges.
    false: Prevent Signed HTTP Exchanges from loading.

chrome.users.SigninInterceptionEnabled: Signin interception.
  signinInterceptionEnabled: TYPE_BOOL
    true: Enable signin interception.
    false: Disable signin interception.

chrome.users.SimpleProxySettings: Proxy mode.
  simpleProxyMode: TYPE_ENUM
    USER_CONFIGURED: Allow user to configure.
    DIRECT: Never use a proxy.
    SYSTEM: Use system proxy settings.
    AUTO_DETECT: Always auto detect the proxy.
    FIXED_SERVERS: Always use the proxy specified in 'simpleProxyServerUrl'.
    PAC_SCRIPT: Always use the proxy auto-config specified in 'simpleProxyPacUrl'.
  simpleProxyServerUrl: TYPE_STRING
    Proxy server URL. Specifies the URL of a proxy server to uesr on administered devices.
  simpleProxyPacUrl: TYPE_STRING
    Proxy server auto configuration file URL. URL of the .pac file that should be used for network connections.
  proxyBypassList: TYPE_LIST
    URLs which bypass the proxy. Specifies a list of URLs that will not user the configured proxy server.

chrome.users.SingleSignOn: Single sign-on.
  idpRedirectEnabled: TYPE_BOOL
    true: Enable SAML-based single sign-on for Chrome devices.
    false: Disable SAML-based single sign-on for Chrome devices.

chrome.users.SingleSignOnLoginFrequency: SAML single sign-on login frequency.
  samlOfflineSigninTimeLimit: TYPE_ENUM
    SAML_ONE_DAY: Every day.
    SAML_THREE_DAYS: Every 3 days.
    SAML_ONE_WEEK: Every week.
    SAML_TWO_WEEKS: Every 2 weeks.
    SAML_THREE_WEEKS: Every 3 weeks.
    SAML_FOUR_WEEKS: Every 4 weeks.
    EVERY_TIME: Every Time.
    SAML_NEVER: Never.

chrome.users.SingleSignOnPasswordSynchronization: SAML single sign-on password synchronization.
  samlInSessionPasswordChangeEnabled: TYPE_BOOL
    true: Trigger authentication flows to synchronize passwords with SSO providers.
    false: Do not trigger authentication flows for password synchronization.
  samlPasswordExpirationAdvanceWarningDays: TYPE_INT64
    How many days in advance to notify SAML users when their password is due to expire. 0–90 days. A value of 0 means users will not be notified in advance, but will only be notified once the password has already expired.

chrome.users.SiteIsolationAndroid: Site isolation (Chrome on Android).
  sitePerProcessAndroid: TYPE_ENUM
    UNSET: Turn on site isolation only for login sites, as well as any origins specified in 'isolateOriginsAndroid'.
    FALSE: Turn off site isolation for all websites, except those set in 'isolateOriginsAndroid'.
    TRUE: Turn on site isolation for all websites, as well as any origins specified in 'isolateOriginsAndroid'.
  isolateOriginsAndroid: TYPE_LIST
    Isolated origins (Android). Enter a list of origins to isolate within a website on Android, for instance https://login.example.com or https://[*.]example.com.

chrome.users.SiteIsolationBrowser: Site isolation.
  isolateOrigins: TYPE_LIST
    Isolated origins. Enter a list of origins to isolate within a website, for instance https://login.example.com or https://[*.]example.com. .
  sitePerProcess: TYPE_BOOL
    true: Require site isolation for all websites, as well as any origins specified in 'isolateOrigins'.
    false: Turn off site isolation for all websites, except those set in 'isolateOrigins'.

chrome.users.SiteSearchSettings: Site search.
  siteSearchSettings
    siteSearchEngines
      featured: TYPE_BOOL
      name: TYPE_STRING
      shortcut: TYPE_STRING
      url: TYPE_STRING
      allowUserOverride: TYPE_BOOL

chrome.users.SmartLockAllowed: Smart Lock.
  smartLockAllowed: TYPE_BOOL
    true: Allow Smart Lock.
    false: Do not allow Smart Lock.

chrome.users.SmartScreenDimDelay: Delay screen dim on user activity.
  userActivityScreenDimDelayScale: TYPE_INT64
    Scale percent for screen dim delay on user activity. Controls the percent that the screen dim delay scales when there's user activity while the screen dims or soon after the screen turns off.
  presentationScreenDimDelayScale: TYPE_INT64
    Scale percent for screen dim delay when presenting. Controls the percent that the screen dim delay scales when the device is presenting.
  powerSmartDimEnabled: TYPE_BOOL
    true: Enable smart dim model.
    false: Disable smart dim model.

chrome.users.SmsMessagesAllowed: Messages.
  smsMessagesAllowed: TYPE_BOOL
    true: Allow users to sync SMS messages between their phone and Chromebook.
    false: Do not allow users to sync SMS messages between their phone and Chromebook.

chrome.users.SpellcheckEnabled: Spell check.
  spellcheckEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable spell check.
    TRUE: Enable spell check.
  spellcheckLanguage: TYPE_LIST
    af: Afrikaans.
    sq: Albanian - ‪shqip‬.
    hy: Armenian - ‪հայերեն‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fo: Faroese - ‪føroyskt‬.
    fr: French - ‪Français‬.
    fr-FR: French (France) - ‪Français (France)‬.
    de: German - ‪Deutsch‬.
    de-DE: German (Germany) - ‪Deutsch (Deutschland)‬.
    el: Greek - ‪Ελληνικά‬.
    he: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    it-IT: Italian (Italy) - ‪Italiano (Italia)‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    nb: Norwegian Bokmål - ‪norsk bokmål‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt: Portuguese - ‪Português‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sh: Serbo-Croatian - ‪srpskohrvatski‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es: Spanish - ‪Español‬.
    es-AR: Spanish (Argentina) - ‪Español (Argentina)‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es-MX: Spanish (Mexico) - ‪Español (México)‬.
    es-ES: Spanish (Spain) - ‪Español (España)‬.
    es-US: Spanish (United States) - ‪Español (Estados Unidos)‬.
    sv: Swedish - ‪Svenska‬.
    tg: Tajik - ‪тоҷикӣ‬.
    ta: Tamil - ‪தமிழ்‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.
  spellcheckLanguageBlocklist: TYPE_LIST
    af: Afrikaans.
    sq: Albanian - ‪shqip‬.
    hy: Armenian - ‪հայերեն‬.
    bg: Bulgarian - ‪български‬.
    ca: Catalan - ‪català‬.
    hr: Croatian - ‪Hrvatski‬.
    cs: Czech - ‪Čeština‬.
    da: Danish - ‪Dansk‬.
    nl: Dutch - ‪Nederlands‬.
    en-AU: English (Australia).
    en-CA: English (Canada).
    en-GB: English (United Kingdom).
    en-US: English (United States).
    et: Estonian - ‪eesti‬.
    fo: Faroese - ‪føroyskt‬.
    fr: French - ‪Français‬.
    fr-FR: French (France) - ‪Français (France)‬.
    de: German - ‪Deutsch‬.
    de-DE: German (Germany) - ‪Deutsch (Deutschland)‬.
    el: Greek - ‪Ελληνικά‬.
    he: Hebrew - ‫עברית‬.
    hi: Hindi - ‪हिन्दी‬.
    hu: Hungarian - ‪magyar‬.
    id: Indonesian - ‪Indonesia‬.
    it: Italian - ‪Italiano‬.
    it-IT: Italian (Italy) - ‪Italiano (Italia)‬.
    ko: Korean - ‪한국어‬.
    lv: Latvian - ‪latviešu‬.
    lt: Lithuanian - ‪lietuvių‬.
    nb: Norwegian Bokmål - ‪norsk bokmål‬.
    fa: Persian - ‫فارسی‬.
    pl: Polish - ‪polski‬.
    pt: Portuguese - ‪Português‬.
    pt-BR: Portuguese (Brazil) - ‪Português (Brasil)‬.
    pt-PT: Portuguese (Portugal) - ‪Português (Portugal)‬.
    ro: Romanian - ‪română‬.
    ru: Russian - ‪Русский‬.
    sr: Serbian - ‪српски‬.
    sh: Serbo-Croatian - ‪srpskohrvatski‬.
    sk: Slovak - ‪Slovenčina‬.
    sl: Slovenian - ‪slovenščina‬.
    es: Spanish - ‪Español‬.
    es-AR: Spanish (Argentina) - ‪Español (Argentina)‬.
    es-419: Spanish (Latin America) - ‪Español (Latinoamérica)‬.
    es-MX: Spanish (Mexico) - ‪Español (México)‬.
    es-ES: Spanish (Spain) - ‪Español (España)‬.
    es-US: Spanish (United States) - ‪Español (Estados Unidos)‬.
    sv: Swedish - ‪Svenska‬.
    tg: Tajik - ‪тоҷикӣ‬.
    ta: Tamil - ‪தமிழ்‬.
    tr: Turkish - ‪Türkçe‬.
    uk: Ukrainian - ‪Українська‬.
    vi: Vietnamese - ‪Tiếng Việt‬.
    cy: Welsh - ‪Cymraeg‬.

chrome.users.SpellCheckService: Spell check service.
  spellCheckServiceEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable the spell checking web service.
    TRUE: Enable the spell checking web service.
  spellCheckServicePolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.SpokenFeedbackEnabled: Spoken feedback.
  spokenFeedbackEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable spoken feedback.
    TRUE: Enable spoken feedback.

chrome.users.SslErrorOverrideAllowed: SSL error override.
  sslErrorOverrideAllowed: TYPE_BOOL
    true: Allow users to click through SSL warnings and proceed to the page.
    false: Block users from clicking through SSL warnings.

chrome.users.SslErrorOverrideAllowedForOrigins: SSL error override allowed domains.
  sslErrorOverrideAllowedForOrigins: TYPE_LIST
    Domains that allow clicking through SSL warnings. Enter a list of domain names.

chrome.users.SslVersionMin: Minimum SSL version enabled.
  sslVersionMin: TYPE_ENUM
    TL_SV_1: TLS 1.0.
    TL_SV_1_1: TLS 1.1.
    TL_SV_1_2: TLS 1.2.
    SSL_V_3: SSL3.

chrome.users.StandardizedBrowserZoomEnabled: Zoom Behavior.
  standardizedBrowserZoomEnabled: TYPE_BOOL
    true: Standard CSS zoom.
    false: Legacy CSS zoom.

chrome.users.StartupPages: Pages to load on startup.
  restoreOnStartupUrls: TYPE_LIST
    Startup pages. Example: https://example.com.
  restoreOnStartup: TYPE_ENUM
    UNSET: Allow the user to decide.
    NEW_TAB: Open New Tab page.
    RESTORE_SESSION: Restore the last session.
    LIST_OF_URLS: Open a list of URLs.
    LIST_OF_URLS_AND_RESTORE_SESSION: Open a list of URLs and restore the last session.

chrome.users.StickyKeysEnabled: Sticky keys.
  stickyKeysEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Disable sticky keys.
    TRUE: Enable sticky keys.

chrome.users.StrictMimetypeCheckForWorkerScriptsEnabled: Strict MIME type checking for worker scripts.
  strictMimetypeCheckForWorkerScriptsEnabled: TYPE_BOOL
    true: Require a JavaScript MIME type for worker scripts.
    false: Use lax MIME type checking for worker scripts.

chrome.users.SuggestedContentEnabled: Suggested content.
  suggestedContentEnabled: TYPE_BOOL
    true: Enable suggested content.
    false: Disable suggested content.

chrome.users.SuppressCrossOriginIframeDialogs: Cross-origin JavaScript dialogs.
  suppressCrossOriginIframeDialogs: TYPE_BOOL
    true: Block JavaScript dialogs triggered from a cross-origin iframe.
    false: Allow JavaScript dialogs triggered from a cross-origin iframe.

chrome.users.SuppressUnsupportedOsWarning: Unsupported system warning.
  suppressUnsupportedOsWarning: TYPE_BOOL
    true: Suppress warnings when Chrome is running on an unsupported system.
    false: Allow Chrome to display warnings when running on an unsupported system.

chrome.users.SyncSettingsCbcm: Chrome Sync and Roaming Profiles (Chrome Browser - Cloud Managed).
  syncTypeCbcm: TYPE_ENUM
    SYNC_CLOUD_DEFAULT_VALUE: Allow Chrome Sync.
    SYNC_ROAMING_PROFILES: Allow Roaming Profiles.
    SYNC_DISABLED: Disallow Sync.
  syncTypesListDisabledCbcm: TYPE_LIST
    apps: Apps.
    autofill: Autofill.
    bookmarks: Bookmarks.
    extensions: Extensions.
    typedUrls: History.
    passwords: Passwords.
    readingList: Reading list.
    preferences: Settings.
    themes: Themes & Wallpapers.
    tabs: Open tabs.
    wifiConfiguration: WiFi configurations.
  clearBrowsingDataOnExitListCbcm: TYPE_LIST
    browsing_history: Browsing history.
    download_history: Download history.
    cookies_and_other_site_data: Cookies and other site data.
    cached_images_and_files: Cached images and files.
    password_signin: Passwords.
    autofill: Autofill.
    site_settings: Site settings.
    hosted_app_data: Hosted app data.
  roamingProfileLocationCbcm: TYPE_STRING
    Roaming profile directory. Configures the directory that Google Chrome will use for storing the roaming copy of the profiles.
  profileReauthPrompt: TYPE_ENUM
    DO_NOT_PROMPT: Do not prompt for re-authentication after authentication expiration.
    PROMPT_IN_TAB: Prompt for re-authentication in a tab after authentication expiration.

chrome.users.SyncSettingsCros: Chrome Sync (ChromeOS).
  syncDisabledCros: TYPE_BOOL
    true: Disable Chrome Sync.
    false: Allow Chrome Sync.
  syncTypesListDisabledCros: TYPE_LIST
    apps: Apps.
    autofill: Autofill.
    bookmarks: Bookmarks.
    extensions: Extensions.
    typedUrls: History.
    passwords: Passwords.
    readingList: Reading list.
    preferences: Settings.
    themes: Themes & Wallpapers.
    tabs: Open tabs.
    wifiConfiguration: WiFi configurations.
  clearBrowsingDataOnExitListCros: TYPE_LIST
    browsing_history: Browsing history.
    download_history: Download history.
    cookies_and_other_site_data: Cookies and other site data.
    cached_images_and_files: Cached images and files.
    password_signin: Passwords.
    autofill: Autofill.
    site_settings: Site settings.
    hosted_app_data: Hosted app data.
  passwordSharingEnabled: TYPE_BOOL
    true: Allow sharing user credentials with family members.
    false: Do not allow sharing user credentials with family members.

chrome.users.SystemFeaturesDisableList: Disabled system features.
  systemFeaturesDisableList: TYPE_LIST
    camera: Camera.
    os_settings: OS settings.
    browser_settings: Browser settings.
    scanning: Scanning.
    crosh: Crosh.
    recorder: Recorder.

chrome.users.SystemShortcutBehavior: Override system shortcuts.
  systemShortcutBehavior: TYPE_ENUM
    DEFAULT: Do not override system shortcuts.
    SHOULD_IGNORE_COMMON_VDI_SHORTCUTS: Override some system shortcuts.
    SHOULD_IGNORE_COMMON_VDI_SHORTCUTS_FULLSCREEN_ONLY: Override some system shortcuts while in fullscreen.
    ALLOW_PASSTHROUGH_OF_SEARCH_BASED_SHORTCUTS: Prioritize active app over OS for Search key shortcuts.
    ALLOW_PASSTHROUGH_OF_SEARCH_BASED_SHORTCUTS_FULLSCREEN_ONLY: Prioritize active app over OS for Search key shortcuts while in fullscreen.

chrome.users.SystemTerminalSshAllowed: SSH in terminal system app.
  systemTerminalSshAllowed: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable SSH in Terminal System App.
    TRUE: Enable SSH in Terminal System App.

chrome.users.TabCompareSettings: Tab compare.
  tabCompareSettings: TYPE_ENUM
    ALLOWED: Allow tab compare and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow tab compare without improving AI models.
    DISABLED: Do not allow tab compare.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.TabDiscardingExceptions: Exceptions to tab discarding.
  tabDiscardingExceptions: TYPE_LIST
    URL pattern exceptions to tab discarding. Specifies URL patterns where any URL matching one or more of these patterns will never be discarded by the browser.

chrome.users.TabOrganizerSettings: Tab organizer.
  tabOrganizerSettings: TYPE_ENUM
    ALLOWED: Allow tab organizer and improve AI models.
    ALLOWED_WITHOUT_LOGGING: Allow tab organizer without improving AI models.
    DISABLED: Do not allow tab organizer.
    UNSET: Use the value specified in the Generative AI policy defaults setting.

chrome.users.TargetBlankImpliesNoOpener: Pop-up interactions.
  targetBlankImpliesNoOpener: TYPE_BOOL
    true: Block pop-ups opened with a target of _blank from interacting with the page that opened the pop-up.
    false: Allow pop-ups opened with a target of _blank to interact with the page that opened the pop-up.

chrome.users.TaskManager: Task manager.
  taskManagerEndProcessEnabled: TYPE_BOOL
    true: Allow users to end processes with the Chrome task manager.
    false: Block users from ending processes with the Chrome task manager.

chrome.users.ThirdPartyBlockingEnabled: Third party code.
  thirdPartyBlockingEnabled: TYPE_BOOL
    true: Prevent third party code from being injected into Chrome.
    false: Allow third party code to be injected into Chrome.

chrome.users.ThirdPartyCookieBlocking: Third-party cookie blocking.
  blockThirdPartyCookies: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Allow third-party cookies.
    TRUE: Disallow third-party cookies.

chrome.users.ThirdPartyPasswordManagersAllowed: Third-party password managers allowed.
  thirdPartyPasswordManagersAllowed: TYPE_BOOL
    true: Allow using third-party password managers in Chrome.
    false: Block using third-party password managers in Chrome.

chrome.users.ThirdPartyStoragePartitioningSettings: Third-party storage partitioning.
  defaultThirdPartyStoragePartitioningSetting: TYPE_ENUM
    ALLOW_PARTITIONING: Allow third-party storage partitioning to be enabled.
    BLOCK_PARTITIONING: Block third-party storage partitioning from being enabled.
  thirdPartyStoragePartitioningBlockedForOrigins: TYPE_LIST
    Block third-party storage partitioning for these origins. Specifies top-level origins which block third-party storage partitioning.

chrome.users.ThreeDContent: 3D content.
  disableThreeDApis: TYPE_BOOL
    true: Never allow display of 3D content.
    false: Always allow display of 3D content.

chrome.users.ThrottleNonVisibleCrossOriginIframesAllowed: Throttling of non-visible, cross-origin iframes.
  throttleNonVisibleCrossOriginIframesAllowed: TYPE_BOOL
    true: Enable throttling.
    false: Disable throttling.

chrome.users.TotalMemoryLimitMb: Chrome browser memory limit.
  totalMemoryLimitMb: TYPE_INT64
    Memory consumption limit in MB (minimum 1024). Sets a limit on megabytes of memory a single Chrome instance can use.

chrome.users.TouchVirtualKeyboardEnabled: Touch on-screen keyboard.
  touchVirtualKeyboardEnabled: TYPE_ENUM
    UNSET: Enable touch on-screen keyboard in tablet mode.
    FALSE: Don't enable touch on-screen keyboard in tablet mode.
    TRUE: Enable touch on-screen keyboard in both tablet and laptop modes.

chrome.users.Translate: Google Translate.
  translateEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Never offer translation.
    TRUE: Always offer translation.
  translatePolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.TranslatorApiAllowed: Translator API.
  translatorApiAllowed: TYPE_BOOL
    true: Allow the use of Translator API in Google Chrome.
    false: Disallow the use of Translator API in Google Chrome.

chrome.users.TrashEnabled: Trashed files.
  trashEnabled: TYPE_BOOL
    true: Allow files to be sent to the Trash bin in the Files app.
    false: Do not allow files to be sent to the Trash bin in the Files app.

chrome.users.TripleDesEnabled: 3DES cipher suites in TLS.
  tripleDesEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable 3DES cipher suites in TLS.
    TRUE: Enable 3DES cipher suites in TLS.

chrome.users.UiAutomationProviderEnabled: UI Automation accessibility provider.
  uiAutomationProviderEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: Disable the UI Automation provider.
    TRUE: Enable the UI Automation provider.

chrome.users.UnifiedDesktop: Unified Desktop (BETA).
  unifiedDesktopEnabledByDefault: TYPE_BOOL
    true: Make Unified Desktop mode available to user.
    false: Do not make Unified Desktop mode available to user.

chrome.users.UnmanagedDeviceSignalsConsentFlowEnabled: User consent to share device signals.
  unmanagedDeviceSignalsConsentFlowEnabled: TYPE_BOOL
    true: Ask for consent to share signals on unmanaged devices.
    false: Do not ask for consent to share signals on unmanaged devices.

chrome.users.UnthrottledNestedTimeoutEnabled: JavaScript setTimeout() clamping.
  unthrottledNestedTimeoutEnabled: TYPE_ENUM
    UNSET: Use the default Chrome setting.
    FALSE: JavaScript setTimeout() will be clamped after a normal nesting threshold.
    TRUE: JavaScript setTimeout() will not be clamped as aggressively.

chrome.users.UpdatesSuppressed: Suppress auto-update check.
  updatesSuppressedDurationMin: TYPE_INT64
    Duration (minutes). Auto-update checks will begin to be suppressed at the start time specified in 'updatesSuppressedStartTime', for the duration specified here, in minutes. This duration does not take into account daylight savings time.
  updatesSuppressedStartTime
    timeOfDay
      hours: TYPE_INT32
      minutes: TYPE_INT32
      seconds: TYPE_INT32
      nanos: TYPE_INT32

chrome.users.UrlBlocking: URL blocking.
  urlBlocklist: TYPE_LIST
    Blocked URLs. Any URL in this list will be blocked, unless it also appears in the list of exceptions specified in 'urlAllowlist'. Maximum of 1000 URLs.
  urlAllowlist: TYPE_LIST
    Blocked URL exceptions. Any URL that matches an entry in this exception list will be allowed, even if it matches an entry in the blocked URLs. Wildcards ("*") are allowed when appended to a URL, but cannot be entered alone. Maximum of 1000 URLs. .
  chromeInternalUrlsBlocked: TYPE_BOOL
    true: Block sensitive internal Chrome URLs.
    false: Do not block sensitive internal Chrome URLs.

chrome.users.UrlKeyedAnonymizedDataCollectionEnabled: Enable URL-keyed anonymized data collection.
  urlKeyedAnonymizedDataCollectionEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Data collection is never active.
    TRUE: Data collection is always active.

chrome.users.UrlParamFilterEnabled: URL parameter filtering.
  urlParamFilterEnabled: TYPE_BOOL
    true: Allow the browser to filter URL parameters.
    false: Disallow any filtering of URL parameters.

chrome.users.UsbDetectorNotificationEnabled: USB device detected notification.
  usbDetectorNotificationEnabled: TYPE_BOOL
    true: Show notifications when USB devices are detected.
    false: Do not show notifications when USB devices are detected.

chrome.users.UseMojoVideoDecoderForPepperAllowed: Use a new decoder for hardware accelerated video decoding.
  useMojoVideoDecoderForPepperAllowed: TYPE_BOOL
    true: Allow Pepper to use the new video decoder.
    false: Force Pepper to use the legacy video decoder.

chrome.users.UserAgentClientHintsEnabled: User-Agent client hints.
  userAgentClientHintsEnabled: TYPE_BOOL
    true: Allow User-Agent client hints.
    false: Disable User-Agent client hints.

chrome.users.UserAgentClientHintsGreaseUpdateEnabled: User-Agent Client Hints GREASE Update.
  userAgentClientHintsGreaseUpdateEnabled: TYPE_BOOL
    true: Allow the updated User-Agent GREASE algorithm to be run.
    false: Force the prior User-Agent GREASE algorithm to be used.

chrome.users.UserAgentReduction: User-Agent Reduction.
  userAgentReduction: TYPE_ENUM
    DEFAULT: Allow reduction controlled via Field-Trials and Origin-Trials.
    FORCE_DISABLED: Disable reduction for all origins.
    FORCE_ENABLED: Enable reduction for all origins.

chrome.users.UserAvatarCustomizationSelectorsEnabled: Customization of user avatar image using Google profile image or local images.
  userAvatarCustomizationSelectorsEnabled: TYPE_BOOL
    true: Allow user avatar selection from local filesystem, camera and Google profile.
    false: Prevent user avatar selection from local filesystem, camera and Google profile.

chrome.users.UserBorealisAllowed: Steam on ChromeOS.
  userBorealisAllowed: TYPE_BOOL
    true: Allow Steam on ChromeOS.
    false: Do not allow Steam on ChromeOS.

chrome.users.UserDataSnapshotRetentionLimit: User data snapshot limits.
  userDataSnapshotRetentionLimit: TYPE_INT64
    The maximum number of user data snapshots retained. Set to 0 to disable taking snapshots.

chrome.users.UserDownloadDirectory: Download location.
  downloadDirectory: TYPE_ENUM
    LOCAL_FOLDER_DEFAULT: Set local Downloads folder as default, but allow user to change.
    GOOGLE_DRIVE_DEFAULT: Set Google Drive as default, but allow user to change.
    GOOGLE_DRIVE_FORCED: Force Google Drive.
    ONEDRIVE_DEFAULT: Set OneDrive as default, but allow user to change.
    ONEDRIVE_FORCED: Force OneDrive.

chrome.users.UserEnrollmentNudging: Initial sign-in.
  userEnrollmentNudging: TYPE_ENUM
    NONE: Don't require users to enroll device.
    ENROLLMENT_REQUIRED: Require users to enroll device.

chrome.users.UserFeedbackAllowed: Allow user feedback.
  userFeedbackAllowed: TYPE_BOOL
    true: Allow user feedback.
    false: Do not allow user feedback.

chrome.users.UserPrintersAllowed: Printer management.
  userPrintersAllowed: TYPE_BOOL
    true: Allow users to add new printers.
    false: Do not allow users to add new printers.

chrome.users.UTwoFSecurityKeyApiEnabled: U2F Security Key API.
  uTwoFSecurityKeyApiEnabled: TYPE_BOOL
    true: Allow use of the deprecated U2F Security Key API.
    false: Apply default settings for U2F API deprecation.

chrome.users.Variations: Variations.
  variationsEnabled: TYPE_ENUM
    ENABLED: Enable Chrome variations.
    CRITICAL_FIXES_ONLY: Enable variations for critical fixes only.
    DISABLED: Disable variations.

chrome.users.VerifiedMode: Verified Mode.
  userVerifiedModeRequired: TYPE_BOOL
    true: Require verified mode boot for Verified Access.
    false: Skip boot mode check for Verified Access.
  servicesWithFullAccess: TYPE_LIST
    Service accounts which are allowed to receive user data. Service accounts allowed to receive user data.
  servicesWithLimitedAccess: TYPE_LIST
    Service accounts which can verify users but do not receive user data. Service accounts which can verify users but do not receive user data.

chrome.users.VideoCaptureAllowedUrls: Video input allowed URLs.
  videoCaptureAllowedUrls: TYPE_LIST
    URL patterns to allow. URLs that will be granted access to the video input device without a prompt. Prefix domain with [*.] to include subdomains.

chrome.users.VideoInput: Built-in camera access.
  videoCaptureAllowed: TYPE_BOOL
    true: Enable camera input for websites and apps.
    false: Disable camera input for websites and apps.

chrome.users.VirtualKeyboardEnabled: Accessibility on-screen keyboard.
  virtualKeyboardEnabled: TYPE_ENUM
    UNSET: Allow the user to decide.
    FALSE: Don't enable accessibility on-screen keyboard.
    TRUE: Enable accessibility on-screen keyboard.

chrome.users.VirtualKeyboardResizesLayoutByDefault: Virtual keyboard resizes the viewport.
  virtualKeyboardResizesLayoutByDefault: TYPE_BOOL
    true: The layout viewport is resized by the virtual keyboard.
    false: The viewport is not modified by the virtual keyboard.

chrome.users.VirtualMachinesAllowed: Linux virtual machines.
  virtualMachinesAllowed: TYPE_BOOL
    true: Allow usage for virtual machines needed to support Linux apps for users.
    false: Block usage for virtual machines needed to support Linux apps for users.

chrome.users.VirtualMachinesAndroidAdbSideloadingAllowed: Android apps from untrusted sources.
  virtualMachinesAndroidAdbSideloadingAllowed: TYPE_ENUM
    DISALLOW: Prevent the user from using Android apps from untrusted sources.
    ALLOW: Allow the user to use Android apps from untrusted sources.

chrome.users.VirtualMachinesBackupRestoreUiAllowed: Linux virtual machine backup and restore.
  virtualMachinesBackupRestoreUiAllowed: TYPE_BOOL
    true: Enable Linux virtual machine backup and restore.
    false: Disable Linux virtual machine backup and restore.

chrome.users.VirtualMachinesCommandLineAccessAllowed: Command line access.
  virtualMachinesCommandLineAccessAllowed: TYPE_BOOL
    true: Enable VM command line access.
    false: Disable VM command line access.

chrome.users.VirtualMachinesPortForwardingAllowed: Port forwarding.
  virtualMachinesPortForwardingAllowed: TYPE_BOOL
    true: Allow users to enable and configure port forwarding into the VM container.
    false: Do not allow users to enable and configure port forwarding into the VM container.

chrome.users.WaitForInitialUserActivity: Wait for initial user activity.
  waitForInitialUserActivity: TYPE_BOOL
    true: Start power management delays and session length limits after initial user activity.
    false: Start power management delays and session length limits at session start.

chrome.users.Wallpaper: Custom wallpaper.
  wallpaperImage
    downloadUri: TYPE_STRING

chrome.users.WallpaperGooglePhotosIntegrationEnabled: Wallpaper selection from Google Photos.
  wallpaperGooglePhotosIntegrationEnabled: TYPE_BOOL
    true: Allow Google Photos access from personalization app.
    false: Prevent Google Photos access from personalization app.

chrome.users.WarnBeforeQuittingEnabled: Warn before quitting.
  warnBeforeQuittingEnabled: TYPE_BOOL
    true: Show a warning dialog when the user is attempting to quit.
    false: Do not show a warning dialog when the user is attempting to quit.
  warnBeforeQuittingEnabledCategoryItemPolicyMode: TYPE_ENUM
    MANDATORY: Do not allow users to override.
    RECOMMENDED: Allow users to override.

chrome.users.WebAudioOutputBufferingEnabled: Adaptive buffering for Web Audio.
  webAudioOutputBufferingEnabled: TYPE_BOOL
    true: Enable web audio adaptive buffering.
    false: Disable web audio adaptive buffering.

chrome.users.WebAuthnFactors: WebAuthn.
  webAuthnFactors: TYPE_LIST
    PIN: PIN.
    FINGERPRINT: Fingerprint.

chrome.users.WebBluetoothAccess: Web Bluetooth API.
  defaultWebBluetoothGuardSetting: TYPE_ENUM
    UNSET: Allow the user to decide.
    BLOCK_WEB_BLUETOOTH: Do not allow sites to request access to Bluetooth devices via the Web Bluetooth API.
    ASK_WEB_BLUETOOTH: Allow sites to request access to Bluetooth devices via the Web Bluetooth API.

chrome.users.WebHidAllowDevicesForUrls: WebHID API allowed devices.
  webHidAllowDevicesForUrls
    webOrigin
      url: TYPE_STRING
      device: TYPE_LIST

chrome.users.WebRtcAllowLegacyTlsProtocols: Legacy TLS/DTLS downgrade in WebRTC.
  webRtcAllowLegacyTlsProtocols: TYPE_BOOL
    true: Enable WebRTC peer connections downgrading to obsolete versions of the TLS/DTLS (DTLS 1.0, TLS 1.0 and TLS 1.1) protocols.
    false: Disable WebRTC peer connections downgrading to obsolete versions of the TLS/DTLS (DTLS 1.0, TLS 1.0 and TLS 1.1) protocols.

chrome.users.WebrtcEventLogCollectionAllowed: WebRTC event log collection.
  webRtcEventLogCollectionAllowed: TYPE_BOOL
    true: Allow WebRTC event log collection.
    false: Do not allow WebRTC event log collection.

chrome.users.WebRtcIpHandling: WebRTC IP handling.
  webRtcIpHandling: TYPE_ENUM
    DEFAULT: WebRTC will use all available interfaces when searching for the best path.
    DEFAULT_PUBLIC_AND_PRIVATE_INTERFACES: WebRTC will only use the interface connecting to the public Internet, but may connect using private IP addresses.
    DEFAULT_PUBLIC_INTERFACE_ONLY: WebRTC will only use the interface connecting to the public Internet, and will not connect using private IP addresses.
    DISABLE_NON_PROXIED_UDP: WebRTC will use TCP on the public-facing interface, and will only use UDP if supported by a configured proxy.

chrome.users.WebRtcLocalIpsAllowedUrls: WebRTC ICE candidate URLs for local IPs.
  webRtcLocalIpsAllowedUrls: TYPE_LIST
    URLs for which local IPs are exposed in WebRTC ICE candidates. . Patterns in this list will be matched against the security origin of the requesting URL. If a match is found the local IP addresses are shown in WebRTC ICE candidates. Otherwise, local IP addresses are concealed with mDNS hostnames. Please note that this policy weakens the protection of local IPs if needed by administrators. .

chrome.users.WebRtcTextLogCollectionAllowed: WebRTC text logs collection from Google Services.
  webRtcTextLogCollectionAllowed: TYPE_BOOL
    true: Allow WebRTC text log collection from Google Services.
    false: Do not allow WebRTC text log collection from Google Services.

chrome.users.WebRtcUdpPortRange: WebRTC UDP ports.
  webRtcUdpPortsEnabled: TYPE_BOOL
    true: Specify range of UDP ports allowed for WebRTC.
    false: Allow WebRTC to pick any UDP port (1024-65535).
  webRtcUdpPortsMin: TYPE_INT64
    Minimum value for allowed UDP ports. This setting can only be set after setting web_rtc_udp_ports_enabled = true.
  webRtcUdpPortsMax: TYPE_INT64
    Maximum value for allowed UDP ports. This setting can only be set after setting web_rtc_udp_ports_enabled = true.

chrome.users.WebSerialPortAccess: Web Serial API.
  defaultSerialGuardSetting: TYPE_ENUM
    BLOCK_SERIAL: Do not allow any site to request access to serial ports via the Web Serial API.
    ALLOW_ASK_SERIAL: Allow sites to ask the user to grant access to a serial ports via the Web Serial API.
    UNSET: Allow the user to decide.
  serialAskForUrls: TYPE_LIST
    Allow the Web Serial API on these sites. List of URLs that specify websites that will be allowed to ask users to grant them access to the serial ports. Prefix domain with [*.] to include subdomains.
  serialBlockedForUrls: TYPE_LIST
    Block the Web Serial API on these sites. List of URLs patterns that specify which websites can't ask users to grant them access to a serial port. Prefix domain with [*.] to include subdomains.

chrome.users.WebSqlAccess: Force WebSQL to be enabled.
  webSqlAccess: TYPE_BOOL
    true: Force WebSQL to be enabled.
    false: Allow WebSQL to be disabled by a Chrome flag.

chrome.users.WebSqlInThirdPartyContextEnabled: WebSQL in third-party context.
  webSqlInThirdPartyContextEnabled: TYPE_BOOL
    true: Allow WebSQL in third-party contexts.
    false: Do not allow WebSQL in third-party contexts.

chrome.users.WebSqlNonSecureContextEnabled: WebSQL in non-secure contexts.
  webSqlNonSecureContextEnabled: TYPE_BOOL
    true: Enable WebSQL in non-secure contexts.
    false: Disable WebSQL in non-secure contexts unless enabled by Chrome flag.

chrome.users.WebUsbAllowDevicesForUrls: WebUSB API allowed devices.
  webUsbAllowDevicesForUrls
    webApplications
      url: TYPE_STRING
      devices: TYPE_LIST

chrome.users.WebUsbPortAccess: Controls which websites can ask for USB access.
  defaultWebUsbGuardSetting: TYPE_ENUM
    BLOCK_WEB_USB: Do not allow any site to request access.
    ASK_WEB_USB: Allow sites to ask the user for access.
    UNSET: Allow the user to decide if sites can ask.
  webUsbAskForUrls: TYPE_LIST
    Allow these sites to ask for USB access. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.
  webUsbBlockedForUrls: TYPE_LIST
    Block these sites from asking for USB access. For detailed information on valid url patterns, please see URL patterns at https://cloud.google.com/docs/chrome-enterprise/policies/url-patterns. Note: using only the "*" wildcard is not valid.

chrome.users.WebXrImmersiveArEnabled: WebXR immersive-ar sessions.
  webXrImmersiveArEnabled: TYPE_BOOL
    true: Allow creating WebXR immersive-ar sessions.
    false: Prevent creating WebXR immersive-ar sessions.

chrome.users.WifiSyncAndroidAllowed: Wi-Fi network configurations sync.
  wifiSyncAndroidAllowed: TYPE_BOOL
    true: Allow Wi-Fi network configurations to be synced across Google ChromeOS devices and a connected Android phone.
    false: Do not allow Wi-Fi network configurations to be synced across Google ChromeOS devices and a connected Android phone.

chrome.users.WindowOcclusionEnabled: Occluded window rendering.
  windowOcclusionEnabled: TYPE_BOOL
    true: Allow detection of window occlusion.
    false: Disable detection of window occlusion.

chrome.users.WpadQuickCheckEnabled: WPAD optimization.
  wpadQuickCheckEnabled: TYPE_BOOL
    true: Enable Web Proxy Auto-Discovery (WPAD) optimization.
    false: Disable Web Proxy Auto-Discovery (WPAD) optimization.

chrome.users.ZstdContentEncodingEnabled: Zstd compression.
  zstdContentEncodingEnabled: TYPE_BOOL
    true: Allow zstd-compressed web content.
    false: Do not allow zstd-compressed web content.


```
