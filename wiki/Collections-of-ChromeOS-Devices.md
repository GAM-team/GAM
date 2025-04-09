# Collections of ChromeOS Devices
- [Python Regular Expressions](Python-Regular-Expressions) Search function
- [Definitions](#definitions)
- [Organization Unit Quoting](#organization-unit-quoting)
- [Query Quoting](#query-quoting)
- [Query Notes](#query-notes)
- [CrOS Type Entity](#cros-type-entity)
  - [All ChromeOS devices](#all-chromeos-devices)
  - [A list of ChromeOS deviceIds](#a-list-of-chromeos-deviceids)
  - [A list of ChromeOS device serial numbers](#a-list-of-chromeos-device-serial-numbers)
  - [ChromeOS devices directly in the Organization Unit `<OrgUnitItem>`](#chromeos-devices-directly-in-the-organization-unit-orgunititem)
  - [ChromeOS devices in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units](#chromeos-devices-in-the-organization-unit-orgunititem-and-all-of-its-sub-organization-units)
  - [ChromeOS devices directly in the Organization Units `<OrgUnitList>`](#chromeos-devices-directly-in-the-organization-units-orgunitlist)
  - [ChromeOS devices in the Organization Units `<OrgUnitList>` and all of their sub Organization Units](#chromeos-devices-in-the-organization-units-orgunitlist-and-all-of-their-sub-organization-units)
  - [ChromeOS devices directly in the Organization Unit `<OrgUnitItem>` that also match a query](#chromeos-devices-directly-in-the-organization-unit-orgunititem-that-also-match-a-query)
  - [ChromeOS devices in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units that also match a query](#chromeos-devices-in-the-organization-unit-orgunititem-and-all-of-its-sub-organization-units-that-also-match-a-query)
  - [ChromeOS devices directly in the Organization Units `<OrgUnitList>` that also match a query](#chromeos-devices-directly-in-the-organization-units-orgunitlist-that-also-match-a-query)
  - [ChromeOS devices in the Organization Units `<OrgUnitList>` and all of their sub Organization Units that also match a query](#chromeos-devices-in-the-organization-units-orgunitlist-and-all-of-their-sub-organization-units-that-also-match-a-query)
  - [ChromeOS devices directly in the Organization Unit `<OrgUnitItem>` that also match any query in a list of queries](#chromeos-devices-directly-in-the-organization-unit-orgunititem-that-also-match-any-query-in-a-list-of-queries)
  - [ChromeOS devices in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units that also match any query in a list of queries](#chromeos-devices-in-the-organization-unit-orgunititem-and-all-of-its-sub-organization-units-that-also-match-any-query-in-a-list-of-queries)
  - [ChromeOS devices directly in the Organization Units `<OrgUnitList>` that also match any query in a list of queries](#chromeos-devices-directly-in-the-organization-units-orgunitlist-that-also-match-any-query-in-a-list-of-queries)
  - [ChromeOS devices in the Organization Units `<OrgUnitList>` and all of their sub Organization Units that also match any query in a list of queries](#chromeos-devices-in-the-organization-units-orgunitlist-and-all-of-their-sub-organization-units-that-also-match-any-query-in-a-list-of-queries)
  - [ChromeOS devices that match a query](#chromeos-devices-that-match-a-query)
  - [ChromeOS devices that match any query in a list of queries](#chromeos-devices-that-match-any-query-in-a-list-of-queries)
  - [ChromeOS deviceIds in a flat file/Google Doc/Google Cloud Storage Object](#chromeos-deviceids-in-a-flat-filegoogle-docgoogle-cloud-storage-object)
  - [ChromeOS serial numbers in a flat file/Google Doc/Google Cloud Storage Object](#chromeos-serial-numbers-in-a-flat-filegoogle-docgoogle-cloud-storage-object)
  - [Selected ChromeOS deviceIds in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object](#selected-chromeos-deviceids-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [Selected ChromeOS serial numbers in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object](#selected-chromeos-serial-numbers-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [ChromeOS devices from OUs in a flat file/Google Doc/Google Cloud Storage Object](#chromeos-devices-from-ous-in-a-flat-filegoogle-docgoogle-cloud-storage-object)
  - [ChromeOS deviceIds from OUs in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object](#chromeos-deviceids-from-ous-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [ChromeOS devices directly in or from OUs in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object](#chromeos-devices-directly-in-or-from-ous-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [ChromeOS deviceIds from data fields identified in a `csvkmd` argument](#chromeos-deviceids-from-data-fields-identified-in-a-csvkmd-argument)
- [Examples using CSV files](#examples-using-csv-files)
- [Examples using multiple queries or Org Units](#examples-using-multiple-queries-or-org-units)

## Definitions
* [Basic Items](Basic-Items)

* [List Items](List-Items)

* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
```
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>

<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)

<SheetEntity> ::= <String>|id:<Number>
<UserGoogleSheet> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>) <SheetEntity>

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |
```
```
<CrOSTypeEntity> ::=
        (all cros)|
        (cros <CrOSIDList>)|
        (cros_sn <SerialNumberList>)|
        (cros_ou <OrgUnitItem>)|
        (cros_ou_and_children <OrgUnitItem>)|
        (cros_ous <OrgUnitList>)|
        (cros_ous_and_children <OrgUnitList>)|
        (cros_ou_query <OrgUnitItem> <QueryCrOS>)|
        (cros_ou_and_children_query <OrgUnitItem> <QueryCrOS>)|
        (cros_ous_query <OrgUnitList> <QueryCrOS>)|
        (cros_ous_and_children_query <OrgUnitList> <QueryCrOS>)|
        (cros_ou_queries <OrgUnitItem> <QueryCrOSList>)|
        (cros_ou_and_children_queries <OrgUnitItem> <QueryCrOSList>)|
        (cros_ous_queries <OrgUnitList> <QueryCrOSList>)|
        (cros_ous_and_children_queries <OrgUnitList> <QueryCrOSList>)|
        (crosquery <QueryCrOS>)|
        (crosqueries <QueryCrOSList>)|
        (crosfile
            ((<FileName> [charset <Charset>])|
             (gdoc <UserGoogleDoc>)|
             (gcsdoc <StorageBucketObjectName>))
            [delimiter <Character>])|
        (crosfile_sn
            ((<FileName> [charset <Charset>])|
             (gdoc <UserGoogleDoc>)|
             (gcsdoc <StorageBucketObjectName>))
            [delimiter <Character>])|
        (croscsvfile
            ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
             (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
             (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
             (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
             (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
            [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
            [endcsv|(fields <FieldNameList>)]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [delimiter <Character>])|
        (croscsvfile_sn
            ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
             (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
             (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
             (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
             (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
            [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
            [endcsv|(fields <FieldNameList>)]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [delimiter <Character>])|
        (datafile
            cros|cros_sn|cros_ous|cros_ous_and_children
            ((<FileName> [charset <Charset>])|
              (gdoc <UserGoogleDoc>)|
              (gcsdoc <StorageBucketObjectName>))
             [delimiter <Character>])|
        (csvdatafile
            cros|cros_sn|cros_ous|cros_ous_and_children
            ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
              (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
              (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
              (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
              (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
            [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
            [endcsv|(fields <FieldNameList>)]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [delimiter <Character>])|
        (csvkmd
            cros|cros_sn|cros_ous|cros_ous_and_children
            ((<FileName>|
              (gsheet <UserGoogleSheet>)|
              (gdoc <UserGoogleDoc>)|
              (gcscsv <StorageBucketObjectName>)|
              (gcsdoc <StorageBucketObjectName>))
             [charset <Charset>] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>] [fields <FieldNameList>])
            keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
            subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [datafield <FieldName>(:<FieldName>)* [delimiter <Character>]])
        (croscsvdata <FieldName>(:<FieldName>*))
```
## Organization Unit Quoting
* `<OrgUnitItem>` should be enclosed in `"` if it contains a space, comma or single quote.
* `<OrgUnitList>` may require special quoting based on whether the OUs contain spaces, commas or single quotes.

For quoting rules, see: [List Quoting Rules](Command-Line-Parsing)

## Query Quoting
`<QueryCrOSList>` may require special quoting based on whether the queries contain spaces, commas or single quotes.

For quoting rules, see: [List Quoting Rules](Command-Line-Parsing)

## Query Notes

See https://support.google.com/chrome/a/answer/1698333

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

## CrOS Type Entity

Use these options to select Chrome OS devices for GAM commands.

## All ChromeOS devices
* `all cros`

## A list of ChromeOS deviceIds
* `cros <CrOSList>`

## A list of ChromeOS device serial numbers
* `cros_sn <SerialNumberList>`

## ChromeOS devices directly in the Organization Unit `<OrgUnitItem>`
* `cros_ou <OrgUnitItem>`

## ChromeOS devices in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units
* `cros_ou_and_children <OrgUnitItem>`

## ChromeOS devices directly in the Organization Units `<OrgUnitList>`
* `cros_ous <OrgUnitList>`

## ChromeOS devices in the Organization Units `<OrgUnitList>` and all of their sub Organization Units
* `cros_ous_and_children <OrgUnitList>`

## ChromeOS devices directly in the Organization Unit `<OrgUnitItem>` that also match a query
* `cros_ou_query <OrgUnitItem> <QueryCrOS>`

## ChromeOS devices in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units that also match a query
* `cros_ou_and_children_query <OrgUnitItem> <QueryCrOS>`

## ChromeOS devices directly in the Organization Units `<OrgUnitList>` that also match a query
* `cros_ous_query <OrgUnitList> <QueryCrOS>`

## ChromeOS devices in the Organization Units `<OrgUnitList>` and all of their sub Organization Units that also match a query
* `cros_ous_and_children_query <OrgUnitList> <QueryCrOS>`

## ChromeOS devices directly in the Organization Unit `<OrgUnitItem>` that also match any query in a list of queries
* `cros_ou_queries <OrgUnitItem> <QueryCrOSList>`

## ChromeOS devices in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units that also match any query in a list of queries
* `cros_ou_and_children_queries <OrgUnitItem> <QueryCrOSList>`

## ChromeOS devices directly in the Organization Units `<OrgUnitList>` that also match any query in a list of queries
* `cros_ous_queries <OrgUnitList> <QueryCrOSList>`


## ChromeOS devices in the Organization Units `<OrgUnitList>` and all of their sub Organization Units that also match any query in a list of queries
* `cros_ous_and_children_queries <OrgUnitList> <QueryCrOSList>`

## ChromeOS devices that match a query
* `crosquery <QueryCrOS>`

## ChromeOS devices that match any query in a list of queries
* `crosqueries <QueryCrOSList>`

## ChromeOS deviceIds in a flat file/Google Doc/Google Cloud Storage Object
```
crosfile
   ((<FileName> [charset <Charset>])|
    (gdoc <UserGoogleDoc>)|
    (gcsdoc <StorageBucketObjectName>))
   [delimiter <Character>]
```
* `<FileName>` - A flat file containing a single ChromeOS deviceId per row
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gdoc <UserGoogleDoc>` - A Google Doc containing a single ChromeOS deviceId per row
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing a single ChromeOS deviceId per row
* `delimiter <Character>` - There are multiple deviceIds per row separated by `<Character>`; if not specified, there is single deviceId per row

## ChromeOS serial numbers in a flat file/Google Doc/Google Cloud Storage Object
```
crosfile_sn
   ((<FileName> [charset <Charset>])|
    (gdoc <UserGoogleDoc>)|
    (gcsdoc <StorageBucketObjectName>))
   [delimiter <Character>]
```
* `<FileName>` - A flat file containing a single ChromeOS serial number per row
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gdoc <UserGoogleDoc>` - A Google Doc containing a single ChromeOS serial number per row
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing a single ChromeOS serial number per row
* `delimiter <Character>` - There are multiple serial numbers per row separated by `<Character>`; if not specified, there is single serial number per row

## Selected ChromeOS deviceIds in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
croscsvfile
   ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
    (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
    (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
    (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
    (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
   [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
   [endcsv|(fields <FieldNameList>)]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
   [delimiter <Character>]
```
* `<FileName>(:<FieldName>)+` - A CSV file and the one or more columns that contain ChromeOS deviceIds
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet(:<FieldName>)+ <UserGoogleSheet>` - A Google Sheet and the one or more columns that contain ChromeOS deviceIds
* `gdoc(:<FieldName>)+ <UserGoogleDoc>` - A Google Doc and the one or more columns that contain ChromeOS deviceIds
* `gcscsv(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain ChromeOS deviceIds
* `gcsdoc(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain ChromeOS deviceIds
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `delimiter <Character>` - There are multiple deviceIds per column separated by `<Character>`; if not specified, there is single deviceId per column

## Selected ChromeOS serial numbers in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
croscsvfile_sn
   ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
    (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
    (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
    (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
    (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
   [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
   [endcsv|(fields <FieldNameList>)]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
   [delimiter <Character>]
```
* `<FileName>(:<FieldName>)+` - A CSV file and the one or more columns that contain ChromeOS serial numbers
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet(:<FieldName>)+ <UserGoogleSheet>` - A Google Sheet and the one or more columns that contain ChromeOS serial numbers
* `gdoc(:<FieldName>)+ <UserGoogleDoc>` - A Google Doc and the one or more columns that contain ChromeOS serial numbers
* `gcscsv(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain ChromeOS serial numbers
* `gcsdoc(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain ChromeOS serial numbers
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `delimiter <Character>` - There are multiple serial numbers per column separated by `<Character>`; if not specified, there is single deviceId per column

## ChromeOS devices from OUs in a flat file/Google Doc/Google Cloud Storage Object
```
datafile
   cros|cros_sn|cros_ous|cros_ous_and_children
   ((<FileName> [charset <Charset>])|
     (gdoc <UserGoogleDoc>)|
     (gcsdoc <StorageBucketObjectName>))
    [delimiter <Character>]
```
* `cros|cros_sn|cros_ous|cros_ous_and_children` - The type of item in the file
* `<FileName>` - A flat file containing a single item per row
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gdoc <UserGoogleDoc>` - A Google Doc containing a single item per row
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing a item per row
* `delimiter <Character>` - There are multiple items per row separated by `<Character>`; if not specified, there is single item per row

## ChromeOS deviceIds from OUs in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
csvdatafile
   cros|cros_sn|cros_sn|cros_ous|cros_ous_and_children
   ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
     (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
     (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
     (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
     (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
   [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
   [endcsv|(fields <FieldNameList>)]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
   [delimiter <Character>]
```
* `cros|cros_ous|cros_ous_and_children` - The type of item in the file
* `<FileName>(:<FieldName>)+` - A CSV file and the one or more columns that contain ChromeOS deviceIds
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet(:<FieldName>)+ <UserGoogleSheet>` - A Google Sheet and the one or more columns that contain ChromeOS deviceIds
* `gdoc(:<FieldName>)+ <UserGoogleDoc>` - A Google Doc and the one or more columns that contain ChromeOS deviceIds
* `gcscsv(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain ChromeOS deviceIds
* `gcsdoc(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain ChromeOS deviceIds
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `delimiter <Character>` - There are multiple deviceIds per column separated by `<Character>`; if not specified, there is single deviceId per column

## ChromeOS devices directly in or from OUs in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
csvkmd
   cros|cros_sn|cros_ous|cros_ous_and_children
   ((<FileName>|
     (gsheet <UserGoogleSheet>)|
     (gdoc <UserGoogleDoc>)|
     (gcscsv <StorageBucketObjectName>)|
     (gcsdoc <StorageBucketObjectName>))
    [charset <Charset>] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>] [fields <FieldNameList>])
   keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
   subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
   [datafield <FieldName>(:<FieldName>)* [delimiter <Character>]]
```
* `cros|cros_sn|cros_ous|cros_ous_and_children` - The type of item in the file
* `<FileName>` - A CSV file containing rows with columns of the type of item specified
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet <UserGoogleSheet>` - A Google Sheet containing rows with columns of the type of item specified
* `gdoc <UserGoogleDoc>` - A Google Doc containing rows with columns of the type of item specified
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>])+`
    * `keyfield <FieldName>` - The column containing key values
    * `[keypattern <RESearchPattern>] [keyvalue <RESubstitution>]` - Allows transforming the value(s) in the `keyfield` column. If only `keyvalue <RESubstitution>` is specified, all instances of `<FieldName>` in `keyvalue <RESubstitution>` will be replaced by the item value. If `keypattern <RESearchPattern>` is specified, the item value is matched against `<RESearchPattern>` and the matched segments are substituted into `keyvalue <RESubstitution>`
    * `delimiter <Character>` - There are multiple values per keyfield column separated by `<Character>`; if not specified, there is single value per keyfield column
* `(subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>])*`
    * `subkeyfield <FieldName>` - The column containing subkey values
    * `[keypattern <RESearchPattern>] [keyvalue <RESubstitution>]` - Allows transforming the value(s) in the `subkeyfield` column. If only `keyvalue <RESubstitution>` is specified, all instances of `<FieldName>` in `keyvalue <RESubstitution>` will be replaced by the item value. If `keypattern <RESearchPattern>` is specified, the item value is matched against `<RESearchPattern>` and the matched segments are substituted into `keyvalue <RESubstitution>`
    * `delimiter <Character>` - There are multiple values per subkeyfield column separated by `<Character>`; if not specified, there is single value per subkeyfield column
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `(datafield <FieldName>(:<FieldName)* [delimiter <Character>])*`
    * `datafield <FieldName>(:<FieldName)*` - The column(s) containing data values
    * `delimiter <Character>` - There are multiple values per datafield column separated by `<Character>`; if not specified, there is single value per datafield column

## ChromeOS deviceIds from data fields identified in a `csvkmd` argument
* `croscsvdata <FieldName>(:<FieldName>*)` - Data fields identified in a `csvkmd` argument

## Examples using CSV files

You want to print information about ChromeOS devices at your school from Org Units based on graduation year.

Example 1
CSV File OrgUnit.csv, exactly the data you want, `keypattern` and `keyvalue` are not required.
```
OrgUnit
/Students/2020
/Students/2021
...
```
For each row, the value from the OrgUnit column is used as the Org Unit  name.
```
gam csvkmd cros_ous OrgUnit.csv keyfield OrgUnit print cros
```

Example 2
CSV File GradYear.csv, you have to convert GradYear to Org Unit name `/Students/GradYear`, `keyvalue` is required.
```
GradYear
2020
2021
...
```
For each row, the value from the GradYear column replaces the keyField name in the `keyvalue` argument and that value is used as the Org Unit name.
```
gam csvkmd cros_ous GradYear.csv keyfield GradYear keyvalue "/Students/GradYear" print cros
```

Example 3
CSV File GradYear.csv, you have to convert GradYear to Org Unit name `/Students/LastTwoDigitsOfGradYear`, `keypattern` and `keyvalue` are required.
```
GradYear
2020
2021
...
```
For each row, the value from the GradYear column is matched against the `keypattern` and the matched segments are substituted into the `keyvalue` argument and that value is used as the Org Unit name.
```
gam csvkmd cros_ous GradYear.csv keyfield GradYear keypattern '20(..)' keyvalue '/Students/\1' print cros
```

## Examples using multiple queries or Org Units

Example 1
Print information about all ChromeOS devices with a serial number that starts with HY3 or 5CD.
```
gam crosqueries "id:HY3,id:5CD" print cros allfields nolists
```

Example 2
Print information about all ChromeOS devices in two Org Units that contain spaces in their names.
```
gam crosqueries "\"orgUnitPath='/Students/Middle School/2021'\",\"orgUnitPath='/Students/Middle School/2020'\"" print cros allfields nolists
```

This is equivaluent to:
```
gam cros_ous "'/Students/Middle School/2021','/Students/Middle School/2020'" print cros allfields nolists
```
