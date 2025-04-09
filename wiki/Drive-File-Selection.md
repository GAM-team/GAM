# Drive File Selection
- [Definitions](#definitions)
- [Introduction](#introduction)
- [Select file by ID](#select-file-by-id)
- [Select files by their characteristics](#select-files-by-their-characteristics)
  - [Select with Drive File API query](#select-with-drive-file-api-query)
  - [Select file by name](#select-file-by-name)
  - [Select file ownership](#select-file-ownership)
  - [Select MIME type](#select-MIME-type)
  - [Select file ownership and MIME type](#select-file-ownership-and-mime-type)
  - [Select based on file size](#select-based-on-file-size)
  - [Select based on file name](#select-based-on-file-name)
  - [Select based on permission matching](#select-based-on-permission-matching)
- [Select root folder](#select-root-folder)
- [Select a list of file IDs](#select-a-list-of-file-ids)
- [Select Shared Drive file by ID](#select-shared-drive-file-by-id)
- [Select Shared Drive file by name](#select-shared-drive-file-by-name)
- [Select Shared Drive file by query](#select-shared-drive-file-by-query)
- [Select root folder of a Shared Drive by ID](#select-root-folder-of-a-shared-drive-by-id)
- [Select root folder of a Shared Drive by name](#select-root-folder-of-a-shared-drive-by-name)

## Definitions
```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<DriveFileID> ::= <String>
        https://drive.google.com/open?id=<DriveFileID>
        https://drive.google.com/drive/files/<DriveFileID>
        https://drive.google.com/drive/folders/<DriveFileID>
        https://drive.google.com/drive/folders/<DriveFileID>?resourcekey=<String>
        https://drive.google.com/file/d/<DriveFileID>/<String>
        https://docs.google.com>/document/d/<DriveFileID>/<String>
        https://docs.google.com>/drawings/d/<DriveFileID>/<String>
        https://docs.google.com>/forms/d/<DriveFileID>/<String>
        https://docs.google.com>/presentation/d/<DriveFileID>/<String>
        https://docs.google.com>/spreadsheets/d/<DriveFileID>/<String>
<DriveFileItem> ::= <DriveFileID>|<DriveFileURL>
<DriveFileList> ::= "<DriveFileItem>(,<DriveFileItem>)*"
<DriveFileIDEntity> ::=
        (<DriveFileItem>)|(id( |:)<DriveFileItem>)|(ids( |:)<DriveFileList>)
<DriveFileName> ::= <String>
<DriveFileNameEntity> ::=
        (drivefilename <DriveFileName>)|(drivefilename:<DriveFileName>)|
        (anydrivefilename <DriveFileName>)|(anydrivefilename:<DriveFileName>)
<DriveFolderID> ::= <String>
<DriveFolderIDList> ::= "<DriveFolderID>(,<DriveFolderID>)*"
<DriveFolderName> ::= <String>
<QueryDriveFile> :: = <String> See: https://developers.google.com/drive/api/v3/search-files
<DriveFileQueryEntity> ::= 
        (query <QueryDriveFile>) | (query:<QueryDriveFile>)
<DriveFileQueryShortcut> ::=
        all_files |
        all_folders |
        all_forms |
        all_google_files |
        all_non_google_files |
        all_shortcuts |
        all_3p_shortcuts |
        all_items |
        my_commentable_items |
        my_docs |
        my_files |
        my_folders |
        my_forms |
        my_google_files |
        my_non_google_files |
        my_presentations |
        my_publishable_items |
        my_sheets |
        my_shortcuts |
        my_slides |
        my_3p_shortcuts |
        my_items |
        my_top_files |
        my_top_folders |
        my_top_items |
        others_files |
        others_folders |
        others_forms |
        others_google_files |
        others_non_google_files |
        others_shortcuts |
        others_3p_shortcuts |
        others_items |
        writable_files

<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<SharedDriveIDEntity> ::= (teamdriveid <SharedDriveID>) | (teamdriveid:<SharedDriveID>)
<SharedDriveNameEntity> ::= (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
<SharedDriveFileNameEntity> ::= (teamdrivefilename <DriveFileName>) | (teamdrivefilename:<DriveFileName>)

<SharedDriveEntity> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>
<SharedDriveAdminQueryEntity> ::=
        (teamdriveadminquery <QueryTeamDrive>) | (teamdriveadminquery:<QueryTeamDrive>)
<SharedDriveFileQueryEntity> ::= 
        (query <QueryDriveFile>) | (query:<QueryDriveFile>)
<SharedDriveFileQueryShortcut> ::=
        all_files | all_folders | all_google_files | all_non_google_files | all_items
<SharedDriveEntityAdmin> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>|
        <SharedDriveAdminQueryEntity>
<DriveFileEntity> ::=
        <DriveFileIDEntity> |
        <DriveFileNameEntity> |
        <DriveFileQueryEntity> |
        <DriveFileQueryShortcut> |
        mydrive | mydriveid |
        root | rootid |
        <SharedDriveIDEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveNameEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveFileNameEntity> |
        <SharedDriveFileQueryEntity> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector>) | <CSVDataSelector>)
```
## Introduction
Many Gam commands operate on Google Drive files, there are multiple ways to specify the file on which to operate.
The Google Drive REST API can only manipulate files by ID; you either specify an ID or an option that will produce an ID.

## Select file by ID
Select a file by giving its unique ID.

There are multiple formats for backwards compatibility with old Gam commands that used different formats to specify the same data.
```
<DriveFileIDEntity> ::=
        <DriveFileItem> |
        (id <DriveFileItem>) | (id:<DriveFileItem>) |
        (ids <DriveFileList>) | (ids:<DriveFileList>)
```
### Examples
```
gam user testuser show fileinfo 1234ABCD
gam user testuser show fileinfo id 1234ABCD
gam user testuser show fileinfo id:1234ABCD
gam user testuser show fileinfo https://drive.google.com/a/domain.com/file/d/1234ABCD
gam user testuser show fileinfo ids "1234ABCD,5678EFGH"
gam user testuser show fileinfo ids:"1234ABCD,5678EFGH"
```
## Select files by their characteristics
The `print|show filetree|filelist` have variety of options for choosing the files to display.

## Select with Drive File API query
The Google Drive API has a query option that you can use to select files.
* https://developers.google.com/drive/api/v3/search-files
* https://developers.google.com/drive/api/v3/ref-search-terms

```
<DriveFileQueryEntity> ::= 
        (query <QueryDriveFile>) | (query:<QueryDriveFile>)
```
The default query for selecting files is `'me' in owners`; all files and folders in `My Drive` that the user owns.
You can specify multiple `query <QueryDriveFile>` and `query:<QueryDriveFile>` options.
Each one is appended to the default/existing query with `and (<QueryDriveFile>)`.

The are several options manipulate the query.

## Select file by name
If you have a file name, a search must be performed to find the ID that matches the name.
Remember, searching for a file by name may return several file IDs if you have multiple files with the same name.

There are multiple formats for backwards compatibility with old Gam commands that used different formats to specify the same data.
If a drive file name contains spaces or commas, it must be enclosed in quotes.
```
<DriveFileNameEntity> ::=
        (anyname <DriveFileName>) | (anyname:<DriveFileName>) | (anydrivefilename <DriveFileName>) | (anydrivefilename:<DriveFileName>) |
        (name <DriveFileName>) | (name:<DriveFileName>) | (drivefilename <DriveFileName>) | (drivefilename:<DriveFileName>) |
        (othername <DriveFileName>) | (othername:<DriveFileName>) | (otherdrivefilename <DriveFileName>) | (otherdrivefilename:<DriveFileName>)
```
* `anyname <DriveFileName>` - `(name = '<DriveFileName>')`
* `anyname:<DriveFileName>` - `(name = '<DriveFileName>')`
* `anydrivefilename <DriveFileName>` - `(name = '<DriveFileName>')`
* `anydrivefilename:<DriveFileName>` - `(name = '<DriveFileName>')`
* `name <DriveFileName>` - `('me' in owners and name = '<DriveFileName>')`
* `name:<DriveFileName>` - `('me' in owners and name = '<DriveFileName>')`
* `drivefilename <DriveFileName>` - `('me' in owners and name = '<DriveFileName>')`
* `drivefilename:<DriveFileName>` - `('me' in owners and name = '<DriveFileName>')`
* `othername <DriveFileName>` - `(not 'me' in owners and name = '<DriveFileName>')`
* `othername:<DriveFileName>` - `(not 'me' in owners and name = '<DriveFileName>')`
* `otherdrivefilename <DriveFileName>` - `(not 'me' in owners and name = '<DriveFileName>')`
* `otherdrivefilename:<DriveFileName>` - `(not 'me' in owners and name = '<DriveFileName>')`

### Examples
```
gam user testuser show fileinfo drivefilename "Test File"
gam user testuser show fileinfo drivefilename:"Test File"
gam user testuser show fileinfo anydrivefilename "Test File"
gam user testuser show fileinfo anydrivefilename:"Test File"
```
## Select file ownership
By default, files the user owns are displayed; you can select the ownership characteristic.
```
anyowner|(showownedby any|me|others)
```
* `showownedby any` or `anyowner` - Removes `'me' in owners` and `not 'me' in owners` from the query
* `showownedby me` - Adds `'me' in owners` to the query
* `showownedby others` - Adds `not 'me' in owners` to the query

## Select MIME type

By default, all types of files and folders are displayed; you can specify a list of MIME types to display or a list of MIME types to suppress.
```
<MimeTypeShortcut> ::=
        gdoc|gdocument|
        gdrawing|
        gfile|
        gfolder|gdirectory|
        gform|
        gfusion|
        gjam|
        gmap|
        gpresentation|
        gscript|
        gshortcut|
        g3pshortcut|
        gsheet|gspreadsheet|
        gsite
<MimeTypeName> ::= application|audio|font|image|message|model|multipart|text|video
<MimeType> ::= <MimeTypeShortcut>|(<MimeTypeName>/<String>)
<MimeTypeList> ::= "<MimeType>(,<MimeType>)*"
```
This is the mapping from `<MimeTypeShortcut>` to MIME type.
* `gdoc|gdocument` - application/vnd.google-apps.document
* `gdrawing` - application/vnd.google-apps.drawing
* `gfile` - application/vnd.google-apps.file
* `gfolder|gdirectory` - application/vnd.google-apps.folder
* `gform` - application/vnd.google-apps.form
* `gfusion|gfusiontable` - application/vnd.google-apps.fusiontable
* `gjam` - application/vnd.google-apps.jam
* `gmap` - application/vnd.google-apps.map
* `gpresentation` - application/vnd.google-apps.presentation
* `gscript` - application/vnd.google-apps.script
* `gshortcut` - application/vnd.google-apps.shortcut
* `g3pshortcut` - application/vnd.google-apps.drive-sdk
* `gsite` - application/vnd.google-apps.site
* `gsheet|gspreadsheet` - application/vnd.google-apps.spreadsheet

Display files and folders with specified MIME types
```
showmimetype <MimeTypeList>
```
Adds `(mimeType = '<MimeType>' or mimeType = '<MimeType>' ...)` to the query,

Display files and folders with MIME types other than those specified
```
showmimetype not <MimeTypeList>
```
Adds `(mimeType != '<MimeType>' and mimeType != '<MimeType>' ...)` to the query.

## Select file ownership and MIME type
The options combine ownership and broad MIME type selections.
```
<DriveFileQueryShortcut> ::=
        all_files | all_folders | all_google_files | all_non_google_files | all_items |
        my_docs | my_files | my_folders | my_forms | my_google_files | my_non_google_files | my_items |
        my_presentations | my_publishable_items | my_sheets | my_slides |
        my_top_files | my_top_folders | my_top_items |
        others_files | others_folders | others_google_files | others_non_google_files | others_items |
        writable_files
```
* all_files - "mimeType != 'application/vnd.google-apps.folder'"
* all_folders - "mimeType = 'application/vnd.google-apps.folder'"
* all_google_files - "mimeType != 'application/vnd.google-apps.folder' and mimeType contains 'vnd.google'"
* all_non_google_files - "not mimeType contains 'vnd.google'"
* all_items - "" (An empty query specifies all files and folders)
* my_docs - "'me' in owners and mimeType = 'application/vnd.google-apps.document'"
* my_files - "'me' in owners and mimeType != 'application/vnd.google-apps.folder'"
* my_folders - "'me' in owners and mimeType = 'application/vnd.google-apps.folder'"
* my_forms - "'me' in owners and mimeType = 'application/vnd.google-apps.form'"
* my_google_files - "'me' in owners and mimeType != 'application/vnd.google-apps.folder' and mimeType contains 'vnd.google'"
* my_non_google_files - "'me' in owners and not mimeType contains 'vnd.google'"
* my_presentations - "'me' in owners and mimeType = 'application/vnd.google-apps.presentation'"
* my_publishable_items - "'me' in owners and (mimeType = 'application/vnd.google-apps.document' or mimeType = 'application/vnd.google-apps.form' or mimeType = 'application/vnd.google-apps.presentation' or mimeType = 'application/vnd.google-apps.spreadsheet')"
* my_sheets - "'me' in owners and mimeType = 'application/vnd.google-apps.spreadsheet'"
* my_slides - "'me' in owners and mimeType = 'application/vnd.google-apps.presentation'"
* my_items - "'me' in owners"
* my_top_files - "'me' in owners and mimeType != 'application/vnd.google-apps.folder' and 'root' in parents"
* my_top_folders - "'me' in owners and mimeType = 'application/vnd.google-apps.folder' and 'root' in parents"
* my_top_items - "'me' in owners and 'root' in parents"
* others_files - "not 'me' in owners and mimeType != 'application/vnd.google-apps.folder'"
* others_folders - "not 'me' in owners and mimeType = 'application/vnd.google-apps.folder'"
* others_google_files - "not 'me' in owners and mimeType != 'application/vnd.google-apps.folder' and mimeType contains 'vnd.google'"
* others_non_google_files - "not 'me' in owners and not mimeType contains 'vnd.google'"
* others_items - "not 'me' in owners"
* writable_files - "'me' in writers and mimeType != 'application/vnd.google-apps.folder'"

## Select based on file size
For these filters, GAM processes then after the list of files is downloaded. You can combine these
options `query <QueryDriveFile>` to minimize the number of files downloaded but they also work with other
file selection options.

Limit the display to files with binary content of size greater than or equal to a number of bytes.
```
minimumfilesize <Integer>`
```
## Select based on file name
The Google Drive API has limited name matching in the query; Limit the display to files whose name matches `<REMatchPattern>`.
```
filenamematchpattern <REMatchPattern>`
```
## Select based on permission matching
Use [Permission matches](#permission-matches) to limit the display to files with matching permissions.

### Examples
```
gam user testuser show fileinfo query "name='Test File'"
gam user testuser show fileinfo query:"name='Test Folder' and mimeType='application/vnd.google-apps.folder'"
gam user testuser print filelist my_non_google_files
```
## Select root folder
```
root|mydrive
```
Examples
```
gam user testuser show fileinfo root
```
## Select a list of file IDs
You can select a list of file IDs by referencing files that contain file IDs.
```
<DriveFileEntity> ::=
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector>) | <CSVDataSelector>)
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
```
* [Collections of Items](Collections-of-Items)

## Select Shared Drive file by ID
Select a Shared Drive file by giving its unique ID.
```
<SharedDriveIDEntity> ::=
        <DriveFileItem> |
        (teamdriveid <DriveFileItem>) | (teamdriveid:<DriveFileItem>)
```
### Examples
```
gam user testuser show fileinfo 1234ABCD
gam user testuser show fileinfo id 1234ABCD
gam user testuser show fileinfo teamdriveid 1234ABCD
```
## Select Shared Drive file by name
If you have the name, a search must be performed to find the ID that matches the name.
You must specify the Shared Drive, either by ID or name, and the name of the file.

Remember, searching for a file by name may return several file IDs if you have multiple files with the same name.
```
<SharedDriveIDEntity> ::=
        (teamdriveid <DriveFileItem>) | (teamdriveid:<DriveFileItem>)
<SharedDriveNameEntity> ::=
        (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
<SharedDriveFileNameEntity> ::=
        (teamdrivefilename <DriveFileName>) | (teamdrivefilename:<DriveFileName>)
```
### Examples
```
gam user testuser show fileinfo teamdriveid 1234ABCD teamdrivefilename  "Test File"
gam user testuser show fileinfo teamdrive "Shared Drive 1"  teamdrivefilename "Test File"
```
## Select Shared Drive file by query
You can use a query to find a file ID. You perform the query on all Shared Drives or a specific Shared Drive.

See: [Drive Query](https://developers.google.com/drive/api/v3/search-files)
```
<SharedDriveFileQueryEntity> ::=
        (teamdrivequery <QueryDriveFile>) | (teamdrivequery:<QueryDriveFile>)
<SharedDriveFileQueryShortcut> ::=
        all_files | all_folders | all_google_files | all_non_google_files | all_items
```
Keyword to query mappings for `<DriveFileQueryShortcut>`:
* all_files - "mimeType != 'application/vnd.google-apps.folder'"
* all_folders - "mimeType = 'application/vnd.google-apps.folder'"
* all_google_files - "mimeType != 'application/vnd.google-apps.folder' and mimeType contains 'vnd.google'"
* all_non_google_files - "not mimeType contains 'vnd.google'"
* all_items - "" (An empty query specifies all files and folders)

### Examples
```
gam user testuser show fileinfo teamdrivequery "name='Test File'"
gam user testuser show fileinfo teamdriveid 1234ABCD teamdrivequery "name='Test File'"
gam user testuser show fileinfo teamdrive teamdrive "Shared Drive 1" teamdrivequery "name='Test File'"
gam user testuser show fileinfo teamdriveid 1234ABCD all_non_google_files
```
## Select root folder of a Shared Drive by ID
The root folder of a Shared Drive is a folder, you select it by giving its unique ID.
```
<SharedDriveIDEntity> ::=
        <DriveFileItem> |
        (teamdriveid <DriveFileItem>) | (teamdriveid:<DriveFileItem>)
```
### Examples
```
gam user testuser show fileinfo 1234ABCD
gam user testuser show fileinfo teamdriveid 1234ABCD

```
## Select root folder of a Shared Drive by name
If you have a Shared Drive name, a search must be performed to find the ID that matches the name.
```
<SharedDriveNameEntity> ::=
        (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
```
### Examples
```
gam user testuser show fileinfo teamdrive "Shared Drive 1"

```
