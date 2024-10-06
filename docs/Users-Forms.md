!# Users - Forms
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Create a Form](#create-a-form)
- [Update a Form](#update-a-form)
- [Display Forms](#display-forms)
- [Display Form Responses](#display-form-responses)
- [Combine Form Information](#combine-form-information)

## API documentation
* https://developers.google.com/forms/api/reference/rest

## Notes
To use these commands you must add the 'Forms API' to your project and update your service account authorization.

Forms are identified by their `<DriveFileID>`.
```
gam update project
gam user user@domain.com update serviceaccount
```

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DriveFileParentAttribute> ::=
        (parentid <DriveFolderID>)|
        (parentname <DriveFolderName>)|
        (anyownerparentname <DriveFolderName>)|
        (teamdriveparentid <DriveFolderID>)|
        (teamdriveparent <SharedDriveName>)|
        (teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>)|
        (teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>))|
        (teamdriveparentid <DriveFolderID>)|(teamdriveparent <SharedDriveName>)|
        (teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>)|
        (teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>)

<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
```

## Create a Form
```
gam <UserTypeEntity> create form
        title <String> [description <String>] [isquiz [Boolean>]
        [drivefilename <DriveFileName>] [<DriveFileParentAttribute>]
        [(csv [todrive <ToDriveAttribute>*]) | returnidonly]
```

If `drivefilename <DriveFileName>` is not specified, the file will be named `<String>` from `title`.

By default, the user, form title and file name/ID values are displayed on stdout.
* `csv [todrive <ToDriveAttribute>*]` - Write user, file ID, file name, form title and responderUri values to a CSV file.
* `returnidonly` - Display just the file ID of the created file as output

To retrieve the file ID with `returnidonly`:
```
Linux/MacOS
fileId=$(gam user user@domain.com create form title "xyz" ... returnidonly)
Windows PowerShell
$fileId = & gam user user@domain.com create form title "xyz" ... returnidonly
```
The file ID will only be valid when the return code of the command is 0; program accordingly.

## Update a Form
Select forms with `<DriveFileEntity>`:
* `<DriveFileID>` - Update a specific form
* `my_forms` - Update all forms owned by the user
```
gam <UserTypeEntity> update form <DriveFileEntity>
        [title <String>] [description <String>] [isquiz [Boolean>]
```

## Display Forms
Select forms with `<DriveFileEntity>`:
* `<DriveFileID>` - Display responses for a specific form
* `my_forms` - Display responses for all forms owned by the user
```
gam <UserTypeEntity> show forms <DriveFileEntity>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the form in JSON format

```
gam <UserTypeEntity> print forms <DriveFileEntity> [todrive <ToDriveAttribute>*]
        (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
* `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Form Responses
Select forms with `<DriveFileEntity>`:
* `<DriveFileID>` - Display responses for a specific form
* `my_forms` - Display responses for all forms owned by the user
```
gam <UserTypeEntity> show formresponses <DriveFileEntity>
        [filtertime.* <Time>] [filter <String>]
        [countsonly|formatjson]
```
By default, GAM displays form response details, use the `countsonly` option to get the number of responses but no response details.

By default, GAM displays all form responses, you can filter by response time:
* `timestamp > <Time>` - Display all form responses submitted after `<Time>`
* `timestamp >= <Time>` - Display all form responses submitted at or after `<Time>`

For example, to get the form responses submitted since the beginning of the year:
* `filter timestamp >= 2022-01-01T00:00:00Z`

Use the `filtertime.* <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

For example, to get the responses subnitted in the last four hours:
* `filtertime4h -4h filter "timestamp >= #filtertime4h#`

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the form response in JSON format

```
gam <UserTypeEntity> print formresponses <DriveFileEntity> [todrive <ToDriveAttribute>*]
        (addcsvdata <FieldName> <String>)*
        [filtertime.* <Time>] [filter <String>]
        [countsonly|(formatjson [quotechar <Character>])]
```
By default, GAM displays form response details, use the `countsonly` option to get the number of responses but no response details.

* `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

By default, GAM displays all form responses, you can filter by response time:
* `timestamp > <Time>` - Display all form responses submitted after `<Time>`
* `timestamp >= <Time>` - Display all form responses submitted at or after `<Time>`

For example, to get the form responses submitted since the beginning of the year:
* `filter timestamp >= 2022-01-01T00:00:00Z`

Use the `filtertime.* <Time>` option to allow times, usually relative, to be substituted into the `filter <String>` option.
The characters following `filtertime` can be any combination of lowercase letters and numbers.

For example, to get the responses subnitted in the last four hours:
* `filtertime4h -4h filter "timestamp >= #filtertime4h#`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Combine Form Information
Combine form information from several GAM commands.

```
# Get form Id and createdTime
gam redirect csv ./forms.csv  user user@domain.com print filelist showmimetype gform fields id,name,createdtime
# Get number of responses, add createdTime
gam redirect csv ./formsresponses.csv multiprocess csv forms.csv gam user "~Owner" print formresponses "~id" countsonly addcsvdata createdTime "~createdTime"
# Get full form info, add createdTime and responses (count)
gam redirect csv ./formsinfo.csv multiprocess csv formsresponses.csv gam user "~User" print forms "~formId" addcsvdata createdTime "~createdTime" addcsvdata responses "~responses"
```
