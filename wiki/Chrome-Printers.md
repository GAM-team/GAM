# Chrome Printers
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Quoting rules](#quoting-rules)
- [Manage printers](#manage-printers)
- [Display printers](#display-printers)
- [Display printer models](#display-printer-models)
- [Bulk printer updates](#bulk-printer-updates)

## API documentation
* [Chrome Printer Management API](https://developers.google.com/admin-sdk/chrome-printer/reference/rest)

## Notes
To use these features you must authorize the appropriate scope: `Directory API - Printers (supports readonly)`.

As of 2021-10-05, `gam update printer` does not work due to some API problem. To update a printer,
you'll have to delete it and create it.

```
gam oauth create
```

## Definitions
```
<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>
<OrgUnitList> ::= "<OrgUnitItem>(,<OrgUnitItem>)*"

<PrinterID> ::= <String>
<PrinterIDList> ::= "<PrinterID>(,<PrinterID>)*"

<PrinterAttribute> ::=
        (description <String>)|
        (displayname <String>)|
        (json [charset <Charset>] <JSONData>)|(json file <FileName> [charset <Charset>])|
        (makeandmodel <String>)|
        (ou|org|orgunit <OrgUnitItem>)|
        (uri <String>)|
        (driverless [<Boolean>])

<PrinterFieldName> ::=
        auxiliarymessages|
        createtime|
        description|
        displayname|
        id|
        makeandmodel|
        name|
        ou|org|orgunit|orgunitid|
        uri|
        usedriverlessconfig|
<PrinterFieldNameList> ::= "<PrinterFieldName>(,<PrinterFieldName>)*"
```
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

<FileSelector> ::=
        file ((<FileName> [charset <Charset>])|
              (gdoc <UserGoogleDoc>)|
              (gcsdoc <StorageBucketObjectName>))
             [delimiter <Character>]

<CSVFileSelector> ::=
        csvfile ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
                 (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
                 (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
                 (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
                 (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
                [warnifnodata] [columndelimiter <Character>] [quotechar <Character>]
                [endcsv|(fields <FieldNameList>)]
                (matchfield|skipfield <FieldName> <RESearchPattern>)*
                [delimiter <Character>]

```
## Quoting rules
Items in a list can be separated by commas or spaces; if an item itself contains a comma, a space or a single quote, special quoting must be used.
Typically, you will enclose the entire list in double quotes and quote each item in the list as detailed below.

- Items, separated by commas, without spaces, commas or single quotes in the items themselves
   * ```"item,item,item"```
- Items, separated by spaces, without spaces, commas or single quotes in the items themselves
   * ```"item item item"```
- Items, separated by commas, with spaces, commas or single quotes in the items themselves
   * ```"'it em','it,em',\"it'em\""```
- Items, separated by spaces, with spaces, commas or single quotes in the items themselves
   * ```"'it em' 'it,em' \"it'em\""```

## Manage printers
When creating a printer you must specify: `displayname`, `ou`, `uri` and `makeandmodel` or `driverless`.
```
gam create printer <PrinterAttribute>+ [nodetails]
gam update printer <PrinterID> <PrinterAttribute>+ [nodetails]
gam delete printer
        <PrinterIDList>|
        <FileSelector>|
	<CSVFileSelector>
```
By default, when a printer is created/updated, GAM outputs details of the printer; the `nodetails` option suppresses this output.

## Display printers
Display information about a single printer.

```
gam info printer <PrinterID>
        [fields <PrinterFieldNameList>] [formatjson]
```
Display information about multiple printers.
```
gam show printers
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [filter <String>] [showinherited [<Boolean>]]
        [fields <PrinterFieldNameList>] [formatjson]
gam print printers [todrive <ToDriveAttribute>*]
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [filter <String>] [showinherited [<Boolean>]]
        [fields <PrinterFieldNameList>] [[formatjson [quotechar <Character>]]
```
Use these options to select printers; if none are chosen, all printers in the account are selected.

If only `filter <String>` is specified, the query applies to all printers. If one of the `ou` options
is also specified, the filter applies to printers within the OUs. The `filter <String>` is applied
to the printer `displayName` and `description` fields.

- `filter <String>` - Filter on printer `description` and `displayName'.
- `ou <OrgUnitItem>` - Select printers directly in the OU `<OrgUnitItem>`
- `ou_and_children <OrgUnitItem>` - Select printers in the OU `<OrgUnitItem>` and its sub OUs
- `ous <OrgUnitList>` - Select printers directly in the OUs `<OrgUnitList>`
- `ous_and_children <OrgUnitList>` - Select printers in the OUs `<OrgUnitList>` and their sub OUs

By default, only printers defined in the specified OUs are displayed. Use the `showinherited` option
to display inherited printers in the OUs; three additional fields are displayed.
- `inherited` - False if the printer is defined in the OU, True if the printer is inherited by the OU
- `parentOrgUnitId` - Blank if the printer is defined in the OU, the ID of the defining OU if the printer is inherited by the OU
- `parentOrgUnitPath` - Blank if the printer is defined in the OU, the path of the defining OU if the printer is inherited by the OU

## Display printer models
```
gam show printermodels
        [filter <String>]
        [formatjson]
gam print printermodels [todrive <ToDriveAttribute>*]
        [filter <String>]
        [[formatjson [quotechar <Character>]]
```
If `filter <String>` isn't specified, all printer models are displayed.
You can filter by manufacturer: `filter "manufacturer:XYX"`

## Bulk printer updates
Suppose you have replaced one model of printer with another and have to update the make and model.

As of 2021-10-05, you'll have to delete and create the updated printer as `gam update printer` does not work due to some API problem.

Get the list of printers.
```
gam redirect csv ./StudentPrinters.csv print printers formatjson quotechar "'" ou /Students
```
Edit StudentPrinters.csv and add a new column labelled `action`; it does not matter where you place the column.
In each row's JSON data there will be an entry like this: `"makeAndModel": "vendor1 xy abcd"`; replace `vendor1 xy abcd`
with `vendor2 ab wxyz` for the rows of interest and put an `x` in the `action` column.

Delete the marked printers.
```
gam config csv_input_row_filter "action:regex:x" redirect stdout ./DeletePrinters.txt multiprocess redirect stderr stdout csv ./StudentPrinters.csv quotechar "'" gam delete printer "~id"
```

Recreate the marked printers with the updated `makeAndModel`.
```
gam config csv_input_row_filter "action:regex:x" redirect stdout ./CreatetePrinters.txt multiprocess redirect stderr stdout csv ./StudentPrinters.csv quotechar "'" gam create printer json "~JSON"
```
