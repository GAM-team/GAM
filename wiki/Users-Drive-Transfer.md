# Users - Drive - Transfer
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Definitions](#definitions)
- [Google Data Transfers](Google-Data-Transfers)
- [GAM Data Transfers](#gam-data-transfers)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
* [Shortcuts](https://developers.google.com/drive/api/guides/shortcuts)
* [Prepare account for transfer](https://support.google.com/a/answer/1247799)
* [Limited and Expansive Access](https://developers.google.com/workspace/drive/api/guides/limited-expansive-access)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<DriveFileOrderByFieldName> ::=
        createddate|createdtime|
        folder|
        lastviewedbyme|lastviewedbymedate|lastviewedbymetime|lastviewedbyuser|
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
## GAM Data Transfers
```
gam <UserTypeEntity> transfer drive <UserItem> [select <DriveFileEntity>]
        [(targetfolderid <DriveFolderID>)|(targetfoldername <DriveFolderName>)]
        [targetuserfoldername <DriveFolderName>] [targetuserorphansfoldername <DriveFolderName>]
        [mergewithtarget [<Boolean>]]
        [skipids <DriveFileEntity>]
        [keepuser|(retainrole reader|commenter|writer|editor|contentmanager|fileorganizer|none)]
        [noretentionmessages]
        [nonowner_retainrole reader|commenter|writer|editor|contentmanager|fileorganizer|current|none]
        [nonowner_targetrole reader|commenter|writer|editor|contentmanager|fileorganizer|current|none|source]
        [enforceexpansiveaccess [<Boolean>]]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [preview] [todrive <ToDriveAttribute>*]
```
By default, all of the source users files will be transferred except those in the trash. If you want to transfer a subset of
the source users files, use the `select <DriveFileEntity>` option.

This option handles special cases where you want to prevent selected files/folders from being transferred.
* `skipids <DriveFileEntity>` - Do not transfer files/folders with the specified IDs.

You can specify the access that the source user retains to the files that it owns.
If no option is  specified, the source user retains no access to the transferred files.
* `keepuser` - The source user retains write access to the files; old style, equivalent to `retainrole writer`.
* `retainrole reader|commenter|writer|editor|contentmanager|fileorganizer` - The source user retains the specified access to the files.
* `retainrole none` - The source user retains no access to the files; this is the default.

You can specify the access that the source user retains to the files that it does not own.
If no option is  specified, the source user retains the same access as specifed with `retainrole`.
* `nonowner_retainrole reader|commenter|writer|editor|contentmanager|fileorganizer` - The source user retains the specified access to the files.
* `nonowner_retainrole current` - The source user retains its current access to the files.
* `nonowner_retainrole none` - The source user retains no access to the files.

You can specify the access that is assigned to the target user for those files that the source user does not own.
If the target user already has access to a file, the following options will not diminish that access.
If no option is  specified, the target user gets the same access to the files that the source user had.
* `nonowner_targetrole reader|commenter|writer|editor|contentmanager|fileorganizer` - The target user gets the specified access to the files.
* `nonowner_targetrole current` - The target user maintains its current access to the files.
* `nonowner_targetrole none` - The target user gets no access to the files.
* `nonowner_targetrole source` - The target user gets the same access to the files that the source user had; this is the default.

* `noretentionmessages` - Suppress the role retention messages.

The transferred files are placed into a subfolder of an existing parent folder that belongs to the target user.
The parent folder must exist, the subfolder will be created if necessary.

Choose one of the following options to specify an existing target user folder as the parent folder of the subfolder.
If neither option is chosen, the root folder of the target user will be the parent folder of the subfolder.
* `targetfolderid <DriveFolderID>` - The ID of an existing folder owned by the target user,
* `targetfoldername <DriveFolderName>` - The name of an existing folder owned by the target user.

Use the following option to specify the subfolder of the parent folder to receive the transferred files.
This folder will be created if necessary. If `targetuserfoldername` is not specified, the default value `#user# old files` will be used.
* `targetuserfoldername <DriveFolderName>` - The name of a subfolder under the parent folder.
* `targetuserfoldername ""` - No subfolder will be created, the transferred files will be transferred to the parent folder.

The option `mergewithtarget`, when used with `select <DriveFileItem>`, transfers a folder without creating a new folder in the target user folder.
The contents of the folder, but not the folder itself, are transferred to the new owner.

Use the following option to specify the subfolder of the parent folder to receive the transferred orphaned files.
This folder will be created if necessary. If `targetuserorphansfoldername` is not specified, the default value `#user# orphaned files` will be used.
* `targetuserorphansfoldername <DriveFolderName>` - The name of a subfolder under the parent folder.
* `targetuserorphansfoldername ""` - No subfolder will be created, the transferred orphaned files will be transferred to the parent folder.

In `<DriveFolderName>`, the following substitutions will be made:
* `#user#` - Will be replaced by the source users email address.
* `#email#` - Will be replaced by the source users email address.
* `#username#` - Will be replaced by the portion of the source users email address before the @.

Use the `preview` option to output a CSV file showing the files to be transferred without actually performing the transfer.
The column headers are: `OldOwner, NewOwner, type, id, title`.

### Caution
As of September 30th, 2020, Google changed how Drive API behaves where multi-parenting of a file is no longer allowed. When moving a file which has inherited permissions, it's important to review permissions before attempting an ownership transfer.

> When transferring ownership of a file, the requester can control whether the transferred file is moved to the new owner’s My Drive or kept in its current location. If the requester chooses to move the file, any access inherited from the previous parent is lost. However, the access that had been directly added to the file is preserved. The previous owner maintains editor access on the file, just as they had prior to these changes.


### Examples

Use defaults for the parent folder and subfolder; a subfolder named `olduser@domain.com old files` will be created as a subfolder of the root folder of newuser@domain.com.
The source user retains no access to the files.
```
gam user olduser@domain.com transfer drive newuser@domain.com
```

Transfer several users files to subfolders named "#username#'s Files" under the existing target parent folder named "Transferred Files".
```
gam users olduser1,olduser2,olduser3 transfer drive newuser@domain.com targetfoldername "Transferred Files" targetuserfoldername "#username#'s Files" targetuserorphansfoldername" "#username#'s Orphaned Files"
```
