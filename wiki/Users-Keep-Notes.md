# Users - Keep - Notes
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Add Note](#add-note)
- [Delete Note](#delete-note)
- [Display Notes](#display-notes)
- [Download Note Attachments](#download-note-attachments)
- [Manage Notes permissions](#manage-notes-permissions)
  - [Add Permissions](#add-permissions)
  - [Delete Permissions](#delete-permissions)
- [Examples](#examples)

## API documentation
* [Keep API](https://developers.google.com/keep/api/reference/rest)

## Notes
To use these commands you must add the 'Keep API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
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

<JSONData> ::=
        (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<NoteContent> ::=
        ((text <String>)|
         (textfile <FileName> [charset <Charset>])|
         (gdoc <UserGoogleDoc>)|
         (gcsdoc <StorageBucketObjectName>)|
         <JSONData>)

<NotesName> ::= notes/<String>
<NotesNameList> ::= "<NotesName>(,<NotesName)*"
<NotesNameEntity> ::=
        <NotesNameList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<NotesField> ::=
        attachments|
        body|
        createtime|
        name|
        permissions|
        title|
        trashed|
        trashtime|
        updatetime
<NotesFieldList> ::= "<NotesField>(,<NotesField>)*"

<DriveFolderID> ::= <String>
<DriveFolderName> ::= <String>
<DriveFileParentAttribute> ::=
        (parentid <DriveFolderID>)|
        (parentname <DriveFolderName>)|
        (anyownerparentname <DriveFolderName>)|
        (teamdriveparentid <DriveFolderID>)|
        (teamdriveparent <SharedDriveName>)|
        (teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>)|
        (teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>)
```

Keep notes have an ID that is referred to by Google as its `name`; this is the value
you will use wherever `<NotesName>` is required.

## Add Note
```
gam <UserTypeEntity> create note [title <String>]
        [missingtextvalue <String>]
        <NoteContent>
        [copyacls [copyowneraswriter]]
        [compact|formatjson|nodetails]
```
`<NoteContent>` is the note text, there are four ways to specify it:
* `message|textmessage|htmlmessage <String>` - Use `<String>` as the note text
* `file|htmlfile <FileName> [charset <Charset>]` - Read the note text from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the note text from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the note text from the Google Cloud Storage file `<StorageBucketObjectName>`

Use the `<JSONData>` option to specify the title, text and list options.

Use the `missingtextvalue <String>` option to have GAM supply a value for JSON `list` and `text` items that are missing text fields.
This option must appear before the `<JSONData>` option. If not specified and a text field is missing, you'll get the following error:
`Request contains an invalid argument.`

The `title <String>` option takes precedence over the JSON title.

If you specify options `json` and `copyacls`, the note is created and any ACLs
from the json data are added to the note. If you also specify `copyowneraswriter`,
the original note owner is added as a writer to the created note.

By default, Gam displays the created note as an indented list of keys and values; the note text is displayed as individual lines.
* `compact` - Display the note text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the note in JSON format
* `nodetails` - Display the note name only

## Delete Note
```
gam <UserTypeEntity> delete note <NoteNameEntity>
```

## Display Notes
Display selected notes
```
gam <UserTypeEntity> info note <NotesNameEntity>
        [fields <NotesFieldList>]
        [compact|formatjson]
```
By default, Gam displays the information as an indented list of keys and values; the note text is displayed as individual lines.
* `compact` - Display the note text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the note in JSON format

Display all notes
```
gam <UserTypeEntity> show notes
        [fields <NotesFieldList>] [filter <String>]
        [role owner|writer]
        [countsonly]
        [compact|formatjson]
```
By default, GAM displays all non-trashed notes:
* `filter trashed` - Display notes in the trash
* `role owner|writer` - Display notes where the user has the specified role

When  option `countsonly` is specified, the number of notes a user owns, the number of notes of user can edit
and the total number of notes is displayed.

By default, Gam displays the information as an indented list of keys and values; the note text is displayed as individual lines.
* `compact` - Display the note text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the note in JSON format

```
gam <UserTypeEntity> print notes [todrive <ToDriveAttribute>*]
        [fields <NotesFieldList>] [filter <String>]
        [role owner|writer]
        [countsonly]
        [formatjson [quotechar <Character>]]

```
By default, GAM displays all non-trashed notes:
* `filter trashed` - Display notes in the trash
* `role owner|writer` - Display notes where the user has the specified role

When  option `countsonly` is specified, the number of notes a user owns, the number of notes of user can edit
and the total number of notes is displayed.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Download Note Attachments
```
gam <UserTypeEntity> get noteattachments <NotesNameEntity>
        [targetfolder <FilePath>] [targetname <FileName>] [overwrite [<Boolean>]]
        [<DriveFileParentAttribute>]
```
By default, when getting an attachment, it is downloaded to the directory specified in `gam.cfg/drive_dir`.
* `targetfolder <FilePath>` - Specify an alternate location for the downloaded file.

By default, when getting an attachment, the local name is the same as the Note title or `attachment` if the Note doesn't have a title..
* `targetname <FileName>` - Specify an alternate name for the downloaded file.

The strings `#email#`, `#user#` and `#username#` will be replaced by the the user's full emailaddress or just the name portion
in `targetfolder <FilePath>` and `targetname <FileName>`.

The final attachment local file name will have `-<N>.<extension>` appended to the base name:
* `<N>` - The index of the attachment
* `<extension>` - An extension based on the MIME type; `gif, jpg, png, webp`

By default, when getting an attachment, an existing local file will not be overwritten; a numeric prefix is added to the filename.
* `overwrite` - Overwite an existing file
* `overwrite true` - Overwite an existing file
* `overwrite false` - Do not overwite an existing file; add a numeric prefix and create a new file

If `<DriveFileParentAttribute>` is specified, the dowloaded attachments will be uploaded to Google Drive.

## Manage Notes permissions
* The owner of a note can not have it's role changed.
* The owner of a note can not be deleted.
* A new owner can not be added to a note.

### Add permissions
```
gam <UserTypeEntity> create noteacl <NotesNameEntity>
        (user|group <EmailAddress>)+
        <JSONData>
        [nodetails]
```

By default, Gam displays the user, note name, number of created permissions and the permission details
* `nodetails` - Do not display the permission details

### Delete permissions
```
gam <UserTypeEntity> delete noteacl <NotesNameEntity>
        (user|group <EmailAddress>)+
        <JSONData>
```
Use the `user and `group`` options to specify email addresses.

Use the `json` option to specify permissions.
```
{"permissions": [{"email": "user@domain.com", "name": "notes/abc123xyz/permissions/def456uvw", "role": "WRITER", "user": {"email": "user@domain.com"}}]}
```

## Examples
### Copy notes and permissions from one user to another.
```
gam redirect csv ./notes.csv user user1@domain.com print notes formatjson quotechar "'"
gam csv ./notes.csv quotechar "'" gam user user2@domain.com create note json "~JSON" copyacls
```

### Delete all permissions for a note
```
gam redirect stdout ./notes.json user user@domain.com info note notes/abc123xyz permissions formatjson
gam user user@domain.com delete notesacl notes/abc123xyz json file notes.json
```

### Delete all of a user's trashed notes.
```
gam redirect csv ./notes.csv user user@domain.com print notes fields name filter trashed
gam user user@domain.com delete notes csvfile notes.csv:name
```