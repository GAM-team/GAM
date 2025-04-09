# Users - Spreadsheets
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [JSON data quoting](#json-data-quoting)
- [Create spreadsheets](#create-spreadsheets)
- [Update spreadsheets](#update-spreadsheets)
- [Display information about spreadsheets](#display-information-about-spreadsheets)
- [Clear values in a spreadsheet](#clear-values-in-a-spreadsheet)
- [Display values in a spreadsheet](#display-values-in-a-spreadsheet)
- [Append/update values in a spreadsheet](#appendupdate-values-in-a-spreadsheet)
- [Extended Examples with show sheetrange](#extended-examples-with-show-sheetrange)
- [Extended Examples with print sheetrange](#extended-examples-with-print-sheetrange)
- [Repair an uneditable sheet within a spreadsheet](#repair-an-uneditable-sheet-within-a-spreadsheet)

## API documentation
* [Sheets API](https://developers.google.com/sheets/api/reference/rest)
* [Sheets API - Create](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/create)
* [Sheets API - Batch Update](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/batchUpdate)
* [Sheets API - Values](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values#ValueRange)
* [Sheets API - Values Append](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append)
* [Sheets API - Insert Data](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append#InsertDataOption)
* [Sheets API - Values Batch Update](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchUpdate)
* [Sheets API - Values Batch Clear](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchClear)
* [Sheets API - Values Batch Get](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchGet)
* [Sheets API - Dimension](https://developers.google.com/sheets/api/reference/rest/v4/Dimension)
* [Sheets API - Value Render](https://developers.google.com/sheets/api/reference/rest/v4/ValueRenderOption)
* [Sheets API - DateTime Render](https://developers.google.com/sheets/api/reference/rest/v4/DateTimeRenderOption)

## Query documentation
* [Search Files](https://developers.google.com/drive/api/v3/search-files)
* [Search Terms](https://developers.google.com/drive/api/v3/ref-search-terms)

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
```
* The following right-hand side characters are literal: `{}[],'":`
* The following right-hand side characters are part of the meta-syntax: `<>()*|`
```
<SpreadsheetJSONCreateRequest> ::=
        '{"properties": {<SpreadsheetProperties>}, "sheets": [{<Sheet>}(,{<Sheet>})*],
          "namedRanges": [{<NamedRange>}(,{<NamedRange>})*],
          "developerMetadata": [{<DeveloperMetadata>}(,{DeveloperMetadata>})]}'
<SpreadsheetJSONUpdateRequest> ::=
        '{"requests": [{<Request>}(,{<Request>})], "includeSpreadsheetInResponse": true|false,
          "responseRanges": ["<SpreadsheetRange>"(,"<SpreadsheetRange>")],
          "responseIncludeGridData": true|false}
<SpreadsheetField> ::=
        developermetadata|
        namedranges|
        properties|
        sheets|
        spreadsheetid|
        spreadsheeturl
<SpreadsheetFieldList> ::= "<SpreadsheetField>(,<SpreadsheetField>)*"
<SpreadsheetSheetsField> ::=
        bandedranges|
        basicfilter|
        charts|
        columngroups|
        conditionalformats|
        data|
        developermetadata|
        filterviews|
        merges|
        properties|
        protectedranges|
        rowgroups|
        slicers
<SpreadsheetRange> ::= <String>
<SpreadsheetRangeList> ::= "'<SpreadsheetRange>'(,'<SpreadsheetRange>')*"
<SpreadsheetValue> ::= "<String>"|<Number>|true|false
<SpreadsheetValueList> ::= "<SpreadsheetValue>(,<SpreadsheetValue>)*"
<SpreadsheetJSONRangeValues> ::=
        '{"range": <SpreadsheetRange>, "values": [<SpreadsheetValueList>(,<SpreadsheetValueList>)*],
          "majorDimension": "ROWS|COLUMNS"}'
<SpreadsheetJSONRangeValuesList> ::=
        '[<SpreadsheetJSONRangeValues>(,<SpreadsheetJSONRangeValues>)*]'
```
## JSON data quoting
When entering JSON data from the command line, different quoting rules apply based on OS.

### Linux/Mac OS
In all cases, surround entire argument in single quotes.
```
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson valuerangesonly
gam user testuser@domain.com update sheetranges drivefilename TestSheet json '[{"range": "A1:C1", "values": [[1, 2, 3]], "majorDimension": "ROWS"}, {"range": "A3:C3", "values": [["10/01/2017 10:30:00", true, 6]], "majorDimension": "ROWS"}]' userentered includevaluesinresponse
```
### Windows PowerShell
For JSON data without double quotes, surround entire argument in double quotes.
```
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range "Sheet1!A1:B2" formatjson valuerangesonly
```
For JSON data with double quotes, surround entire argument in single quotes; guard double quotes with backslah.
```
gam user testuser@domain.com update sheetranges drivefilename TestSheet json '[{\"range\": \"A1:C1\", \"values\": [[1, 2, 3]], \"majorDimension\": \"ROWS\"}, {\"range\": \"A3:C3\", \"values\": [[\"10/01/2017 10:30:00\", true, 6]], \"majorDimension\": \"ROWS\"}]' userentered includevaluesinresponse
```
### Windows Command Prompt
For JSON data without double quotes, surround entire argument in double quotes.
```
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range "Sheet1!A1:B2" formatjson valuerangesonly
```
For JSON data with double quotes, surround entire argument in double quotes; guard double quotes with backslah.
```
gam user testuser@domain.com update sheetranges drivefilename TestSheet json "[{\"range\": \"A1:C1\", \"values\": [[1, 2, 3]], \"majorDimension\": \"ROWS\"}, {\"range\": \"A3:C3\", \"values\": [[\"10/01/2017 10:30:00\", true, 6]], \"majorDimension\": \"ROWS\"}]" userentered includevaluesinresponse
```
### JSON file
When entering data from a JSON file, no special quoting is required.
```
File Sheet.json contains:
[{"range": "A1:C1", "values": [[1, 2, 3]], "majorDimension": "ROWS"}, {"range": "A3:C3", "values": [["10/01/2017 10:30:00", true, 6]], "majorDimension": "ROWS"}]

gam user testuser@domain.com update sheetranges drivefilename TestSheet json file Sheet.json
```
### A field with JSON data from a CSV file
Surround data in single quotes.
```
CSV file Sheet.csv contains:
User,spreadsheetId,JSON
user@domain.com,1MOq6umgWSM7NF8-CQ-Aj3_n1DIu_GvyCcuLxxxxxx,'[{"range": "Sheet1!A1:C1", "values": [["1", "2", "3"]], "majorDimension": "ROWS"}, {"range": "Sheet1!A3:C3", "values": [["10/01/2017 10:30:00", true, "6"]], "majorDimension": "ROWS"}]'

gam csv Sheet.csv quotechar "'" gam user "~User" update sheetranges "~spreadsheetId" json "~JSON" userentered includevaluesinresponse
```
## Create spreadsheets
```
gam <UserTypeEntity> create|add sheet
        ((json [charset <Charset>] <SpreadsheetJSONCreateRequest>) |
         (json file <FileName> [charset <Charset>]))
        [<DriveFileParentAttribute>]
        [formatjson] [returnidonly]
```
The JSON data can be read from a command line argument or a file.

The Google Sheets API creates the spreadheet in the user's root folder; use the following options to have Gam
assign the spreadsheet to a different location. If the assignment fails, the spreadsheet is left in the root folder.
* `parentid <DriveFolderID>` - Folder ID.
* `parentname <DriveFolderName>` - Folder name; the folder must be owned by `<UserTypeEntity>`.
* `anyownerparentname <DriveFolderName>` - Folder name; the folder can be owned by any user, `<UserTypeEntity>` must be able to write to the folder.
* `teamdriveparentid <DriveFolderID>` - Shared Drive folder ID; when used alone, this indicates a specfic Shared Drive folder.
* `teamdriveparent <SharedDriveName>` - Shared Drive name; when used alone, this indicates the root level of the Shared Drive.
* `teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>` - A Shared Drive ID and a folder name  on that Shared Drive.
* `teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>` - A Shared Drive name and a folder name on that Shared Drive.
* If none of the parent options are specified, the parent folder is the root folder.

The output is formatted for human readability; use the following options to produce JSON output
* `formatjson` - Display output in JSON format for program parsing.
* `returnidonly` - Display just the file ID of the created spreadsheet file as output

### Example
Create a basic sheet.

```
File Sheet.json contains:
{"properties": {"title": "Gam Sheet"}, "sheets": [{"properties": {"sheetId": 0, "title": "Gam Tab", "sheetType": "GRID"}}]}

gam user testuser@domain.com create sheet json file Sheet.json
```

## Update spreadsheets
```
gam <UserTypeEntity> update sheet <DriveFileEntity>
        ((json [charset <Charset>] <SpreadsheetJSONUpdateRequest>) |
         (json file <FileName> [charset <Charset>]))
        [formatjson]
```
The JSON data can be read from a command line argument or a file. On the command line, the
JSON data is enclosed in single quotes; these should not be present when the JSON data is read from a file.

The output is formatted for human readability. Use the following option to produce JSON output for program parsing.
* `formatjson` - Display output in JSON format.

### Examples
Add a new tab/sheet to a spreadsheet.
```
File Sheet.json contains:
{"requests": [{"addSheet": {"properties": {"title": "New Sheet", "sheetType": "GRID"}}}]}

gam user testuser@domain.com update sheet <DriveFileItem> json file Sheet.json
```

Delete a tab/sheet from a spreadsheet. 
```
Get the sheet IDs.
gam user testuser@domain.com info sheet <DriveFileItem> fields sheets
Get the desired sheetId from the output.
File Sheet.json contains:
{"requests": [{"deleteSheet": {"sheetId": 1234567890}}]}

gam user testuser@domain.com update sheet <DriveFileItem> json file Sheet.json
```

Rename a tab/sheet in a spreadsheet. 
```
Get the sheet IDs.
gam user testuser@domain.com info sheet <DriveFileItem> fields sheets
Get the desired sheetId from the output.
File Sheet.json contains:
{"requests": [{"updateSheetProperties": {"properties": {"sheetId": 1234567890, "title": "New Title"}, "fields": "title"}}]}

gam user testuser@domain.com update sheet <DriveFileItem> json file Sheet.json
```

Delete a column from a tab in a spreadsheet.
```
Get the sheet IDs.
gam user testuser@domain.com info sheet <DriveFileItem> fields sheets
Get the desired sheetId from the output.
Columns are numbered starting from 0 at the left; specify the starting column and the ending column + 1.
In this example, column B is being deleted.
File Sheet.json contains:
{"requests": [{"deleteRange": {"range": {"sheetId": 1234567890, "startColumnIndex": 1, "endColumnIndex": 2}, "shiftDimension": "COLUMNS"}}]}

gam user testuser@domain.com update sheet <DriveFileItem> json file Sheet.json
```
## Display information about spreadsheets
```
gam <UserTypeEntity> info|show sheet <DriveFileEntity>
        [fields <SpreadsheetFieldList>] [sheetsfields <SpreadsheetSheetsFieldList>]
        (range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
        [includegriddata [<Boolean>]] [shownames]
        [formatjson]
```
By default, the Sheets API does not return the sheet file name, use the `shownames` option to have GAM
make an additional API call to get and display the sheet file name.

The output is formatted for human readability. Use the following option to produce JSON output for program parsing.
* `formatjson` - Display output in JSON format.
```
gam <UserTypeEntity> print sheet <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [fields <SpreadsheetFieldList>] [sheetsfields <SpreadsheetSheetsFieldList>]
        (range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
        [includegriddata [<Boolean>]] [shownames]
        [formatjson [quotechar <Character>]]
```
By default, the Sheets API does not return the sheet file name, use the `shownames` option to have GAM
make an additional API call to get and display the sheet file name.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Clear values in a spreadsheet
```
gam <UserTypeEntity> clear sheetrange <DriveFileEntity>
        (range <SpreadsheetRange>)+ (rangelist <SpreadsheetRangeList>)*
        [formatjson]
```
Multiple ranges can be specified.

With `clear`, the output is formatted for human readability. Use the following option to produce JSON output for program parsing.
* `formatjson` - Display output in JSON format.

### Example
```
gam user testuser@domain.com clear sheetranges drivefilename TestSheet range A4:C5 range A9:C10
``` 
## Display values in a spreadsheet
```
gam <UserTypeEntity> print sheetrange <DriveFileEntity> [todrive <ToDriveAttribute>*]
        (range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
        [rows|columns] [formula|formattedvalue|unformattedvalue]
        [serialnumber|formattedstring]
        [formatjson [quotechar <Character>] [valuerangesonly [<Boolean>]]]
gam <UserTypeEntity> show sheetrange <DriveFileEntity>
        (range <SpreadsheetRange>)* (rangelist <SpreadsheetRangeList>)*
        [rows|columns] [formula|formattedvalue|unformattedvalue]
        [serialnumber|formattedstring]
        [formatjson [valuerangesonly [<Boolean>]]]
```
Multiple ranges can be specified.

Specify how the values are displayed; the default is `rows`.
* `rows` - Display rows of data
* `columns` - Display columns of data

Specify how values should be rendered in the output; the default is `formattedvalue`.
* `formula` - Values will not be calculated; the reply will include the formulas.
* `formattedvalue` - Values will be calculated and formatted in the reply according to the cell's formatting.
* `unformattedvalue` - Values will be calculated, but not formatted in the reply.

Specify how date and time values should be rendered in the output; the default is `formattedstring`.
* `serialnumber` - Instructs date, time, datetime, and duration fields to be output as doubles in "serial number" format, as popularized by Lotus 1-2-3.
* `formattedstring` - Instructs date, time, datetime, and duration fields to be output as strings in their given number format (which is dependent on the spreadsheet locale).

With `show`, the values output is formatted for human readability. With `print`, the values output is expanded into multiple columns.
* `formatjson` - Display values output in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

The `valuerangesonly` option used in conjunction with `formatjson` limits the display to just the `valueRanges` data.
This will make it simpler to capture the sheetrange data, modify it, and update the sheet with the modified data.

### Examples
For Windows, see [JSON data quoting](#json-data-quoting)
```
gam user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson 
Getting all Drive Files/Folders that match query ('me' in owners and name = 'TestSheet') for testuser@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'TestSheet') for testuser@domain.com...
{"User": "testuser@domain.com", "spreadsheetId": "111-Ca4obeBiojvhWFfMH12lHz71GTwBmJGbL-KnYzzz", "JSON": {"valueRanges": [{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]}}
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson 

gam user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson valuerangesonly
Getting all Drive Files/Folders that match query ('me' in owners and name = 'TestSheet') for testuser@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'TestSheet') for testuser@domain.com...
[{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson valuerangesonly

gam user testuser@domain.com print sheetrange name "TestSheet" range 'Sheet1!A1:B2' formatjson quotechar "'"
Getting all Drive Files/Folders that match query ('me' in owners and name = 'TestSheet') for testuser@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'TestSheet') for testuser@domain.com...
User,spreadsheetId,JSON
testuser@domain.com,1uK-Ca4obeBiojvhWFfMH12lHz71GTwBmJGbL-KnY2tM,'{"valueRanges": [{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]}'
gam redirect csv SheetData.csv user testuser@domain.com print sheetrange name "TestSheet" range 'Sheet1!A1:B2' formatjson quotechar "'"

gam user testuser@domain.com print sheetrange name "TestSheet" range 'Sheet1!A1:B2' formatjson quotechar "'" valuerangesonly
Getting all Drive Files/Folders that match query ('me' in owners and name = 'TestSheet') for testuser@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'TestSheet') for testuser@domain.com...
JSON
'[{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]'
gam redirect csv SheetData.csv user testuser@domain.com print sheetrange name "TestSheet" range 'Sheet1!A1:B2' formatjson quotechar "'" valuerangesonly
```

## Append/update values in a spreadsheet
```
gam <UserTypeEntity> append sheetrange <DriveFileEntity>
        ((json [charset <Charset>] <SpreadsheetJSONRangeValues>|<SpreadsheetJSONRangeValuesList>) |
         (json file <FileName> [charset <Charset>]))
        [overwrite|insertrows]
        [raw|userentered] [formula|formattedvalue|unformattedvalue] [serialnumber|formattedstring]
        [includevaluesinresponse [<Boolean>]] [formatjson]
gam <UserTypeEntity> update sheetrange <DriveFileEntity>
        ((json [charset <Charset>] <SpreadsheetJSONRangeValues>|<SpreadsheetJSONRangeValuesList>)+
         (json file <FileName> [charset <Charset>])+)
        [raw|userentered] [formula|formattedvalue|unformattedvalue] [serialnumber|formattedstring]
        [includevaluesinresponse [<Boolean>]] [formatjson]
```
* `append` - Only one range can be specified.
* `update` - Multiple ranges can be specified.

The JSON data can be read from a command line argument or a file.

Specify how data is to be appended to the spreadsheet; the default is `insertrows`.
* `overwrite` - The new data overwrites existing data in the areas it is written.
* `insertrows` - Rows are inserted for the new data.

Specify how the values in `<SpreadsheetValueList>` are to be parsed; the default is `userentered`.
* `raw` - The values the user has entered will not be parsed and will be stored as-is.
* `userentered` - The values will be parsed as if the user typed them into the UI. Numbers will stay as numbers, but strings may be converted to numbers, dates, etc. following the same rules that are applied when entering text into a cell via the Google Sheets UI.

Specify whether the response should include the values of the cells that were appended/updated; the default is false.
* `includevaluesinresponse [<Boolean>]`

Specify how values should be rendered in the output; the default is `formattedvalue`.
* `formula` - Values will not be calculated; the reply will include the formulas.
* `formattedvalue` - Values will be calculated and formatted in the reply according to the cell's formatting.
* `unformattedvalue` - Values will be calculated, but not formatted in the reply.

Specify how date and time values should be rendered in the output; the default is `formattedstring`.
* `serialnumber` - Instructs date, time, datetime, and duration fields to be output as doubles in "serial number" format, as popularized by Lotus 1-2-3.
* `formattedstring` - Instructs date, time, datetime, and duration fields to be output as strings in their given number format (which is dependent on the spreadsheet locale).

With `append` and `update`, the output is formatted for human readability. Use the following option to produce JSON output for program parsing.
* `formatjson` - Display output in JSON format.

### Examples
For Windows, see [JSON data quoting](#json-data-quoting)

Update a spreadhseet with JSON data from the command line. All of the data must be on one line.
```
gam user user@domain.com update sheetrange name TestSheet json '[{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]'
```
Update a spreadsheet with JSON data from a file.

The JSON parser is OK with the values being on separate lines in the file, as long as the syntax is correct.
Do note that the JSON file contains information on where the data is to be updated, referenced with both sheet name and range.
```
more SheetData.json
[{"range": "Sheet1!C2:E3", "majorDimension": "ROWS", "values":
[["0102", "0304", "AB"],
["0506", "0708", "CD"]]},
{"range": "Sheet2!B9:C10", "majorDimension": "ROWS", "values":
[["0910", "1112"],
["1314", "1516"]]}]

gam user user@domain.com update sheetrange name TestSheet json file SheetData.json
```

## Extended Examples with show sheetrange
For Windows, see [JSON data quoting](#json-data-quoting)

Increment values in a sheet with local data; repeat these steps as required.
- Get the current sheet data with `show sheetrange`
```
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson valuerangesonly
more SheetData.json
[{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]
```
- Edit SheetData.json
- Update the sheet data
```
gam user testuser@domain.com update sheetrange name TestSheet json file SheetData.json
```

Replace values in a sheet with local data.
- Get the current sheet data; perform this step once.
```
gam redirect stdout SheetData.json user testuser@domain.com show sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson valuerangesonly
```
Replace values in a sheet with local data; repeat these steps as required.
- Edit SheetData.json
- Update the sheet data
```
gam user testuser@domain.com update sheetrange name TestSheet json file SheetData.json
```

## Extended Examples with print sheetrange
For Windows, see [JSON data quoting](#json-data-quoting)

Increment values in a sheet with local data; repeat these steps as required.
- Get the current sheet data
```
gam redirect csv SheetData.csv user testuser@domain.com print sheetrange name TestSheet range 'Sheet1!A1:B2' formatjson quotechar "'" valuerangesonly
more SheetData.csv
JSON
'[{"range": 'Sheet1!A1:B2', "majorDimension": "ROWS", "values": [["11", "12"], ["21", "22"]]}]'
```
- Edit SheetData.csv
- Update the sheet data
```
gam csv SheetData.csv quotechar "'" gam user testuser@domain.com update sheetrange name TestSheet json "~JSON"
```

Update values in multiple users/sheets.
- Users/sheets to update
```
more SheetsToUpdate.csv
User,SpreadsheetName,Rangelist
testuser1@domain.com,SimpleSheet,"'Sheet1!A1:C1','Sheet1!C3'"
testuser2@domain.com,TestSheet,'Sheet1!A1:B2'
```
- Get the current sheet data
```
gam redirect csv SheetData.csv multiprocess csv SheetsToUpdate.csv gam user "~User" print sheetrange name "~SpreadsheetName" rangelist "~Rangelist" formatjson quotechar "'"
```
- Edit SheetData.csv
- Update the sheet data
```
gam csv SheetData.csv quotechar "'" gam user "~User" update sheetrange "~spreadsheetId" json "~JSON"
```

## Repair an uneditable sheet within a spreadsheet
Identify uneditable sheet; there is no `editors` field.
```
$ gam user owner@domain.com info sheet 1234-y9d0nbckO_cnb3xyZhsIh0Hxd9WaqpGPBwxyz fields sheets sheetsfields protectedranges
User: owner@domain.com, Show Info 1 Spreadsheet
  Spreadsheet: 1234-y9d0nbckO_cnb3xyZhsIh0Hxd9WaqpGPBwxyz
...
    Sheet: Test (5/5)
      properties:
        gridProperties:
          columnCount: 76
          frozenColumnCount: 1
          hideGridlines: True
          rowCount: 60
        index: 49
        sheetId: 420957925
        sheetType: GRID
        title: Test
      protectedRanges:
        protectedRangeId: 2117059324
        range:
          sheetId: 420957925
```
Make a JSON file that will add the `editors` field.
```
$ cat RepairSheet.json
{"requests": [
{"updateProtectedRange": {"protectedRange": {"protectedRangeId": 2117059324, "editors": {"users": ["owner@domain.com]}}, "fields": "editors"}}
]}
```

Apply the repair update.
```
$ gam user owner@domain.com update sheet 1234-y9d0nbckO_cnb3xyZhsIh0Hxd9WaqpGPBwxyz json file RepairSheet.json
User: user@domain.com, Update 1 Spreadsheet
  User: owner@domain.com, Spreadsheet: 1234-y9d0nbckO_cnb3xyZhsIh0Hxd9WaqpGPBwxyz, Updated
    replies:
```

Verify the repair.
```
$ gam user owner@domain.com info sheet 1234-y9d0nbckO_cnb3xyZhsIh0Hxd9WaqpGPBwxyz fields sheets sheetsfields protectedranges
User: owner@domain.com, Show Info 1 Spreadsheet
  Spreadsheet: 1234-y9d0nbckO_cnb3xyZhsIh0Hxd9WaqpGPBwxyz
...
    Sheet: Test (5/5)
      properties:
        gridProperties:
          columnCount: 76
          frozenColumnCount: 1
          hideGridlines: True
          rowCount: 60
        index: 49
        sheetId: 420957925
        sheetType: GRID
        title: Test
      protectedRanges:
        protectedRangeId: 2117059324
        editors:
          users:
            owner@domain.com
        range:
          sheetId: 420957925
```