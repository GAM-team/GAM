# Mobile Devices
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [Manage mobile devices](#manage-mobile-devices)
- [Display mobile devices](#display-mobile-devices)
- [Print mobile devices](#print-mobile-devices)
- [Display mobile device counts](#display-mobile-device-counts)

## API documentation
* [Directory API - Mobile Devices](https://developers.google.com/admin-sdk/directory/reference/rest/v1/mobiledevices)

## Query documentation
* [Filters](https://support.google.com/a/answer/7549103)
* [Device Search Fields](https://developers.google.com/admin-sdk/directory/v1/search-operators)

## Definitions
```
<QueryMobile> ::= <String>
        See: https://support.google.com/a/answer/7549103
<QueryMobileList> ::= "<QueryMobile>(,<QueryMobile>)*"
<ResourceID> ::= <String>
<ResourceIDList> ::= "<ResourceID>(,<ResourceID>)*"
<MobileEntity> ::=
        <ResourceIDList> |
        (query:<QueryMobile>)|(query <QueryMobile>)

<MobileAction> ::=
        admin_remote_wipe|wipe|
        admin_account_wipe|accountwipe|wipeaccount|
        approve|
        block|
        cancel_remote_wipe_then_activate|
        cancel_remote_wipe_then_block)

<MobileFieldName> ::=
        adbstatus|
        applications|
        basebandversion|
        bootloaderversion|
        brand|
        buildnumber|
        defaultlanguage|
        developeroptionsstatus|
        devicecompromisedstatus|
        deviceid|
        devicepasswordstatus|
        email|
        encryptionstatus|
        firstsync|
        hardware|
        hardwareid|
        imei|
        kernelversion|
        lastsync|
        managedaccountisonownerprofile|
        manufacturer|
        meid|
        model|
        name|
        networkoperator|
        os|
        otheraccountsinfo|
        privilege|
        releaseversion|
        resourceid|
        securitypatchlevel|
        serialnumber|
        status|
        supportsworkprofile|
        type|
        unknownsourcesstatus|
        useragent|
        wifimacaddress
<MobileFieldNameList> ::= "<MobileFieldName>(,<MobileFieldName>)*"

<MobileOrderByFieldName> ::=
        deviceid|email|lastsync|model|name|os|status|type
```
## Manage mobile devices
```
gam update mobile <MobileEntity> action <MobileAction>
        [doit] [matchusers <UserTypeEntity>]
gam delete mobile <MobileEntity>
        [doit] [matchusers <UserTypeEntity>]
```
If `<MobileEntity>` uses a query, the `doit` option must be used to enable execution.

The `matchusers <UserTypeEntity>` option disables execution on devices that don't have
have an email address contained in that list.

## Display mobile devices
```
gam info mobile <MobileEntity>
        [basic|full|allfields] <MobileFieldName>* [fields <MobileFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Print mobile devices
```
gam print mobile [todrive <ToDriveAttribute>*]
        [(query <QueryMobile>)|(queries <QueryMobileList>) (querytime<String> <Time>)*]
        [orderby <MobileOrderByFieldName> [ascending|descending]]
        [basic|full|allfields] <MobileFieldName>* [fields <MobileFieldNameList>]
        [delimiter <Character>] [appslimit <Number>] [oneappperrow] [listlimit <Number>]
        [formatjson [quotechar <Character>]]
```
The `email`, `name` and `otheraccountsinfo` fields can have multiple values; the `listlimit` argument controls how these fields are displayed.
* `listlimit -1` - print no values for the field
* `listlimit 0` - print all values for the field
* `listlimit 1` - print one value for the field, default
* `listlinit N` - print the first N values for the field

The `applications` field can have multiple values; the `appslimit` argument controls how this field is displayed.
* `appslimit -1` - print no values for the field, default
* `appslimit 0` - print all values for the field
* `appslinit N` - print the first N values for the field

For a device with many applications, displaying all of the applications on one row can make an excessively long field;
use the `oneappperrow` option to have each application be  displayed on a separate row with all of the other mobile device fields.

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryMobile>` option.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers. This is most useful in scripts
where you can specify a relative date without having to change the script.

For example, query for mobile devices synced more that 30 days ago.
```
gam print mobile fields querytime30d -30d query "sync:..#querytime30d#"
```

To AND query terms, put all of your terms in one query:
```
gam print mobile query "manufacturer:Meizu os:Android 7.0.0"
```
To OR query terms, put the terms im multiple queries:
```
gam print mobile queries "'model:iPhone 6','model:samsung'"
```

`delimiter` - The items in the `applications`, `email`, `name` and `otheraccountsinfo` fields are separated by `delimiter`, it defaults to the value of `csv_output_field_delimiter` in `gam.cfg`.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display mobile device counts
Display the number of mobile devices.
```
gam print mobile
        [(query <QueryMobile>)|(queries <QueryMobileList>) (querytime<String> <Time>)*]
        showitemcountonly
```
Example
```
$ gam print mobile showitemcountonly
Getting all Mobile Devices, may take some time on a large Google Workspace Account...
Got 100 Mobile Devices...
Got 115 Mobile Devices
115
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print mobile showitemcountonly)
Windows PowerShell
count = & gam print mobile showitemcountonly
```
