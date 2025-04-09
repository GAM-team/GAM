# Users - Drive - Orphans
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Collect orphaned files](#collect-orphaned-files)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/v3/reference/files)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<DriveFileName> ::= <String>
<DriveOrderByFieldName> ::=
        createddate|createdtime|
        folder|
        modifiedbyme|modifiedbymedate|modifiedbymetime|modifiedbyuser|
        modifieddate|modifiedtime|
        name|
        name_natural|
        quotabytesused|quotaused|
        recency|
        sharedwithmedate|sharedwithmetime|
        starred|
        title|
        title_natural|
        viewedbymedate|viewedbymetime
```
## Collect orphaned files
Collect a users orphaned Drive files/folders into a target folder; only orphaned files not in the trash are processed.
```
gam <UserTypeEntity> collect orphans
        [(targetuserfoldername <DriveFolderName>)|(targetuserfolderid <DriveFolderID>)]
        [useshortcuts [<Boolean>]]
        (orderby <DriveOrderByFieldName> [ascending|descending])*
        [preview [todrive <ToDriveAttribute>*]]
```
* `targetuserfoldername <DriveFileName>` - This is the parent folder name for the orphaned files; the default is "#user# orphaned files". In this string, #user# and #email# will be replaced by the source user email address, #username# will be replaced by the source user mail address without the domain. This folder will be created is necessary.
* `targetuserfolderid <DriveFolderID>` - This is the parent folder ID for the orphaned files; it must exist.
* `useshortcuts false` - Add the target user folder as the parent of an orphan if it can be done; otherwise, put a shortcut to the orphan into the target user folder. This is the default behavior. Changing the parent may affect the orphan's access by other users.
* `useshortcuts` or `useshortcuts true` - Put a shortcut to the orphan into the target user folder and do not modify the orphan's parents. GAM will not duplicate an existing shortcut.
* `orderby <DriveOrderByFieldName> [ascending|descending])*` - Specify the order in which files are processed.
* `preview` - If `preview` is specified, no files are collected; a CSV file listing the files to be collected is output.
* `todrive <ToDriveAttribute>*` - When `preview` is specified, the CSV file can be uploaded to Google

### Example
Collect a users orphaned files into the folder "Orphans - testuser@domain.com" on their `My Drive`; change orphan parents if possible without affecting access by other users;
otherwise, use a shortcut.
```
gam user testuser@domain.com collect orphans targetuserfoldername "Orphans - #user#"
```

Collect a users orphaned files into the folder "Orphans - testuser@domain.com" on their `My Drive`; use shortcuts for all orphans rather than changing any orphan's parents.
```
gam user testuser@domain.com collect orphans targetuserfoldername "Orphans - #user#" useshortcuts
```
