# Users - Forms
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Create a Form](#create-a-form)
- [Update a Form](#update-a-form)
- [Extended Example](#extended-example)
- [Display Forms](#display-forms)
- [Display Form Responses](#display-form-responses)
- [Combine Form Information](#combine-form-information)

## API documentation
* [Forms API](https://developers.google.com/forms/api/reference/rest)

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
        title <String> [description <String>] [isquiz [Boolean>]] [<JSONData>]
        [ispublished [<Boolean>] isacceptingresponses [<Boolean>]]
        [drivefilename <DriveFileName>] [<DriveFileParentAttribute>]
        [(csv [todrive <ToDriveAttribute>*]) | returnidonly]
```

The valid combinations of `ispublished` and `isacceptingresponses` are:
* `ispublished true isacceptingresponses true`
* `ispublished true isacceptingresponses false`
* `ispublished false isacceptingresponses false`
* `ispublished false` - Sets `isacceptingresponses false`
* `isacceptingresponses false` - Sets `ispublished false`
* `isacceptingresponses true` - Sets `ispublished true`

`<JSONData>` is a list of form update requests.

* See: https://developers.google.com/forms/api/reference/rest/v1/forms/batchUpdate

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
        [title <String>] [description <String>] [isquiz [Boolean>]] [<JSONData>]
        [ispublished [<Boolean>] isacceptingresponses [<Boolean>]]
```

The valid combinations of `ispublished` and `isacceptingresponses` are:
* `ispublished true isacceptingresponses true`
* `ispublished true isacceptingresponses false`
* `ispublished false isacceptingresponses false`
* `ispublished false` - Sets `isacceptingresponses false`
* `isacceptingresponses false` - Sets `ispublished false`
* `isacceptingresponses true` - Sets `ispublished true`

`<JSONData>` is a list of form update requests.

* See: https://developers.google.com/forms/api/reference/rest/v1/forms/batchUpdate

## Extended Example

This example illustrates the use of JSON data to create and update forms
concerning student classtoom attendance.
The form has two items: Absences and Notes.
In `Absences`, the teacher can check `All present.` or check individual student absences.
In `Notes`, explanatory notes can be entered.

### Create
This is the form create request JSON.

The `deleteItem` request deletes the default item on a newly created form.
```
{
  "requests": [
      {"deleteItem": {"location": {"index": 0}}},
      {"createItem": {
          "item": {
              "title": "Absences?",
              "description": "To report attendance adjustments for late arrivals, please email attendance@domain.com.",
              "questionItem": {
                  "question": {
                      "choiceQuestion": {
                          "type": "CHECKBOX","options": [
                              {"value": "All present."},
                              {"value": "Student Name1"},
                              {"value": "Student Name2"},
                              {"value": "Student Name3"},
                              {"value": "Student Name4"}
                          ]
                      },
                      "required": true}
              }
          },
          "location": {"index": 0}
      }},
      {"createItem": {
          "item": {
              "title": "Notes?",
              "questionItem": {"question": {"textQuestion": {"paragraph": true}}}},
          "location": {"index": 1}
      }}
  ]
}
```

This is the create CSV file with the compressed form creation request JSON.
Each row specifies:
* `User` - The form owner
* `name` - The form file name
* `title` and `description` - The form title and description
* `JSON` - The compressed JSON requests

If you are using a local CSV file, surround the JSON data with single quotes `'`;
do not use the quotes if you are using a Google Sheet.
```
User,name,title,description,JSON
attendance@domain.com,MathClassAttendance,Math Class Attendance,Daily Attendance Report,'{"requests": [{"deleteItem": {"location": {"index": 0}}}, {"createItem": {"item": {"title": "Absent?", "description": "To report attendance adjustments for late arrivals, please email attendance@domain.com.", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX","options": [{"value": "All present."}, {"value": "Student Name1"}, {"value": "Student Name2"}, {"value": "Student Name3"}, {"value": "Student Name4"}]}, "required": true}}}, "location": {"index": 0}}}, {"createItem": {"item": {"title": "Notes?", "questionItem": {"question": {"textQuestion": {"paragraph": true}}}}, "location": {"index": 1}}}]}'
```

Build the forms; this example builds the forms in the `User's` root folder, adjust as required.

If you are using a local CSV file, use the `quotechar "'"` option;
do not use the option if you are using a Google Sheet.
```
$ gam redirect csv ./UpdateForms.csv multiprocess redirect stdout ./CreateForms.txt multiprocess redirect stderr stdout csv CreateForms.csv quotechar "'"  gam user "~User" create form drivefilename "~name" parentid root title "~title" description "~description" json "~JSON" csv
2025-01-05T09:36:18.723-08:00,0/1,Using 1 process...
2025-01-05T09:36:18.724-08:00,0,Processing item 1/1
2025-01-05T09:36:23.818-08:00,0/1,Processing complete
```

This is the output 
```
$ more UpdateForms.csv 
User,formId,name,title,responderUri
attendance@domain.com,1xWfG_7sDCgrWDd-oqDCGE328-CozoAmqYMtP3WY2liw,MathClassAttendance,Math Class Attendance,https://docs.google.com/forms/d/e/1FAIpQLScYqOI2A4TBFVC4YwSxES6-lOD3O_jrN4vhkX09wXkNk0Z66w/viewform
```

### Update
This is the form update request JSON; the data is similar to the form create JSON.
The `deleteItem` request is deleted, `createItem` is replaced with `updateItem`, the `updateMask`
key and value are added to each update item. You would typically add, delete or update the `Student Name` values.
```
{
  "requests": [
      {"updateItem": {
	  "item": {
              "title": "Absent?",
              "description": "To report attendance adjustments for late arrivals, please email attendance@domain.com.",
              "questionItem": {
		  "question": {
		      "choiceQuestion": {
			  "type": "CHECKBOX","options": [
			      {"value": "All present."},
			      {"value": "Student Name1"},
			      {"value": "Student Name2"},
			      {"value": "Student Name3"},
			      {"value": "Student Name4"},
			      {"value": "Student Name5"}
			  ]
		      },
		      "required": true}
	      }
	  },
          "location": {"index": 0},
          "updateMask": "title,description,questionItem"}},
      {"updateItem": {
	  "item": {
              "title": "Notes?",
              "questionItem": {"question": {"textQuestion": {"paragraph": true}}}},
          "location": {"index": 1},
          "updateMask": "title,questionItem"}}
  ]
}
```

This is the update CSV file with the compressed form update request JSON.
Each row specifies:
* `User` - The form owner
* `name` - The form file name
* `title` and `description` - The form title and description
* `update` - Can be used to update selected rows
* `JSON` - The compressed JSON requests

If you are using a local CSV file, surround the JSON data with single quotes `'`;
do not use the quotes if you are using a Google Sheet.
```
User,formId,name,title,update,JSON
attendance@domain.com,1xWfG_7sDCgrWDd-oqDCGE328-CozoAmqYMtP3WY2liw,MathClassAttendance,Math Class Attendance,,'{"requests": [{"updateItem": {"item": {"title": "Absent?", "description": "To report attendance adjustments for late arrivals, please email attendance@domain.com.", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX","options": [{"value": "All present."}, {"value": "Student Name1"}, {"value": "Student Name2"}, {"value": "Student Name3"}, {"value": "Student Name4"}, {"value": "Student Name5"}]}, "required": true}}}, "location": {"index": 0}, "updateMask": "title,description,questionItem"}}, {"updateItem": {"item": {"title": "Notes?", "questionItem": {"question": {"textQuestion": {"paragraph": true}}}}, "location": {"index": 1}, "updateMask": "title,questionItem"}}]} '
```

Update all of the forms.

If you are using a local CSV file, use the `quotechar "'"` option;
do not use the option if you are using a Google Sheet.
```
$ gam redirect stdout ./UpdateForms.txt multiprocess redirect stderr stdout csv UpdateForms.csv quotechar "'" gam user "~User" update form "~formId" json "~JSON"
2025-01-05T10:07:00.037-08:00,0/1,Using 1 process...
2025-01-05T10:07:00.037-08:00,0,Processing item 1/1
2025-01-05T10:07:03.110-08:00,0/1,Processing complete
```

Update selected forms; put an `x` in the `update` column of the rows to be updated.
```
$ gam config csv_input_row_filter "update:text=x' redirect stdout ./UpdateForms.txt multiprocess redirect stderr stdout csv UpdateForms.csv quotechar "'" gam user "~User" update form "~formId" json "~JSON"
2025-01-05T10:07:00.037-08:00,0/1,Using 1 process...
2025-01-05T10:07:00.037-08:00,0,Processing item 1/1
2025-01-05T10:07:03.110-08:00,0/1,Processing complete
```

This is the output.
```
$ more UpdateForms.txt 
User: attendance@domain.com, Update 1 Form
  User: attendance@domain.com, Form: 1xWfG_7sDCgrWDd-oqDCGE328-CozoAmqYMtP3WY2liw, Updated
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
