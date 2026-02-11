# Drive Items
- [Basic Items](Basic-Items)
- [List Items](List-Items)
```
<DriveFileID> ::= <String>
<DriveFileURL> ::=
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
<DriveFileName> ::= <String>
<DriveFileIDEntity> ::=
        <DriveFileItem> |
        (id <DriveFileItem>) | (id:<DriveFileItem>) |
        (ids <DriveFileList>) | (ids:<DriveFileList>)
<DriveFileNameEntity> ::=
        (name <DriveFileName>) | (name:<DriveFileName>) |
        (drivefilename <DriveFileName>) | (drivefilename:<DriveFileName>) |
        (anyname <DriveFileName>) | (anyname:<DriveFileName>) |
        (anydrivefilename <DriveFileName>) | (anydrivefilename:<DriveFileName>)
<SharedDriveIDEntity> ::=
        <DriveFileItem> |
        (shareddriveid <DriveFileItem>) | (shareddriveid:<DriveFileItem>)
<SharedDriveName> ::= <String>
<SharedDriveNameEntity> ::=
        (shareddrive <SharedDriveName>) | (shareddrive:<SharedDriveName>)
<SharedDriveEntity> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>
<SharedDriveFileNameEntity> ::=
        (shareddrivefilename <DriveFileName>) | (shareddrivefilename:<DriveFileName>)
```
