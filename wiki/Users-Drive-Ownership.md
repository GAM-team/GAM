# Users - Drive - Ownership
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Definitions](#definitions)
- [Transfer ownership of files that a source user owns to a target user](#transfer-ownership-of-files-that-a-source-user-owns-to-a-target-user)
- [Claim ownership of files that other users own](#claim-ownership-of-files-that-other-users-own)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
* [Limited and Expansive Access](https://developers.google.com/workspace/drive/api/guides/limited-expansive-access)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<DriveFolderID> ::= <String>
<DriveFolderName> ::= <String>
<DriveFolderNameList> ::= "<DriveFolderName>(,<DriveFolderName>)*"
<DriveFolderPath> ::= <String>(/<String>)*
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>

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
## Transfer ownership of files that a source user owns to a target user
This is typically used when a user owns a file/folder within a folder owned by another user
and ownership is to be transferred to the owner of the containing folder.

Use [Users - Drive - Transfer](Users-Drive-Transfer) for more complex ownership transfers.
```
gam <UserTypeEntity> transfer ownership <DriveFileEntity> <UserItem>
        [<DriveFileParentAttribute>] [includetrashed] [norecursion [<Boolean>]]
        [enforceexpansiveaccess [<Boolean>]]
        (orderby <DriveOrderByFieldName> [ascending|descending])*
        [preview] [filepath] [pathdelimiter <Character>] [buildtree] [todrive <ToDriveAttribute>*]
```
`<DriveFileEntity>` specifies a file/folder owned by the source user `<UserTypeEntity>`.

The target user is specified by `<UserItem>`.

By default, there is no change of parents for the transferred files/folders, they remain in their current location.
* `<DriveFileParentAttribute>` - Specify a parent folder in the My Drive of the target user `<UserItem>`.

By default, files in the trash are not transferred.
* `includetrashed` - Ownership of files in the trash will be transferred.

By default, ownership transfer of a folder includes all of its sub files and folders.
* `norecursion` or `norecursion true` - No sub files and folders of the selected folder have their ownership transferred.

Specify order of file processing.
* `(orderby <DriveOrderByFieldName> [ascending|descending])*`

Preview the transfer.

Typically, the filepath option is used with the preview option so you can verify what files are going to be transferred.
If buildtree is specified, you will see the full path to each file. If buildtree is not specified, you will see the
relative file path starting from the top level folder being transferred.
* `preview` - Output a CSV file showing what files will have their ownership transferred.
* `filepath` - Show full path to files in CSV file.
* `pathdelimiter <Character>` - By default, file path components are separated by `/`; use `<Character>` as the separator instead.
* `buildtree` - Download all user files so that full filepath information is available.

## Claim ownership of files that other users own
This is typically used in a classroom setting where a teacher has shared a folder to students;
the students create files in the folder and the teacher claims ownership of the files at some
point to control the students further access to the files.
```
gam <UserTypeEntity> claim ownership <DriveFileEntity>
        [<DriveFileParentAttribute>] [includetrashed]
        [skipids <DriveFileEntity>] [onlyusers|skipusers <UserTypeEntity>] [subdomains <DomainNameEntity>]
        [restricted [<Boolean>]] [writerscanshare|writerscantshare [<Boolean>]]
        [keepuser | (retainrole reader|commenter|writer|editor|none)] [noretentionmessages]
        [enforceexpansiveaccess [<Boolean>]]
        (orderby <DriveOrderByFieldName> [ascending|descending])*
        [preview] [filepath] [pathdelimiter <Character>] [buildtree] [todrive <ToDriveAttribute>*]
```
By default, there is no change of parents for the claimed files/folders, they remain in their current location.
* `<DriveFileParentAttribute>` - Specify a parent folder in the My Drive of the claiming user `<UserTypeEntity>`.

By default, files in the trash are not transferred.
* `includetrashed` - Ownership of files in the trash will be transferred.

Specify order of file processing.
* `(orderby <DriveOrderByFieldName> [ascending|descending])*`

This option handles special cases where you want to prevent ownership from being transferred for selected files/folders.
* `skipids <DriveFileEntity>` - Do not transfer ownership for files/folders with the specified IDs.

These mutually exclusive  options handle special cases where you want to prevent ownership from being transferred based on the current file/folder owner.
* `onlyusers <UserTypeEntity>` - Only transfer ownership for files/folders owned by the specified users.
* `skipusers <UserTypeEntity>` - Do not transfer ownership for files/folders owned by the specified users.

By default, only files owned by users in the same domain as the claiming user have their ownership transferred.
* `subdomains <DomainNameEntity>` - Transfer ownership for files in the selected sub-domains.

These options handle special cases where you want to restrict access to the claimed files.
* `restricted [<Boolean>]` - Prevent viewers and commenters from downloading, printing, and copying the files.
* `writerscanshare [<Boolean>]` - Allow writers to share the document with other users.
* `writerscantshare [<Boolean>]` - Prevent writers from sharing the document with other users.

Specify role for original owner.
* `keepuser` - Original owner retains the role of writer; this is the default
* `retainrole reader|commenter|writer|editor` - Original owner retains the specified role
* `retainrole none` - Orginal owner retains no role

* `noretentionmessages` - Suppress the owner role retention messages.

Preview the transfer.

Typically, the filepath option is used with the preview option so you can verify what files are going to be transferred.
If buildtree is specified, you will see the full path to each file. If buildtree is not specified, you will see the
relative file path starting from the top level folder being transferred.
* `preview` - Output a CSV file showing what files will have their ownership transferred.
* `filepath` - Show full path to files in CSV file.
* `pathdelimiter <Character>` - By default, file path components are separated by `/`; use `<Character>` as the separator instead.
* `buildtree` - Download all user files so that full filepath information is available.
