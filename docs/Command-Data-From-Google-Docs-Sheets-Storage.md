# Command data from Google Docs, Sheets and Cloud Storage
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Read data from a Google Doc or Drive File](#read-data-from-a-google-doc-or-drive-file)
  - [Plain Text](#plain-text)
  - [HTML](#html)
- [Read data from a Google Sheet](#read-data-from-a-google-sheet)
- [Read data from a Google Cloud Storage File](#read-data-from-a-google-cloud-storage-file)
  - [Plain Text](#plain-text)
  - [CSV](#csv)
  - [HTML](#html)

## Introduction
Google Sheets can be used in `gam csv ...` commands.
* [Bulk Processing](Bulk-Processing)

Google Docs and Sheets can be used to specify collections of data.
* [Collections of ChromeOS Devices](Collections-of-ChromeOS-Devices)
* [Collections of Items](Collections-of-Items)
* [Collections of Users](Collections-of-Users)

Google Docs and Drive Files can be used to specify notes, messages and signatures.
* [Domain Shared Contacts - Global Address List](Contacts-GAL)
* [Send Email](Send-Email)
* [Users](Users)
* [Users - Contacts](Users-Contacts)
* [Users - Gmail - Messages/Threads](Users-Gmail-Messages-Threads)
* [Users - Gmail - SendAs/Signature/Vacation](Users-Gmail-Send-As-Signature-Vacation)

## Definitions
* [Drive Items](Drive-Items)

## Read data from a Google Doc or Drive File
```
<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)
```
* `<EmailAddress>` - The email address of a user with at least read access to the document

Use one of the following to specify the file:
* `<DriveFileIDEntity>` - The ID of the file on a Drive or Shared Drive
* `<DriveFileNameEntity>` - The name of the file
* `<SharedDriveEntity> <SharedDriveFileNameEntity>` - A Shared Drive and the name of the file on that drive

## Plain Text
Interpret a Google Doc as plain text or read a Drive file with MIME type text/plain.
```
gdoc <UserGoogleDoc>
```

## HTML
Read a Drive file with MIME type text/html.
```
ghtml <UserGoogleDoc>
```

## Read data from a Google Sheet
```
<SheetEntity> ::= <String>|id:<Number>

<UserGoogleSheet> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>) <SheetEntity>
```
* `<EmailAddress>` - The email address of a user with at least read access to the document

Use one of the following to specify the file:
* `<DriveFileIDEntity>` - The ID of the file on a Drive or Shared Drive
* `<DriveFileNameEntity>` - The name of the file
* `<SharedDriveEntity> <SharedDriveFileNameEntity>` - A Shared Drive and the name of the file on that drive

If a file name is specified, it must resolve to a single file ID; otherwise an error is generated.

If a Shared Drive name is specified, it must resolve to a single Shared Drive ID; otherwise an error is generated.

Select a sheet/tab from the Google Sheet with its ID or name; it is verified to exist within the Google Sheet.

Example:

```
gam csv gsheet you@exmaple.com <DriveFileIDEntity> "Sheet 1" gam create user firstname "~FirstName" lastname "~lastName" email "~email"
```
## Read data from a Google Cloud Storage File
```
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>
```

## CSV
Read a Google Cloud Storage file with contentType text/csv.
```
gcscsv <StorageBucketObjectName>
```

## Plain Text
Read a Google Cloud Storage file with contentType text/plain.
```
gcsdoc <StorageBucketObjectName>
```

## HTML
Read a Google Cloud Storage file with contentType text/html.
```
gcshtml <StorageBucketObjectName>
```
