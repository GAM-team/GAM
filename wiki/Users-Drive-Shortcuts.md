# Users - Drive Shortcuts
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Python Regular Expressions](Python-Regular-Expressions) Sub function
- [Definitions](#definitions)
- [Create shortcuts](#create-shortcuts)
- [Check shortcut validity](#check-shortcut-validity)
- [Delete broken shortcuts](#delete-broken-shortcuts)
- [Delete stale shortcuts](#delete-stale-shortcuts)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
* [Shortcuts](https://developers.google.com/drive/api/v3/shortcuts)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
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
## Create shortcuts
```
gam <UserTypeEntity> create|add drivefileshortcut <DriveFileEntity> [shortcutname <String>]
        [<DriveFileParentAttribute>|convertparents]
        [csv [todrive <ToDriveAttribute>*]] [returnidonly]
```
Shortcuts will be created for all files in `<DriveFileEntity>`; if `shortcutname <String>`
is not specified, the shortcuts will be named `<DriveFileName>` where `<DriveFileName>`
is the name of each file referenced in `<DriveFileEntity>`. `<String>` can contain the string `#filename#` which will be replaced with
`<DriveFileName>`; e.g., `shortcutname "Shortcut to #filename#"`.

There are two modes of operaton:
* `<DriveFileParentAttribute>` - Create shortcuts in specific locations
  * `parentid <DriveFolderID>` - Folder ID.
  * `parentname <DriveFolderName>` - Folder name; the folder must be owned by `<UserTypeEntity>`.
  * `anyownerparentname <DriveFolderName>` - Folder name; the folder can be owned by any user, `<UserTypeEntity>` must be able to write to the folder.
  * `teamdriveparentid <DriveFolderID>` - Shared Drive folder ID; when used alone, this indicates a specfic Shared Drive folder.
  * `teamdriveparent <SharedDriveName>` - Shared Drive name; when used alone, this indicates the root level of the Shared Drive.
  * `teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>` - A Shared Drive ID and a folder name  on that Shared Drive.
  * `teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>` - A Shared Drive name and a folder name on that Shared Drive.
* `convertparents` - Convert all but the last parent reference in `<DriveFileEntity>` to shortcuts. My testing shows that as parents are added to a file, they are added to the front of the parents list; thus, the last parent is the original parent.

If neither `<DriveFileParentAttribute>` nor `convertparents` are specified, the shortcut is placed in the root folder (My Drive).

When creating shortcuts in specific locations, duplicate shortcuts will not be created.
A duplicate shortcut is one that is in the same folder as another shortcut of the same name pointing to the
same target file/folder.

By default, the user, shortcut name(ID) and file name(ID) are displayed on stdout.
* `returnidonly` - Display just the shortcut ID of the created shortcut on stdout

Alternatively, you can direct the output to a CSV file:
* `csv [todrive <ToDriveAttribute>*]` - Write user, shortcut name, shortcut ID, file name and file ID values to a CSV file.

To retrieve the shortcut ID with `returnidonly`:
```
Linux/MacOS
fileId=$(gam user user@domain.com create drivefileshortcut ... returnidonly)
Windows PowerShell
$fileId = & gam user user@domain.com create drivefileshortcut ... returnidonly
```
The shortcut ID will only be valid when the return code of the command is 0; program accordingly.

### Examples
Create a shortcut where the shortcut name is the same as the target filename.
```
$ gam user testsimple create drivefileshortcut name "My Doc" parentname "Top Folder"
User: user@domain.com, Drive File: My Doc, Create 1 Drive File Shortcut
  User: user@domain.com, Drive File: My Doc, Drive File Shortcut: My Doc(xxxD5Txq7Ptt_V-eQJMkW-O1ZS3EORzzz), Created
```
Create a shortcut where the shortcut name is different from the target filename.
```
$ gam user testsimple create drivefileshortcut name "My Doc" parentname "Top Folder" shortcutname "Shortcut to #filename#"
User: user@domain.com, Drive File: My Doc, Create 1 Drive File Shortcut
  User: user@domain.com, Drive File: My Doc, Drive File Shortcut: Shortcut to My Doc(xxxVCDtuBaJ7bc64rbK5FTVyy6ZxQyzzz), Created

$ gam user testsimple create drivefileshortcut name "My Doc 1" parentname "Top Folder" returnidonly
xxxDmNzbA86RAacOgeGqK6n9jwV2ypzzz
```
## Check shortcut validity
The files/folders that shortcuts reference can be deleted or have their MIME type changed so that it doesn't
match the MIME type specified in the shortcut. You can check the validity of shortcuts.
```
gam <UserTypeEntity> check drivefileshortcut <DriveFileEntity>
        [csv [todrive <ToDriveAttribute>*]]
```
By default, the user, shortcut name(ID) and file name(ID) and validity are displayed on stdout.

Alternatively, you can direct the output to a CSV file:
* `csv [todrive <ToDriveAttribute>*]` - Write user and shortcut/target file details to a CSV file.
  * `User` - User email address
  * `name` - Shortcut file name
  * `id` - Shortcut file ID
  * `owner` - Shortcut file owner
  * `parentId` - Shortcut file parent
  * `shortcutDetails.targetId` - Target file ID in shortcut
  * `shortcutDetails.targetMimeType` - Target file MIME type in shortcut
  * `targetName` - Target file name
  * `targetId` - Target file ID
  * `targetMimeType` - Target file MIME type
  * `code` - 
    * 0 - Valid shortcut: `shortcutDetails.targetId` exists and `shortcutDetails.targetMimeType` matches `targetMimeType`
    * 1 - File `id` not found
    * 2 - File `id` is not a shortcut
    * 3 - File `shortcutDetails.targetId` not found
    * 4 - `shortcutDetails.targetMimeType` does not match `targetMimeType`

## Delete broken shortcuts
You can delete shortcuts that point to files that have been deleted.

`my_shortcuts` is a synonym for `query ('me' in owners and mimeType = 'application/vnd.google-apps.shortcut')`
```
gam redirect csv ./Shortcuts.csv user user@domain.com check drivefileshortcut my_shortcuts csv
gam csv Shortcuts.csv matchfield code 3 gam user "~owner" delete drivefile "~id"
```

## Delete stale shortcuts
You can delete/create shortcuts that point to files whose MIME type has changed; short cuts can't be updated.

`my_shortcuts` is a synonym for `query ('me' in owners and mimeType = 'application/vnd.google-apps.shortcut')`
```
gam redirect csv ./Shortcuts.csv user user@domain.com check drivefileshortcut my_shortcuts csv
gam csv Shortcuts.csv matchfield code 4 gam user "~owner" delete drivefile "~id"
gam csv Shortcuts.csv matchfield code 4 gam user "~owner" create drivefileshortcut "~targetId" parentid "~parentId" shortcutname "~name"
```

## Check shortcut validity on Shared Drives
```
gam redirect csv ./TDShortcuts.csv user organizer@domain.com print filelist select teamdriveid <SharedDriveID> showmimetype gshortcut fields id
gam redirect csv ./Shortcuts.csv user organizer@domain.com check drivefileshortcut csvfile TDShortcuts.csv:id csv
```
