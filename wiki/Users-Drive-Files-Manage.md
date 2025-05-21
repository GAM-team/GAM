# Users - Drive Files Manage
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Python Regular Expressions](Python-Regular-Expressions) Sub function
- [Permission Matches](Permission-Matches)
- [Definitions](#definitions)
- [Create files](#create-files)
  - [Create folders](#create-folders)
  - [Bulk Create Files and Folders](#bulk-create-files-and-folders)
  - [Bulk Create Student Folders on a Shared Drive](#bulk-create-student-folders-on-a-shared-drive)
  - [Create folder hierarchy](#create-folder-hierarchy)
  - [Bulk Create folder hierarchies](#bulk-create-folder-hierarchies)
- [Update files](#update-files)
- [Download files](#download-files)
- [Trash files](#trash-files)
- [Untrash files](#untrash-files)
- [Purge files](#purge-files)
- [Copy/Move Files](Users-Drive-Copy-Move)
- [Shortcuts](Users-Drive-Shortcuts)
- [Classification Labels](Users-Classification-Labels)
- [Download Google Documents as JSON](#download-google-documents-as-json)
- [Upload changes to Google Documents](#upload-changes-to-google-documents)
- [Download and Upload Google Apps Scripts](#download-and-upload-google-apps-scripts)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
* [Shortcuts](https://developers.google.com/drive/api/guides/shortcuts)
* [Third-party Apps](https://support.google.com/a/answer/6105699)
* [Move content to Shared Drives](https://support.google.com/a/answer/7374057)
* [Shared Drive Limits](https://support.google.com/a/users/answer/7338880)
* [My Drive Shared Drive API differences](https://developers.google.com/drive/api/v3/shared-drives-diffs)
* [Google Docs API](https://developers.google.com/docs/api/reference/rest)
* [Limited and Expansive Access](https://developers.google.com/workspace/drive/api/guides/limited-expansive-access)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<ColorHex> ::= "#<Hex><Hex><Hex><Hex><Hex><Hex>"
<ColorNameGoogle> ::=
        asparagus|bluevelvet|bubblegum|cardinal|chocolateicecream|denim|desertsand|
        earthworm|macaroni|marsorange|mountaingray|mountaingrey|mouse|oldbrickred|
        pool|purpledino|purplerain|rainysky|seafoam|slimegreen|spearmint|
        toyeggplant|vernfern|wildstrawberries|yellowcab
<ColorNameWeb> ::=
        aliceblue|antiquewhite|aqua|aquamarine|azure|beige|bisque|black|blanchedalmond|
        blue|blueviolet|brown|burlywood|cadetblue|chartreuse|chocolate|coral|
        cornflowerblue|cornsilk|crimson|cyan|darkblue|darkcyan|darkgoldenrod|darkgray|
        darkgrey|darkgreen|darkkhaki|darkmagenta|darkolivegreen|darkorange|darkorchid|
        darkred|darksalmon|darkseagreen|darkslateblue|darkslategray|darkslategrey|
        darkturquoise|darkviolet|deeppink|deepskyblue|dimgray|dimgrey|dodgerblue|
        firebrick|floralwhite|forestgreen|fuchsia|gainsboro|ghostwhite|gold|goldenrod|
        gray|grey|green|greenyellow|honeydew|hotpink|indianred|indigo|ivory|khaki|
        lavender|lavenderblush|lawngreen|lemonchiffon|lightblue|lightcoral|lightcyan|
        lightgoldenrodyellow|lightgray|lightgrey|lightgreen|lightpink|lightsalmon|
        lightseagreen|lightskyblue|lightslategray|lightslategrey|lightsteelblue|
        lightyellow|lime|limegreen|linen|magenta|maroon|mediumaquamarine|mediumblue|
        mediumorchid|mediumpurple|mediumseagreen|mediumslateblue|mediumspringgreen|
        mediumturquoise|mediumvioletred|midnightblue|mintcream|mistyrose|moccasin|
        navajowhite|navy|oldlace|olive|olivedrab|orange|orangered|orchid|
        palegoldenrod|palegreen|paleturquoise|palevioletred|papayawhip|peachpuff|
        peru|pink|plum|powderblue|purple|red|rosybrown|royalblue|saddlebrown|salmon|
        sandybrown|seagreen|seashell|sienna|silver|skyblue|slateblue|slategray|
        slategrey|snow|springgreen|steelblue|tan|teal|thistle|tomato|turquoise|violet|
        wheat|white|whitesmoke|yellow|yellowgreen
<ColorName> ::= <ColorNameGoogle>|<ColorNameWeb>
<ColorValue> ::= <ColorName>|<ColorHex>
```
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<DriveFileRevisionID> ::= <String>
<DriveFolderID> ::= <String>
<DriveFolderName> ::= <String>
<DriveFolderNameList> ::= "<DriveFolderName>(,<DriveFolderName>)*"
<DriveFolderPath> ::= <String>(/<String>)*
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<SheetEntity> ::= <String>|id:<Number>
<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<FileFormat> ::=
        csv|doc|dot|docx|dotx|epub|html|jpeg|jpg|json|mht|odp|ods|odt|
        pdf|png|ppt|pot|potx|pptx|rtf|svg|tsv|txt|xls|xlt|xlsx|xltx|zip|
        ms|microsoft|openoffice|
<FileFormatList> ::= "<FileFormat>(,<FileFormat)*"

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
        gsheet|gspreadsheet|
        gshortcut|
        g3pshortcut|
        gsite|
        

<MimeTypeName> ::= application|audio|font|image|message|model|multipart|text|video

<MimeType> ::= <MimeTypeShortcut>|(<MimeTypeName>/<String>)
```
```
<DriveFileAttribute> ::=
        (contentrestrictions (readonly false)|(readonly true [reason <String>]) [ownerrestricted [<Boolean>]])|
        (copyrequireswriterpermission [<Boolean>])|
        (description <String>)|
        (folderColorRgb <ColorValue>)|
        (indexabletext <String>)|
        (inheritedpermissionsdisabled [<Boolean>])|
        (keeprevisionforever|pinned)|
        (lastviewedbyme <Time>)|
        (mimetype <MimeType>)|
        (ocrlanguage <Language>)|
        (preservefiletimes [<Boolean>])|
        (privateproperty <PropertyKey> <PropertyValue>)|
        (publicproperty <PropertyKey> <PropertyValue>)|
        (property <PropertyKey> <PropertyValue> [private|public])|
        (restricted|restrict [<Boolean>])|
        (securityupdate [<Boolean>])|
        (shortcut <DriveFileID>)|
        (starred|star [<Boolean>])|
        (trashed|trash [<Boolean>])|
        (viewed|view [<Boolean>])|
        (viewerscancopycontent [<Boolean>])|
        (writerscanshare|writerscantshare [<Boolean>])

<DriveFileParentAttribute> ::=
        (parentid <DriveFolderID>)|
        (parentname <DriveFolderName>)|
        (anyownerparentname <DriveFolderName>)|
        (teamdriveparentid <DriveFolderID>)|
        (teamdriveparent <SharedDriveName>)|
        (teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>)|
        (teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>)

<DriveFileCreateAttribute> ::=
        <DriveFileAttribute>|
        <DriveFileParentAttribute>|
        (createddate|createdtime <Time>)|
        (modifieddate|modifiedtime <Time>)|
        ignoredefaultvisibility|
        usecontentasindexabletext

<DriveFileUpdateAttribute> ::=
        <DriveFileAttribute>|
        <DriveFileParentAttribute>|
        (modifieddate|modifiedtime <Time>)|
        usecontentasindexabletext|
        ((addparents <DriveFolderIDList>)|
         (addparentname <DriveFolderName>)|
         (addanyownerparentname <DriveFolderName>))|
        ((removeparents <DriveFolderIDList>)|
         (removeparentname <DriveFolderName>)|
         (removeanyownerparentname <DriveFolderName>))
```
## Create files
```
gam <UserTypeEntity> create|add drivefile
        [(localfile <FileName>|-)|(url <URL>)]
        [(drivefilename|newfilename <DriveFileName>) | (replacefilename <REMatchPattern> <RESubstitution>)*]
        [stripnameprefix <String>] [noduplicate]
        [timestamp [<Boolean>]] [timeformat <String>]
        <DriveFileCreateAttribute>*
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) |
         (returnidonly|returnlinkonly|returneditlinkonly|showdetails)]
```
By default, an empty file is created.

To upload content to the file use:
* `localfile <FileName>` - Upload content from `<FileName>`
* `localfile -` - Upload content from stdin
* `url <URL>` - Upload content downloaded from `<URL>`

You can specify where the new file is to be located:
* `parentid <DriveFolderID>` - Folder ID.
* `parentname <DriveFolderName>` - Folder name; the folder must be owned by `<UserTypeEntity>`.
* `anyownerparentname <DriveFolderName>` - Folder name; the folder can be owned by any user, `<UserTypeEntity>` must be able to write to the folder.
* `teamdriveparentid <DriveFolderID>` - Shared Drive folder ID; when used alone, this indicates a specfic Shared Drive folder.
* `teamdriveparent <SharedDriveName>` - Shared Drive name; when used alone, this indicates the root level of the Shared Drive.
* `teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>` - A Shared Drive ID and a folder name  on that Shared Drive.
* `teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>` - A Shared Drive name and a folder name on that Shared Drive.
* If none of the parent options are specified, the parent folder is the root folder.

By default, Google assigns the current time to the attributes `createdTime` and `modifiedTime`; you can assign your own values
with `createdtime <Time>` and `modifiedtime <Time>`.

The option `preservefiletimes`, when used with `localfile <FileName>`, will set the `createdTime` and `modifiedTime` attributes from the local file.

On some Linux systems getting the createdtime is problematic.
* See: https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python/39501288#39501288

These are the naming rules:
* `create drivefile localfile "LocalFile.csv"` - Google Drive file is named "LocalFile.csv"
* `create drivefile drivefilename "GoogleFile.csv" localfile "LocalFile.csv"` - Google Drive file is named "GoogleFile.csv"

If `stripnameprefix <String>` is specified, `<String>` will be stripped from the front of the Google Drive file name if present.

You can add a timestamp to the FileName.
* `tdtimestamp` - Should a timestamp (of the time the file is uploaded to Google) be added to the title of the uploaded file.
* `tdtimeformat` - Format of the timestamp added to the title of the uploaded file; if not specified, an ISO format timestamp is added.
  * See: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior

If `noduplicate` is specfied, GAM will issue a warning and not perform the create if a non-trashed item with the same name (regardless of MIME type)
exists in the parent folder.

By default, when files are uploaded from local content, they are created with `binary` format, i.e., the data is uploaded
without any conversion. Legacy GAM had an option `convert` that was passed to the Drive API v2 that it used.
* convert - Whether to convert this file to the corresponding Docs Editors format

Advanced GAM uses Drive API v3 that doesn't support the `convert` option; it uses the `mimetype` argument to cause conversions.
* `mimetype gdoc` - Convert the uploaded content to a Google Doc; e.g., convert a Word (.docx) or text (.txt) file to a Google Doc
* `mimetype gsheet` - Convert the uploaded content to a Google Sheet; e.g., convert an Excel (.xlsx) or CSV (.csv) file to a Google Sheet
* `mimetype gpresentation` - Convert the uploaded content to a Google Slides; e.g., convert a PowerPoint (.pptx) file to a Google Slides

By default, the user, file name and id values are displayed on stdout.
* `returnidonly` - Display just the file ID of the created file on stdout
* `returnlinkonly` - Display just the file webViewLink of the created file on stdout
* `returneditlinkonly` - Display just the file editLink of the created file on stdout
* `showdetails` - Add the parent folder ID and MIME type to the output

Alternatively, you can direct the output to a CSV file:
* `csv [todrive <ToDriveAttribute>*]` - Write user, file name and id values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

To retrieve the file ID with `returnidonly`:
```
Linux/MacOS
fileId=$(gam user user@domain.com create drivefile ... returnidonly)
Windows PowerShell
$fileId = & gam user user@domain.com create drivefile ... returnidonly
```
The file ID will only be valid when the return code of the command is 0; program accordingly.

## Create folders

Google Drive folders to GAM are just like files, with the MimeType for a folder. To create a folder `FooFolder` in the root of the Drive for user `Fred`:

```
gam user Fred@yourdomain.com create drivefile drivefilename FooFolder mimetype gfolder
```

The same, but created in the existing folder `BarFolder`:

```
gam user Fred@yourdomain.com create drivefile drivefilename FooFolder mimetype gfolder parentname BarFolder
```

This only works if the folder name for the parent is unique. An alternative is to use the folder ID:

```
gam user Fred@yourdomain.com create drivefile drivefilename FooFolder mimetype gfolder parentid <FolderID>
```

## Bulk Create Files and Folders
Make a CSV file FileNames.csv with at least two columns, primaryEmail and Name.
```
Files
gam redirect csv ./FileNamesIDs.csv multiprocess [todrive <ToDriveAttribute>*] csv FileNames.csv gam user "~primaryEmail" create drivefile drivefilename "~Name" csv [other options as desired]

Folders
gam redirect csv ./FileNamesIDs.csv multiprocess [todrive <ToDriveAttribute>*] csv FileNames.csv gam user "~primaryEmail" create drivefile drivefilename "~Name" csv mimetype gfolder [other options as desired]

Add a column mimetype to create files and folders
gam redirect csv ./FileNamesIDs.csv multiprocess [todrive <ToDriveAttribute>*] csv FileNames.csv gam user "~primaryEmail" create drivefile drivefilename "~Name" csv mimetype "~mimetype" [other options as desired]
```
This will create a three column CSV file SharedDriveNamesIDs.csv with columns: User,name,id
* There will be a row for each file/folder.

## Bulk Create Student Folders on a Shared Drive
You are building student folders on a Shared Drive as an admin and want to add ACLs to the folders
allowing the student write access and you want a shortcut on the student's My Drive pointing to the folder.
By adding the student's primary email address to the CSV output, it can be used in subsequent commands.
Sustitute for admin@domain.com and `<TeamDriveID>`.
```
Students.csv
primaryEmail,Name
bob@domain.com,Bob Jones
mary@domain.com, Mary Smith
...

# Create the student folders on the Shared Drive
gam redirect csv ./StudentFolders.csv multiprocess csv Students.csv gam user admin@domain.com create drivefile mimetype gfolder drivefilename "~~Name~~ Digital Portfolio" parentid <TeamDriveID> csv addcsvdata primaryEmail "~primaryEmail"
# Add ACLs granting the students write access to their folders; "~User" refers to admin@domain.com
gam csv StudentFolders.csv gam user "~User" add drivefileacl "~id" user "~primaryEmail" role fileorganizer
# Add a shortcut to the folder on the student's My Drive
gam csv StudentFolders.csv gam user "~primaryEmail" create drivefileshortcut "~id" parentid root
```

## Create folder hierarchy
Starting at the specified parent folder, GAM steps through the hierarchy of folder names;
if a folder with that name already exists within the parent folder, is owned by the user and is not in the trash, it is used,
otherwise a new folder is created within the parent folder.
```
gam <UserTypeEntity> create|add drivefolderpath
        [pathdelimiter <Character>]
        ((fullpath <DriveFolderPath) |
         (path <DriveFolderPath> [<DriveFileParentAttribute>]) |
         (list <DriveFolderNameList> [<DriveFileParentAttribute>]))
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) |
         returnidonly]
```

`pathdelimiter` defaults to `/`; if some folder name in `fullpath` or `path` contains a `/`, you can use
`pathdelimiter <Character>` to specify a character that does not appear in the folder names to delimit
components of the path.

You must specify the folder hiearchy with one of the following options:
* `fullpath "My Drive/<DriveFolderPath>"` - Build path in root of My Drive
* `fullpath "SharedDrives/<SharedDriveName>/<DriveFolderPath>"` - Build path in root of Shared Drive `<SharedDriveName>`
* `path "<DriveFolderPath>" [<DriveFileParentAttribute>]` - Build path in location specified by `<DriveFileParentAttribute>`; if omitted, `My Drive` is used
* `list "<DriveFolderNameList>" [<DriveFileParentAttribute>]` - Use if a folder name contains a `/`. Build path in location specified by `<DriveFileParentAttribute>`; if omitted, `My Drive` is used

By default, the user, folder names and id values are displayed on stdout.
* `returnidonly` - Display just the folder ID of the last folder on stdout

Alternatively, you can direct the output to a CSV file:
* `csv [todrive <ToDriveAttribute>*]` - Write user, folder name and id values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

### Examples
Specify path, parent is My Drive
```
gam user user@domain.com create drivefolderpath path "Top Folder/Middle Folder/Bottom Folder" 
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top Folder(1-4Nr7oF0wAdOw2tjbDMV1bZ003h5Poqq), Created (1/3)
  User: user@domain.com, Drive Folder Name: Middle Folder(1z3oOPd44XdEJgUnwCi7d60zBh8J_BkVk), Created (2/3)
  User: user@domain.com, Drive Folder Name: Bottom Folder(1C6vwyIaq8sSG9-NSFXCPSBJyY6TccQKS), Created (3/3)
```
Add an additional folder to the path
```
gam user user@domain.com create drivefolderpath path "Top Folder/Middle Folder/Bottom Folder/Sub Folder"
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top Folder(1-4Nr7oF0wAdOw2tjbDMV1bZ003h5Poqq), Exists (1/4)
  User: user@domain.com, Drive Folder Name: Middle Folder(1z3oOPd44XdEJgUnwCi7d60zBh8J_BkVk), Exists (2/4)
  User: user@domain.com, Drive Folder Name: Bottom Folder(1C6vwyIaq8sSG9-NSFXCPSBJyY6TccQKS), Exists (3/4)
  User: user@domain.com, Drive Folder Name: Sub Folder(1xo6ZOe1Gk4IYKway4aeuznBQUhrixMqO), Created (4/4)
```
Specify path, parent is folder named "Folder Tree"
```
gam user user@domain.com create drivefolderpath path "Top Folder/Middle Folder/Bottom Folder" parentname "Folder Tree"
Getting all Drive Files/Folders that match query ('me' in owners and mimeType = 'application/vnd.google-apps.folder' and name = 'Folder Tree' and trashed = false) for user@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and mimeType = 'application/vnd.google-apps.folder' and name = 'Folder Tree' and trashed = false) for user@domain.com...
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top Folder(1YS6pDXupOTN5TzvOprgSbXj9Gp10z4vK), Created (1/3)
  User: user@domain.com, Drive Folder Name: Middle Folder(1m6A3a9w0DCkwtjqF0heIwLyQTHI1TIk1), Created (2/3)
  User: user@domain.com, Drive Folder Name: Bottom Folder(1sfC-QPtMg_W1ZpOKL5URylugd0x_nxRt), Created (3/3)

gam user user@domain.com show filetree select drivefilename "Folder Tree" fields id
Getting all Drive Files/Folders that match query ('me' in owners and name = 'Folder Tree') for user@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'Folder Tree') for user@domain.com...
User: user@domain.com, Show 1 Drive File/Folder
  Folder Tree: (id: 19-0hkpwj-FKaeQ1B7prozNVQU0PD588b)
    Top Folder: (id: 1YS6pDXupOTN5TzvOprgSbXj9Gp10z4vK)
      Middle Folder: (id: 1m6A3a9w0DCkwtjqF0heIwLyQTHI1TIk1)
        Bottom Folder: (id: 1sfC-QPtMg_W1ZpOKL5URylugd0x_nxRt
```
	
Build in root of a Shared Drive
```
gam user user@domain.com create drivefolderpath fullpath "SharedDrives/TS Shared Drive/Top Folder/Middle Folder/Bottom Folder/Sub Folder"
Getting all Drive Files/Folders that match query (mimeType = 'application/vnd.google-apps.folder' and name = 'TS SD6 Folder' and trashed = false) for user@domain.com
Got 1 Drive File/Folder that matched query (mimeType = 'application/vnd.google-apps.folder' and name = 'TS SD6 Folder' and trashed = false) for user@domain.com...
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top Folder(1QSJY0CZCz_M8veZPaEqi_zbSjQFfSXDl), Created (1/4)
  User: user@domain.com, Drive Folder Name: Middle Folder(1JdTD6_5vAEiB1Rnn-fpc12zmjIOu81Aa), Created (2/4)
  User: user@domain.com, Drive Folder Name: Bottom Folder(1lBLgr9umxZ9JM-vZ7QeuPU2b0tR1o8AL), Created (3/4)
  User: user@domain.com, Drive Folder Name: Sub Folder(1-F733sDRWG_lktQr7dyppKdjAw6fAcf7), Created (4/4)
```

Build in a Shared Drive Folder
```
gam user user@domain.com create drivefolderpath path "Top Folder/Middle Folder/Bottom Folder/Sub Folder" teamdriveparent "TS Shared Drive" teamdriveparentname "TS SD6 Folder"
Getting all Drive Files/Folders that match query (mimeType = 'application/vnd.google-apps.folder' and name = 'TS SD6 Folder' and trashed = false) for user@domain.com
Got 1 Drive File/Folder that matched query (mimeType = 'application/vnd.google-apps.folder' and name = 'TS SD6 Folder' and trashed = false) for user@domain.com...
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top Folder(1QSJY0CZCz_M8veZPaEqi_zbSjQFfSXDl), Created (1/4)
  User: user@domain.com, Drive Folder Name: Middle Folder(1JdTD6_5vAEiB1Rnn-fpc12zmjIOu81Aa), Created (2/4)
  User: user@domain.com, Drive Folder Name: Bottom Folder(1lBLgr9umxZ9JM-vZ7QeuPU2b0tR1o8AL), Created (3/4)
  User: user@domain.com, Drive Folder Name: Sub Folder(1-F733sDRWG_lktQr7dyppKdjAw6fAcf7), Created (4/4)
```

Specify list because folder names contain `/`, parent is folder named "Slash Folders"
```
gam user user@domain.com create drivefolderpath list "'Top/Folder','Middle/Folder','Bottom/Folder'" parentname "Slash Folders"
Getting all Drive Files/Folders that match query ('me' in owners and mimeType = 'application/vnd.google-apps.folder' and name = 'Slash Folders' and trashed = false) for user@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and mimeType = 'application/vnd.google-apps.folder' and name = 'Slash Folders' and trashed = false) for user@domain.com...
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top/Folder(1j9gZX6fwbHEjN0GFAFVzuhbG2G9qUOzZ), Created (1/3)
  User: user@domain.com, Drive Folder Name: Middle/Folder(1tYGwL1cYE29trboqoT6utfrnG-fbN7-4), Created (2/3)
  User: user@domain.com, Drive Folder Name: Bottom/Folder(1HpJ4DU178j4KRai3mIRbndGP5t9ptYye), Created (3/3)

gam user user@domain.com show filetree select drivefilename "Slash Folders" fields id
Getting all Drive Files/Folders that match query ('me' in owners and name = 'Slash Folders') for user@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'Slash Folders') for user@domain.com...
User: user@domain.com, Show 1 Drive File/Folder
  Slash Folders: (id: 1kZN9W60ZeRQMTqM4tqnnBniz5AmzmE0x)
    Top/Folder: (id: 1j9gZX6fwbHEjN0GFAFVzuhbG2G9qUOzZ)
      Middle/Folder: (id: 1tYGwL1cYE29trboqoT6utfrnG-fbN7-4)
        Bottom/Folder: (id: 1HpJ4DU178j4KRai3mIRbndGP5t9ptYye)
```

Specify `pathdelimiter "|"` because folder names contain `/`, parent is folder named "Slash Folders"
```
gam user user@domain.com create drivefolderpath pathdelimiter "|" path "Top/Folder|Middle/Folder|Bottom/Folder'" parentname "Slash Folders"
Getting all Drive Files/Folders that match query ('me' in owners and mimeType = 'application/vnd.google-apps.folder' and name = 'Slash Folders' and trashed = false) for user@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and mimeType = 'application/vnd.google-apps.folder' and name = 'Slash Folders' and trashed = false) for user@domain.com...
User: user@domain.com, Drive Folder Path:, Create
  User: user@domain.com, Drive Folder Name: Top/Folder(1j9gZX6fwbHEjN0GFAFVzuhbG2G9qUOzZ), Created (1/3)
  User: user@domain.com, Drive Folder Name: Middle/Folder(1tYGwL1cYE29trboqoT6utfrnG-fbN7-4), Created (2/3)
  User: user@domain.com, Drive Folder Name: Bottom/Folder(1HpJ4DU178j4KRai3mIRbndGP5t9ptYye), Created (3/3)

gam user user@domain.com show filetree select drivefilename "Slash Folders" fields id
Getting all Drive Files/Folders that match query ('me' in owners and name = 'Slash Folders') for user@domain.com
Got 1 Drive File/Folder that matched query ('me' in owners and name = 'Slash Folders') for user@domain.com...
User: user@domain.com, Show 1 Drive File/Folder
  Slash Folders: (id: 1kZN9W60ZeRQMTqM4tqnnBniz5AmzmE0x)
    Top/Folder: (id: 1j9gZX6fwbHEjN0GFAFVzuhbG2G9qUOzZ)
      Middle/Folder: (id: 1tYGwL1cYE29trboqoT6utfrnG-fbN7-4)
        Bottom/Folder: (id: 1HpJ4DU178j4KRai3mIRbndGP5t9ptYye)
```


## Bulk Create folder hierarchies
Make a CSV file FolderPaths.csv containing the folder hierarchies.
```
path
A/B1/C
A/B2/C
A/B3/C
B/A1
B/A2
B/A3
C/D1/A
C/D1/B
C/D2/A
C/D2/B
```

You can't use `gam csv` as the parallel processes will interfere with each other; you must use `gam loop` for serial processing.
```
gam loop FolderPaths.csv gam user user@domain.com create drivefolderpath path "~path"
```

To create the hierarchies for multiple users, make a batch file FolderPaths.bat that contains a line for each user.
```
gam loop FolderPaths.csv gam user user1@domain.com create drivefolderpath path "~path"
gam loop FolderPaths.csv gam user user2@domain.com create drivefolderpath path "~path"
...
```

Execute the batch file.
```
gam redirect stdout CreateFolderPaths.txt multiprocess redirect stderr stdout batch FolderPaths.bat
```

## Update files
```
gam <UserTypeEntity> update drivefile <DriveFileEntity> [copy] [returnidonly|returnlinkonly]
        [(localfile <FileName>|-)|(url <URL>)]
        [retainname | (newfilename <DriveFileName>) | (replacefilename <REMatchPattern> <RESubstitution>)*]
        [stripnameprefix <String>]
        [timestamp [<Boolean>]] [timeformat <String>]
        <DriveFileUpdateAttribute>*
        [(gsheet|csvsheet <SheetEntity> [clearfilter])|(addsheet <String>)]
        [charset <Charset>] [columndelimiter <Character>]
```
By default, an existing file's attributes are updated.

To upload content to the file use:
* `localfile <FileName>` - Upload content from `<FileName>`
* `localfile -` - Upload content from stdin
* `url <URL>` - Upload content downloaded from `<URL>`

You can change where the new file is to be located; this removes all other parent folders:
* `parentid <DriveFolderID>` - Folder ID.
* `parentname <DriveFolderName>` - Folder name; the folder must be owned by `<UserTypeEntity>`.
* `anyownerparentname <DriveFolderName>` - Folder name; the folder can be owned by any user, `<UserTypeEntity>` must be able to write to the folder.
* `teamdriveparentid <DriveFolderID>` - Shared Drive folder ID; when used alone, this indicates a specfic Shared Drive folder.
* `teamdriveparent <SharedDriveName>` - Shared Drive name; when used alone, this indicates the root level of the Shared Drive.
* `teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>` - A Shared Drive ID and a folder name  on that Shared Drive.
* `teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>` - A Shared Drive name and a folder name on that Shared Drive.

You can add/remove parent folders without affecting other parent folders.
* `addparents|removeparents <DriveFolderIDList>` - Specify the parent folders by ID.
* `addparentname|removeparentname <DriveFolderName>` - Perform the query: `"'me' in owners and name='<DriveFolderName>'"` to convert `<DriveFolderName>` to its `<DriveFolderID>`.
* `addanyownerparentname|removeanyownerparentname <DriveFolderName>` - Perform the query: `"name='<DriveFolderName>'"` to convert `<DriveFolderName>` to its `<DriveFolderID>`.

From the Google Drive API documentation.
  * If the item's owner makes a request to add a single parent, the item is removed from all current folders and placed in the requested folder.
  * Other requests that increase the number of parents fail, except when the canAddMyDriveParent file capability is true and a single parent is being added. 

By default, Google assigns the current time to the attribute `modifiedTime`; you can assign your own value
with `modifiedtime <Time>`.

* `preservefiletimes localfile <FileName>` - `modifiedTime` of `<DriveFileEntity>` is set to that of `localfile <FileName>`
* `preservefiletimes` - `modifiedTime` of `<DriveFileEntity>` retains its current value

These are the naming rules when updating from a local file:
* `update drivefile drivefilename "GoogleFile.csv" localfile "NewLocalFile.csv"` - Google Drive file "GoogleFile.csv" is renamed "NewLocalFile.csv"
* `update drivefile drivefilename "GoogleFile.csv" newfilename "NewGoogleFile.csv" localfile "NewLocalFile.csv"` - Google Drive file "GoogleFile.csv" is renamed "NewGoogleFile.csv"
* `update drivefile drivefilename "GoogleFile.csv" retainname localfile "NewLocalFile.csv"` - Google Drive file "GoogleFile.csv" is not renamed

To simply rename a file, use `newfilename <String>`:
* `update drivefile drivefilename "GoogleFile.csv" newfilename "NewGoogleFile.csv"` - Google Drive file "GoogleFile.csv" is renamed "NewGoogleFile.csv"

For more complex renaming, use `replacefilename <REMatchPattern> <RESubstitution>`:
* `update drivefile drivefilename "GoogleFile.csv" replacefilename "Google" "Boggle"` - Google Drive file "GoogleFile.csv" is renamed "BoggleFile.csv"
* `update drivefile drivefilename "GoogleFile.csv" replacefilename "^(.+)$" "New\1"` - Google Drive file "GoogleFile.csv" is renamed "NewGoogleFile.csv"

If `retainname` is not specified and `stripnameprefix <String>` is specified, `<String>` will be stripped from the front of the Google Drive file name if present.

You can add a timestamp to the FileName.
* `tdtimestamp` - Should a timestamp (of the time the file is uploaded to Google) be added to the title of the uploaded file.
* `tdtimeformat` - Format of the timestamp added to the title of the uploaded file; if not specified, an ISO format timestamp is added.
  * See: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior

You can update a specific sheet within a Google spreadsheet or add a new sheet to the spreadsheet
* `gsheet|csvsheet <String>` - Specify a sheet by name in a Google Sheets file to be updated
* `gsheet|csvsheet id:<Number>` - Specify a sheet by ID in a Google Sheets file to be updated
  * `clearfilter` - When updating a sheet, this option causes GAM to clear the spreadsheet basic filter so hidden data will be overwritten
* `addsheet <String>` - Specify a sheet name to be added to the Google Sheets file
* `charset <Charset>` - Specify the character set of the local file; if not specified, the value of `charset` from `gam.cfg` will be used
* `columndelimiter <Character>` - Columns are separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used

If you want the Google spreadsheet to retain its name, specify: `retainname localfile LocalFile.csv`.

By default, the user, file name, updated file name and id values are displayed on stdout.
* `returnidonly` - Display just the file ID of the updated file on stdout
* `returnlinkonly` - Display just the file webViewLink of the updated file on stdout

To retrieve the file ID with `returnidonly`:
```
Linux/MacOS
fileId=$(gam user user@domain.com update drivefile <DriveFileEntity> copy ... returnidonly)
Windows PowerShell
$fileId = & gam user user@domain.com update drivefile <DriveFileEntity> copy ... returnidonly
```
The file ID will only be valid when the return code of the command is 0; program accordingly.

By default, a file or folder is updated. Use the `copy` option to copy a file or folder.

## Download files

```
gam <UserTypeEntity> get drivefile <DriveFileEntity> [revision <DriveFileRevisionID>]
        [(format <FileFormatList>)|(gsheet|csvsheet <SheetEntity>)] [exportsheetaspdf <String>]
        [targetfolder <FilePath>] [targetname <FileName>|-]
        [donotfollowshortcuts [<Boolean>]] [overwrite [<Boolean>]] [showprogress [<Boolean>]]
        [acknowledgeabuse [<Boolean>]]
```
By default, Google Docs/Sheets/Slides are converted to Open Office format when downloaded. If you want a
different format for these files or are downloading a different type of file, you must specify the format.
* `format <FileFormatList>` - Specify a list of formats, the downloaded file will be converted to the first applicable format
* `gsheet|csvsheet <String>` - Specify a sheet by name in a Google Sheets file to be downloaded in the specified format from above or CSV by default
* `gsheet|csvsheet id:<Number>` - Specify a sheet by ID in a Google Sheets file to be downloaded in the specified format from above or CSV by default

You can download Google Sheets into PDF files; `exportsheetaspdf <String>` specifies formatting options.
* All sheets will be downloaded, use `gsheet|csvsheet <String>|id:<Number>` to download a specific sheet
* Page order: &pageorder=1|2
    * 1 = Down, then over
    * 2 = Over, then down
* Paper size: &size=A3|A4|A5|B4|B5|letter|tabloid|legal|statement|executive|folio
* Scale: &scale=1|2|3|4
    * 1 = Normal 100%
    * 2 = Fit to width
    * 3 = Fit to height
    * 4 = Fit to Page
* Orientation: &portrait=true|false
    * false = landscape
* Fit to width: &fitw=true|false
    * false = actual size
* Horizontal alignment: &horizontal_alignment=LEFT|RIGHT|CENTER
* Vertical alignment: &vertical_alignment=TOP|MIDDLE|BOTTOM
* Top margin: &top_margin=0.00
    * All four margins must be set
* Bottom margin: &bottom_margin=0.00
* Left margin: &left_margin=0.00
* Right margin: &right_margin=0.00
* Print sheet names: &sheetnames=true|false
* Print notes: &printnotes=true|false
* Print title: &printtitle=true|false
* Print page numbers: &pagenum=CENTER|UNDEFINED
    * CENTER = include page numbers, but they always seem to be in the bottom right
    * UNDEFINED = do not include page numbera
* Print gridlines: &gridlines=true|false
* Frozen columns: &fzc=true|false
* Frozen rows: &fzr=true|false
* Range: &r1=0&c1=0&r2=1&c2=1
    * Rows and columns are numbered from 0
    * r1 - top row
    * c1 - left column
    * r2 - bottom row + 1
    * c2 - right column +1
If you make a mistake in `exportsheetaspdf <String>`, the download will fail with HTTP error 400 or 500.

By default, when getting a drivefile, it is downloaded to the directory specified in `gam.cfg/drive_dir`.
* `targetfolder <FilePath>` - Specify an alternate location for the downloaded file.

By default, when getting a drivefile, the local name is the same as the Google Drive name.
* `targetname <FileName>` - Specify an alternate name for the downloaded file.
* `targetname -` - The drivefile will be written to stdout

The strings `#email#`, `#user#` and `#username#` will be replaced by the the user's full emailaddress or just the name portion
in `targetfolder <FilePath>` and `targetname <FileName>`.

Shortcuts can not be downloaded so, by default, if `<DriveFileEntity>` is a shortcut, GAM follows the shortcut and downloads the referenced file.
If you do not want this behavior and want GAM to report an error, use the option `donotfollowshortcuts`.

By default, when getting a drivefile, an existing local file will not be overwritten; a numeric prefix is added to the filename.
* `overwrite` - Overwite an existing file
* `overwrite true` - Overwite an existing file
* `overwrite false` - Do not overwite an existing file; add a numeric prefix and create a new file

When getting a drivefile, you can show download progress information with the `showprogress` option.
* `showprogress` - Show download progress information
* `showprogress true` - Show download progress information
* `showprogress false` - Do not show download progress information

You may get the following error from Google when trying to download a file:
```
Download Failed: This file has been identified as malware or spam and cannot be downloaded.
```
Use the `acknowledgeabuse` option to control downloading the file.
* `acknowledgeabuse` - Download the file; `the user is acknowledging the risk of downloading known malware or other abusive files`
* `acknowledgeabuse true` - Download the file; `the user is acknowledging the risk of downloading known malware or other abusive files`
* `acknowledgeabuse false` - Do not download the file; this is the default

### Example: Download a CSV file and execute a Gam command on its contents
Suppose you have a Google Sheets file UserSheet with multiple sheets, one of which is named NewUsers; it has a column labelled primaryEmail.

The following command will download the sheet and show the name for each user in the column.
```
gam user user@domain.com get drivefile drivefilename UserSheet csvsheet NewUsers targetname - | gam redirect stdout - multiprocess csv - gam info user "~primaryEmail" name nogroups nolicenses
```
* The `redirect stdout - multiprocess` option produces clean output from the multiple processes

## Trash files
Move a file or folder to the trash. If a folder is moved to the trash, all of its child files and folders are moved to the trash.
```
gam <UserTypeEntity> trash drivefile <DriveFileEntity> [shortcutandtarget [<Boolean>]]
gam <UserTypeEntity> delete|del drivefile <DriveFileEntity> trash [shortcutandtarget [<Boolean>]]
```

Starting in version 6.80.10, the  option `shortcutandtarget [<Boolean>]` that when true and `<DriveFileEntity` is a shortcut,
causes GAM to process the shortcut and the target of the shortcut.

## Untrash files
Remove a file or folder from the trash. If a folder is removed from the trash, all of its child files and folders are removed from the trash.
```
gam <UserTypeEntity> untrash drivefile <DriveFileEntity> [shortcutandtarget [<Boolean>]]
gam <UserTypeEntity> delete|del drivefile <DriveFileEntity> untrash [shortcutandtarget [<Boolean>]]
```

Starting in version 6.80.10, the  option `shortcutandtarget [<Boolean>]` that when true and `<DriveFileEntity` is a shortcut,
causes GAM to process the shortcut and the target of the shortcut.

## Purge files
Purging a file permanently deletes it; it can not be recovered. If a folder is purged, all of its child files and folders are purged.
```
gam <UserTypeEntity> purge drivefile <DriveFileEntity> [shortcutandtarget [<Boolean>]]
gam <UserTypeEntity> delete|del drivefile <DriveFileEntity> purge [shortcutandtarget [<Boolean>]]
```

Starting in version 6.80.10, the  option `shortcutandtarget [<Boolean>]` that when true and `<DriveFileEntity` is a shortcut,
causes GAM to process the shortcut and the target of the shortcut.

## Download Google Documents as JSON
```
gam <UserTypeEntity> get document <DriveFileEntity>
        [viewmode default|suggestions_inline|preview_suggestions_accepted|preview_without_suggestions]
        [targetfolder <FilePath>] [targetname <FileName>]
        [donotfollowshortcuts [<Boolean>]] [overwrite [<Boolean>]]
```
By default, when getting a document, it is downloaded to the directory specified in `gam.cfg/drive_dir`.
* `targetfolder <FilePath>` - Specify an alternate location for the downloaded document.

By default, when getting a document, the local name is the same as the Google Document name.
* `targetname <FileName>` - Specify an alternate name for the downloaded file.

The strings `#email#`, `#user#` and `#username#` will be replaced by the the user's full emailaddress or just the name portion
in `targetfolder <FilePath>` and `targetname <FileName>`.

Shortcuts can not be downloaded so, by default, if `<DriveFileEntity>` is a shortcut, GAM follows the shortcut and downloads the referenced file.
If you do not want this behavior and want GAM to report an error, use the option `donotfollowshortcuts`.

By default, when getting a document, an existing local file will not be overwritten; a numeric prefix is added to the filename.
* `overwrite` - Overwite an existing file
* `overwrite true` - Overwite an existing file
* `overwrite false` - Do not overwite an existing file; add a numeric prefix and create a new file

## Upload changes to Google Documents

```
<DocumentJSONUpdateRequest> ::=
        '{"requests": [{object (Request)}], "writeControl": {object (WriteControl) }`
See: https://developers.google.com/docs/api/reference/rest/v1/documents/request

gam <UserTypeEntity> update document <DriveFileEntity>
        ((json [charset <Charset>] <DocumentJSONUpdateRequest>) |
         (json file <FileName> [charset <Charset>]))
        [formatjson]
```
The JSON data can be read from a command line argument or a file. On the command line, the
JSON data is enclosed in single quotes; these should not be present when the JSON data is read from a file.

The output is formatted for human readability. Use the following option to produce JSON output for program parsing.
* `formatjson` - Display output in JSON format.

### Examples
Replace Foo with Goo in a document.
```
File Update.json contains:
{ "requests": [{"replaceAllText": {"replaceText": "Goo", "containsText": {"text": "Foo", "matchCase": "True"}}}]}


gam user testuser@domain.com update document <DriveFileItem> json file Update.json
```
## Download and Upload Google Apps Scripts
```
$ gam user user1@domain.com get drivefile 1ZY-YkS3E0OKipALra_XzfIh9cvxoILSbb8TRdHBFCpyB_mXI_J8FmjHv format json
User: user1@domain.com, Download 1 Drive File
  User: user1@domain.com, Drive File: Test Project, Downloaded to: /Users/gamteam/GamWork/Test Project.json, Type: Google Doc
$ gam user user2@domain.com create drivefile localfile "Test Project.json" mimetype application/vnd.google-apps.script+json drivefilename "Test Project"
User: user2@domain.com, Drive File: Test Project(1Ok_svw55VTreZ5CzcViJDLfEzVRi-Un8D9eG6I5pIeVyRl2YsmNiy3C_), Created with content from: Test Project.json
```
