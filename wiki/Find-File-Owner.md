# Find File Owner
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Display File Ownership](#display-file-ownership)
- [Display File Ownership for Old files](#display-file-ownership-for-old-files)

## API documentation
* [Reports API - Activities](https://developers.google.com/admin-sdk/reports/reference/rest/v1/activities)

## Definitions
```
<DriveFileID> ::= <String>
<DriveFileName> ::= <String>
```

## Display File Ownership
These commands use the Reports API audit activity and may not find the owner if the file has not been accessed in 180 days.
If you specify a `<DriveFileID>`, there will be at most one line of output. If you specify a `<DriveFileName>`, there will be
one line of output for each distinct file with that name.

The Reports API calls are:
* `ownership <DriveFileID>` - `gam report drive filter "doc_id==<DriveFileID>"`
* `ownership drivefilename <DriveFileName>` - `gam report drive filter "doc_title==<DriveFileName>"`

```
gam show ownership <DriveFileID>|(drivefilename <DriveFileName>)
        [formatjson]
```
By default, Gam displays the information as a list of keys and values.
* `formatjson` - Display the output in JSON notation

```
gam print ownership <DriveFileID>|(drivefilename <DriveFileName>) [todrive <ToDriveAttribute>*]
        (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
* `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format.
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display File Ownership for Old files
If the above commands fail, you can try to loop through all accounts, however this might take a long time if you are on a large Google Workspace Account.
If any lines are displayed, the file owner is in the `owners.0.emailAddress` column.
```
gam config auto_batch_min 1 multiprocessexit rc=0 redirect csv - multiprocess redirect stderr null multiprocess all users print filelist select id <DriveFileID> fields id,name,owners.emailaddress norecursion showownedby any
gam config auto_batch_min 1 multiprocessexit rc=0 redirect csv - multiprocess redirect stderr null multiprocess all users print filelist select name <DriveFileName> fields id,name,owners.emailaddress norecursion showownedby any
```
