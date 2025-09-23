- [Managing Google Drive Files and Folders for users](#managing-google-drive-files-and-folders-for-users)
  - [Printing User Drive Files to a CSV](#printing-user-drive-files-to-a-csv)
  - [Creating and Uploading Drive Files for Users](#creating-and-uploading-drive-files-for-users)
  - [Updating Drive Files for Users](#updating-drive-files-for-users)
  - [Downloading Drive Files For Users](#downloading-drive-files-for-users)
  - [Deleting Google Drive Files for Users](#deleting-google-drive-files-for-users)
  - [Show Drive File Info for Users](#show-drive-file-info-for-users)
  - [Show Drive File Revisions for Users](#show-drive-file-revisions-for-users)
  - [Empty Drive Trash for Users](#empty-drive-trash-for-users)
- [Managing Google Drive Permissions for Users](#managing-google-drive-permissions-for-users)
  - [Showing the Permissions of a File/Folder for a user](#showing-the-permissions-of-a-filefolder-for-a-user)
  - [Adding permissions to a file/folder for a user](#adding-permissions-to-a-filefolder-for-a-user)
  - [Updating permissions to a file/folder for a user](#updating-permissions-to-a-filefolder-for-a-user)
  - [Removing permissions to a file/folder for a user](#removing-permissions-to-a-filefolder-for-a-user)
- [Managing shared drives](#managing-shared-drives)
  - [Creating shared drives](#creating-shared-drives)
  - [Adding user permissions to shared drives](#adding-user-permissions-to-shared-drives)
  - [Updating shared drives](#updating-shared-drives)
  - [Deleting shared drives](#deleting-shared-drives)
  - [Showing/Printing shared drives](#showingprinting-shared-drives)

GAM now supports Google Drive Management with the ability to add, update, view and delete Drive files and folders for users as well as adding, updating, viewing and deleting file and folder permissions.

# Managing Google Drive Files and Folders for users
## Printing User Drive Files to a CSV
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show filelist [todrive] [query|fullquery <query>] [allfields]
  [createddate] [description] [fileextension] [filesize] [id] [name] [owners] [parents] [permissions] 
  [restricted] [starred] [trashed] [viewed]
  [lastmodifyingusername] [lastviewedbymedate] [modifieddate] [originalfilename] [quotaused] [shared] [writerscanshare]
```
Outputs a CSV file listing the Google Drive files/folders that the given user(s) own. By default, the output is sent to the screen and only the file owner, title and URL columns are shown. The optional `todrive` argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrator's Google Drive rather than displaying it locally. The optional `query` argument allows the results to be narrowed to files/folders matching the given query. The optional `fullquery` argument is similar to query but omits the "'me' in owners" portion of the query. The query format is described in [Google's documentation](https://developers.google.com/drive/api/v2/search-files). The optional `allfields` arguments causes all possible columns to be included in the output. The optional `createddate`, `description`, `fileextension`, `filesize`, `id`, `name`, `restricted`, `starred`, `trashed`, `viewed`, `lastmodifyingusername`, `lastviewedbymedate`, `modifieddate`, `originalfilename`, `quotaused`, `shared` and `writerscanshare` arguments cause the given columns to be included in the output.

### Example
This example displays all of Joe Schmo's files
```
gam user jschmo@acme.com show filelist
```

This example displays all files for all users that contain the text "ProjectX". The results are uploaded to a Google spreadsheet for the admin user.
```
gam all users show filelist query "fullText contains 'ProjectX'" todrive
```

This example displays all PDF files that users under the Students OU own.

```
gam ou_and_children Students show filelist query "mimeType = 'application/pdf'"
```

---

This example displays all of Joe Schmo's folders.

```
gam user jschmo@acme.com show filelist query "mimeType = 'application/vnd.google-apps.folder'"
```

---

## Creating and Uploading Drive Files for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users add drivefile [localfile <filepath>]
  [drivefilename <filename>] [convert] [ocr] [ocrlanguage <language>] [restricted] [starred] [trashed] [viewed]
  [lastviewedbyme <date>] [modifieddate <date>] [description <description>] [mimetype <type>] [parentid <folder id>]
  [parentname <folder name>] [writerscantshare]
```
Create or upload a new file to Google Drive for the given user(s). By default, the command will create a new, empty file/folder. If the optional argument localfile is specified along with the full path to a document on the local computer, GAM will upload that file's contents to Drive. The optional argument drivefilename sets the name of the file/folder in Drive. The optional argument convert causes files to be converted into native Google Docs format where possible. The optional argument ocr causes OCR analysis of images and PDF files when they are converted to native Google Docs format. The optional argument ocrlanguage determines what language is used for ocr analysis. The optional argument restricted prevents users who have reader/commenter access to a file from downloading the file content. The optional arguments starred, trashed and viewed cause the respective action to take place on the new file. The optional arguments lastviewedbyme and modifieddate set the respective timestamps for the new file, the date should follow the format YYYY-MM-DDTHH:MM:SS.000Z. For example, 2013-04-20T12:33:47.166Z. The optional argument description gives a description for the new file. The optional argument mimetype forces the given MIME file type to be used for the new file. The optional argument parentid sets a parent folder for the uploaded/created file to show underneath. The optional argument parentname searches for the given folder name to put the file under. The optional argument writerscantshare prevents users who have writer/editor access to the file from adding additional permissions to the file (only owner can add permissions).

### Examples
This example uploads the file sillycat.mp4 to Google Drive for a user
```
gam user jsmith@acme.com add drivefile localfile sillycat.mp4
```

This example creates a new folder called TPS Reports for all users and then creates a new, empty Google Doc, Spreadsheet, Presentation and Drawing under each user's folder.
```
gam all users add drivefile drivefilename "TPS Reports" mimetype gfolder
gam all users add drivefile drivefilename "TPS Doc" mimetype gdoc parentname 'TPS Reports'
gam all users add drivefile drivefilename "TPS Sheet" mimetype gsheet parentname 'TPS Reports'
gam all users add drivefile drivefilename "TPS Presentation" mimetype gpresentation parentname 'TPS Reports'
gam all users add drivefile drivefilename "TPS Drawing" mimetype gdrawing parentname 'TPS Reports'
```

This example uploads the MyRamblings.docx file to Google Drive and converts it to Google Doc native format. It also renames the file to a nicer looking "My Ramblings".
```
gam user jjones@acme.com add drivefile localfile MyRamblings.docx convert drivefilename "My Ramblings"
```

---


## Updating Drive Files for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users update drivefile [id <drive file id> | drivefilename <filename>] [localfile <filename>] [newfilename <filename>] [convert] [ocr] [ocrlanguage <language>] [restricted true|false] [starred true|false] [trashed true|false] [viewed true|false] [lastviewedbyme <date>] [modifieddate <date>] [description <description>] [mimetype <MIME type>] [parentid <folder id>] [parentname <folder name>] [writerscantshare]
```
Update a Drive file's metadata and/or content. In order to determine which file(s) are updated, either the id or drivefilename arguments must be specified. id specifies the exact unique id of the file to be updated. drivefilename performs a search for files matching the given name. The optional argument localfile specifies a local file whose content will completely replace the content of the given drive file (file id, name, etc will remain unchanged). The optional arguments convert, ocr, ocrlanguage, restricted, starred, trashed, description, mimetype and viewed specify updates that should occur to a file's metadata. The optional lastviewedbyme and modifieddate arguments specify new timestamps that should be placed on the Drive file. The date should follow the format YYYY-MM-DDTHH:MM:SS.000Z. For example, 2013-04-20T12:33:47.166Z. The optional parentid and parentname arguments specify folders under which the drive file should be placed. The optional writerscantshare argument prevents file writers/editors from sharing the file with additional users.

### Examples
This example updates the "My Ramblings" file to be starred and placed under a folder called "Brilliant things I've said" (assumes a folder by that name already exists for the user)
```
gam user bsmith@acme.com update drivefile drivefilename "My Ramblings" starred true parentname 'Brilliant things I've said'
```

This example updates the Drive file DailyReport.pdf with the contents of the local file Report-3-28-2014.pdf.
```
gam user hgregg@acme.com update drivefile drivefilename DailyReport.pdf localfile Report-3-28-2014.pdf
```

---


## Downloading Drive Files For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users get drivefile [id <file id> | query <query> | drivefilename <filename>] [format <FileFormatList>] [targetfolder <local path>] [revision <Number>]

<FileFormat> ::= csv|html|txt|tsv|jpeg|jpg|png|svg|pdf|rtf|pptx|xlsx|docx|odt|ods|openoffice|microsoft
<FileFormatList> ::= '<FileFormat>(,<FileFormat)*'
microsoft ::= docx,pptx,xlsx
openoffice ::= ods,odt

```
Download the given Drive files to the local computer. One of the `id`, `query` or `drivefilename` parameters must be specified to determine which files should be downloaded. By default, Google Docs native format files are downloaded in openoffice format. The optional argument `format` allows you to download the files in other formats by specifying a comma separated list of formats; the first format in the list that is available will be used. The optional argument `targetfolder` allows you to specify where on the local computer the downloaded files should be placed. The optional argument `revision` allows you to specify a specific revision of a file to download.

Note that drive folder hierarchy is NOT maintained when downloading files with this command.

### Examples
This example downloads the file with Drive ID adifd08 to the current path
```
gam user asmith@acme.com get drivefile id adifd08
```

This example downloads all of a user's files to c:\jsmith-files using Microsoft Office format for downloading native Google Docs.
```
gam user jsmith@acme.com get drivefile query "'me' in owners" format microsoft
```

---


## Deleting Google Drive Files for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete drivefile <file id> [purge]
```
Delete the given Drive files for user(s). The "file id" argument is the exact ID of a Google Drive file or a query to search the user's Drive for files in the format ` "query:<query>" `. By default, deleted folders are simply moved to the user's Trash folder which is purged after 30 days. The optional parameter purge causes the files to be immediately purged from the user's Google Drive so that they are no longer recoverable from Trash.

### Examples
This example moves the given Drive file to the user's Trash in Drive.
```
gam user jsmith@acme.com delete drivefile 8sidfddosa
```

This example completely purges all files from a user's Drive that are PDFs (danger Will Robinson!!!)
```
gam user jsmith@acme.com delete drivefile "query:mimeType = 'application/pdf'" purge
```
---

## Show Drive File Info for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show fileinfo <file id> [allfields]
  [createddate] [description] [fileextension] [filesize] [id] [name] [restricted] [starred] [trashed] [viewed]
  [lastmodifyingusername] [lastviewedbymedate] [modifieddate] [originalfilename] [quotaused] [shared] [writerscanshare]
```
Outputs detailed information about a specific file. The optional `allfields` arguments causes all possible columns to be included in the output. The optional `createddate`, `description`, `fileextension`, `filesize`, `id`, `name`, `restricted`, `starred`, `trashed`, `viewed`, `lastmodifyingusername`, `lastviewedbymedate`, `modifieddate`, `originalfilename`, `quotaused`, `shared` and `writerscanshare` arguments cause the given fields to be shown.

### Example
This example shows the file information for Drive ID adifd08
```
gam user asmith@acme.com show fileinfo adifd08
```

---


## Show Drive File Revisions for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show filerevisions <file id>
```
Show the revisions for a file. 

### Examples
This example shows the file revisions for Drive ID adifd08
```
gam user asmith@acme.com show filerevisions adifd08
```

## Empty Drive Trash for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users empty drivetrash
```
Empty users' Drive trash. 

### Examples
This example shows emptying the drive trash for users in the technology group.
```
gam group technology@acme.com empty drivetrash
```

---


# Managing Google Drive Permissions for Users
## Showing the Permissions of a File/Folder for a user
### Syntax
```
gam user <email> show drivefileacl <file id> [asadmin]
```
shows the current permissions of a file or folder owned or shared with a given user. The optional asadmin argument specifies that the super admin should use special access to manage a shared drive which they do not normally have access to. This argument may not work on non shared drive resources.

### Example
This example shows the permissions of one of jsmith's files
```
gam user jsmith@acme.org show drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE

John Smith
 domain: acme.org
 emailAddress: jsmith@acme.org
 photoLink: https://lh5.googleusercontent.com/-AzWvbYordY/AAAAAAAAAAE/AAAAAAAAERg/nzagv0IV4yQ/s64/photo.jpg
 role: owner
 type: user
 id: 17297927562723854745

George Wilson
 domain: gmail.com
 emailAddress: gwilson@gmail.com
 photoLink: https://lh5.googleusercontent.com/-woxYfVbgI4w/AAAAAAAAAaI/AAAAAAAAb
SI/Y0RRW2LWX5U/s64/photo.jpg
 role: writer
 type: user
 id: 00772439636938147216
```

---


## Adding permissions to a file/folder for a user
### Syntax
```
gam user <user email> add drivefileacl <file id> [user|group|domain|anyone <value>] [withlink] [role <reader|commenter|writer|owner|organizer>] [sendemail] [emailmessage <message text>]
```
Grants a user, group, domain or anyone permission to the given Drive file/folder. The role parameter determines the level of access the given user(s) have to the file and can be one of reader, commenter, writer, owner or organizer. Specifying owner will change ownership of the file/folder and only works when the source and target accounts are in the same G Suite instance. Organizer replaces and is the equivalent to the owner role for shared drives. The optional withlink parameter specifies that the file is not "discoverable" or indexed. It is only available if the accessing user knows the exact URL. The optional sendemail parameter will send an email to the user(s) who have been granted access to the file (no email sent by default). The optional emailmessage parameter allows you to specify a portion of the email message body sent to the user.

### Examples
This example silently gives Sally access to Tim's file
```
gam user tim@acme.org add drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE user sally@acme.org role writer withlink
```

This example gives the IT Google Group access to Tim's file and sends an email notification
```
gam user tim@acme.org add drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE group it@acme.org role reader sendemail
```

This example gives anyone in the Acme organization access to Tim's file if they know the URL
```
gam user tim@acme.org add drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE domain acme.org role commenter withlink
```

This example gives anyone on the Internet (logged in to Google or not) access to Tim's file and makes it searchable/discoverable via Google.com search and other search engines
```
gam user tim@acme.org add drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE anyone role reader
```

---


## Updating permissions to a file/folder for a user
### Syntax
```
gam user <user email> update drivefileacl <file id> <permission id> [withlink] [role <reader|commenter|writer|owner|organizer>] [asadmin]
```
Changes a user or groups permissions to the given Drive file/folder. The permisson id parameter can be an email address or a numeric id as shown when listing a file's permissions. If an email address is used, GAM must first look up the permission id of that email address before updating (2 API calls instead of 1). If using numeric id, you must prefix it with "id:". The role parameter determines the level of access the given user(s) have to the file and can be one of reader, commenter, writer, owner or organizer. Specifying owner will change ownership of the file/folder and only works when the source and target accounts are in the same G Suite instance. Organizer replaces and is the equivalent to the owner role for shared drives. The optional withlink parameter specifies that the file is not "discoverable" or indexed. It is only available if the accessing user knows the exact URL. The optional asadmin argument specifies that the super admin should use special access to manage a shared drive which they do not normally have access to. This argument may not work on non shared drive resources.

### Example
This example changes Sally from a reader to a writer for the file.
```
gam user tim@acme.org update drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE sally@acme.org role writer withlink
```

### Example
This example changes Sally from a reader to a writer for the file using her numeric permission ID.
```
gam user tim@acme.org update drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE id:65337053707119961365 role writer withlink
```
### Example
This example makes Sally the owner for the file and changes Tim from owner to writer for the file.
```
gam user tim@acme.org update drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE sally@acme.org role owner
```

---


## Removing permissions to a file/folder for a user
### Syntax
```
gam user <user email> delete drivefileacl <file id> <permission id> [asadmin]
```
Removes the given permission from the file. The permisson id parameter can be an email address or a numeric id as shown when listing a file's permissions. If an email address is used, GAM must first look up the permission id of that email address before updating (2 API calls instead of 1). If using numeric id, you must prefix it with "id:". The optional asadmin argument specifies that the super admin should use special access to manage a shared drive which they do not normally have access to. This argument may not work on non shared drive resources.

### Example
This example removes Sally's access to Tim's file
```
gam user tim@acme.org delete drivefileacl 0B8aCWH-xLi2NckxXOEp5REUtNEE sally@acme.org
```
# Managing shared drives
GAM 4.2 and newer support shared drive management. You can create, update, delete and list shared drives for users. Shared drives can be shared in the same way [Google Drive Files/Folders are shared](#managing-google-drive-permissions-for-users).

Note: Shared drives were previously known as Team Drives.

## Creating shared drives
### Syntax
```
gam user <email> add shareddrive <name>
```
Creates a new shared drive. The name argument specifies the name of the shared drive. The specified user will be the first organizer.

### Example
This example creates a "Sales Reports" shared drive and makes jsalesguy@acme.com the first organizer of the Drive.
```
gam user jsalesguy@acme.com add shareddrive "Sales Reports"
```
----
## Adding user permissions to shared drives
### Syntax
```
gam user <user a email> add drivefileacl <DriveFileEntity> user <user b email> role <DriveFileACLRole>) [withlink|(allowfilediscovery|discoverable [<Boolean>])] [expires|expiration <Time>] [sendemail] [emailmessage <String>] [showtitles]
```
adds a new "user b" to a shared drive owned by "user a". The specified "user b" will be the set role.

### Example
This example adds jsalesguy@acme.com to the shared drive owned by jbossguy@acme.com and makes jsalesguy@acme.com a content and permission manager of the Drive.
```
gam user jbossguy@acme.com add drivefileacl 0ABXXXXXXXXXX9PVA user jsalesguy@acme.com role contentmanager
```
----
## Updating shared drives
### Syntax
```
gam user <email> update shareddrive <id> [name <name>] [ou <orgunit>] [hidden <true|false>]
```
Updates the shared drive specified by the id argument. The name argument updates the shared drive name. The ou argument moves the shared drive to a new orgunit (THIS FEATURE IS CURRENTLY ALPHA). The hidden argument hides or unhides the given shared drive for the given user.

### Example
This example changes the name of shared drive ID dfdfaskfd23 to "2016 Sales Reports"
```
gam user jsalesguy@acme.com update shareddrive dfdfaskfd23 name "2016 Sales Reports"
```

This example moves a shared drive to the /Shared Drives OrgUnit
```
gam user admin@acme.com update shareddrive ou "/Shared Drives"
```
----
## Deleting shared drives
### Syntax
```
gam user <email> delete shareddrive <id> [allowitemdeletion]
```
Deletes the shared drive specified by the id argument. By default, if there are any files/folders on the shared drive then deleting it will fail. The optional argument `allowitemdeletion` will delete the shared drive AND all files/folders currently on it and must be performed by a super admin user.

### Example
This example deletes the dfdfaskfd23 shared drive even if there are files on it.
```
----
gam user jsalesguy@acme.com delete shareddrive dfdfaskfd23 allowitemdeletion
```
----
## Showing/Printing shared drives
### Syntax
```
gam user <email> print|show shareddrives [todrive] [asadmin]
```
Prints to CSV or screen the shared drives the given user(s) can access. The print argument will output CSV format or, if todrive is specified, a Google Sheet. The show argument will output a user-legible list of shared drives to the screen. The optional asadmin argument specifies that the super admin should use special access to manage a shared drive which they do not normally have access to. This argument may not work on non shared drive resources.

### Example
This example creates a Google Sheet of the shared drives accessible to all users in the domain. It will require at least 1 API call per-user.
```
gam all users print shareddrives todrive
```
