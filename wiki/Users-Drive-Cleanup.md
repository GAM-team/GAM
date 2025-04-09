# Users - Drive - Cleanup
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Display empty folders](#display-empty-folders)
- [Delete empty folders](#delete-empty-folders)
- [Empty the trash on My Drive](#empty-the-trash-on-my-drive)
- [Empty the trash on a Shared Drive](#empty-the-trash-on-a-shared-drive)
- [Delete contents of My Drive](#delete-contents-of-my-drive)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/v3/reference/files)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<SharedDriveEntity> ::=
        <SharedDriveID>|(teamdriveid <SharedDriveID>)|(teamdriveid:<SharedDriveID>)|
        (teamdrive <SharedDriveName>)|(teamdrive:<SharedDriveName>)
```
## Display empty folders
```
gam <UserTypeEntity> print emptydrivefolders [todrive <ToDriveAttribute>*]
        [select <DriveFileEntity>]
        [pathdelimiter <Character>]
```
By default, empty folders on My Drive are displayed. Use `select <DriveFileEntity>`
to select a Shared Drive or an alternate starting point folder on My Drive or a Shared Drive.

By default, folder path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

## Delete empty folders
```
gam <UserTypeEntity> delete emptydrivefolders
        [select <DriveFileEntity>]
        [<SharedDriveEntity>]
        [pathdelimiter <Character>]
```
By default, empty folders on My Drive are deleted(purged). Use `select <DriveFileEntity>`
to select a Shared Drive or an alternate starting point folder on My Drive or a Shared Drive.

By default, folder path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

## Empty the trash on My Drive
```
gam <UserTypeEntity> empty drivetrash
```
## Empty the trash on a Shared Drive
```
gam <UserTypeEntity> empty drivetrash <SharedDriveEntity>
```
## Delete contents of My Drive

The following commands will delete the contents of a user's My Drive.

This is not reversible, Think before proceeding.

### Method 1
* Generate a complete list of files/folders that a user owns; this gives you a record of the files/folders that will be deleted. 
* This list may be quite large.
* Delete the top level files/folders; orphans will be deleted.

Show current drive usage.
```
gam redirect stdout ./DrivefileUsage.txt user user@domain.com show drivesettings
```
Generate an initial list of files.
```
gam redirect csv ./InitialFileList.csv user user@domain.com print filelist fields id,name,mimetype,basicpermissions,parents fullpath showdepth orderby name
```
Purge top level files/folders; includes orphans.
```
gam config csv_input_row_filter "depth:count=0" redirect stdout ./PurgeTopLevelFilesFolders.txt multiprocess redirect stderr stdout csv ./InitialFileList.csv gam user "~Owner" purge drivefile "~id"
```
Generate list of remaining files/folders; this list should be empty; investigate if not.
```
gam redirect csv ./FinalFileList.csv user user@domain.com print filelist fields id,name,mimetype,basicpermissions,parents fullpath showdepth orderby name
```
Show updated drive usage.
```
gam redirect stdout ./DrivefileUsage.txt append user user@domain.com show drivesettings
```
### Method 2
* Generate a list of top level files/folders that a user owns.
* Delete them; orphans are not included
* Generate a list of remaining file/folders (orphans).
* Delete them.

Show current drive usage.
```
gam redirect stdout ./DrivefileUsage.txt user user@domain.com show drivesettings
```
Get list of top level files/folders.

GAM version `6.22.14` and higher:
```
gam redirect csv ./TopLevelFilesFolders.csv user user@domain.com print filelist select rootid fields id,name,mimetype depth 0
```
GAM version `6.22.13` and lower.
```
gam user user@domain.com show fileinfo root fields id
User: user@domain.com, Show 1 Drive File/Folder
  Drive Folder: My Drive (0AENlVEBUkz-hUkWXYZ)
    id: 0AENlVEBUkz-hUkWXYZ
gam redirect csv ./TopLevelFilesFolders.csv user user@domain.com print filelist select 0AENlVEBUkz-hUkWXYZ fields id,name,mimetype depth 0
```
Purge top level files/folders.
```
gam redirect stdout ./PurgeTopLevelFilesFolders.txt multiprocess redirect stderr stdout csv ./TopLevelFilesFolders.csv gam user "~Owner" purge drivefile "~id"
```
Get list of remaining files/folders; this list will typically be empty but will list orphans if they exist.
```
gam redirect csv ./OrphanFilesFolders.csv user user@domain.com print filelist fields id,name,mimetype,parents fullpath showdepth
```
Purge top level orphan files/folders; sub files/folders will also be deleted.
```
gam config csv_input_row_filter "depth:count=0" redirect stdout ./PurgeOrphanFilesFolders.txt multiprocess redirect stderr stdout csv ./OrphanFilesFolders.csv gam user "~Owner" purge drivefile "~id"
```
Generate list of remaining files/folders; this list should be empty; investigate if not.
```
gam redirect csv ./FinalFileList.csv user user@domain.com print filelist fields id,name,mimetype,basicpermissions,parents fullpath showdepth orderby name
```
Show updated drive usage.
```
gam redirect stdout ./DrivefileUsage.txt append user user@domain.com show drivesettings
```
### Method 3
* GAM version `6.30.09` and higher
* Generate a list of top level files/folders that a user owns.
* Delete them; orphans are not included
* Generate a list of remaining file/folders (orphans).
* Delete them.

Show current drive usage.
```
gam redirect stdout ./DrivefileUsage.txt user user@domain.com show drivesettings
```
Get list of top level files/folders if desired.
```
gam redirect csv ./TopLevelFilesFolders.csv user user@domain.com print filelist my_top_items fields id,name,mimetype
```
Purge top level files/folders.
```
gam redirect stdout ./PurgeTopLevelFilesFolders.txt redirect stderr stdout user user@domain.com purge drivefile my_top_items
```
Get list of remaining files/folders; this list will typically be empty but will list orphans if they exist.
```
gam redirect csv ./OrphanFilesFolders.csv user user@domain.com print filelist fields id,name,mimetype,parents fullpath showdepth
```
Purge top level orphan files/folders; sub files/folders will also be deleted.
```
gam config csv_input_row_filter "depth:count=0" redirect stdout ./PurgeOrphanFilesFolders.txt multiprocess redirect stderr stdout csv ./OrphanFilesFolders.csv gam user "~Owner" purge drivefile "~id"
```
Generate list of remaining files/folders; this list should be empty; investigate if not.
```
gam redirect csv ./FinalFileList.csv user user@domain.com print filelist fields id,name,mimetype,basicpermissions,parents fullpath showdepth orderby name
```
Show updated drive usage.
```
gam redirect stdout ./DrivefileUsage.txt append user user@domain.com show drivesettings
```
