# Users - Drive - Permissions
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Permission Matches](Permission-Matches)
- [Definitions](#definitions)
- [GUI API permission name mapping](#gui-api-permission-name-mapping)
- [Manage file permissions/sharing](#manage-file-permissionssharing)
- [Display file permissions/sharing](#display-file-permissionssharing)
- [Delete all ACLs except owner from a file](#delete-all-acls-except-owner-from-a-file)
- [Change shares to User1 to shares to User2](#change-shares-to-user1-to-shares-to-user2)
- [Map All ACLs from an old domain to a new domain](#map-all-acls-from-an-old-domain-to-a-new-domain)

## API documentation
* [Drive API - Permissions](https://developers.google.com/drive/api/v3/reference/permissions)
* [Shortcuts](https://developers.google.com/drive/api/guides/shortcuts)

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

<DrivePermissionsFieldName> ::=
        additionalroles|
        allowfilediscovery|
        basicpermissions|
        deleted|
        displayname|
        domain|
        emailaddress|
        expirationdate|
        expirationtime|
        id|
        name|
        pendingowner|
        permissiondetails|
        photolink|
        role|
        type|
        view|
        withlink
<DrivePermissionsFieldNameList> ::= "<DrivePermissionsFieldName>(,<DrivePermissionsFieldName>)*"

```
`basicpermissions` is equivalent to:
```
permissions.allowFileDiscovery,
permissions.deleted,
permissions.domain,
permissions.emailAddress,
permissions.expirationTime,
permissions.id,
permissions.role,
permissions.type
```
In particular, this omits these fields:
```
permissions.displayName,
permissions.permissionDetails,
permissions.photoLink,
permissions.teamDrivePermissionDetails
```
This allows you to select the essential permission fields without enumerating them. Of course,
you can specify `permissions` to get all of the fields, enumerate the specific fields you want or
specify `basicpermissions` and additional permission fields, e.g., `permissions.displayName`.

```
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
<DriveFileACLRole> ::=
        manager|organizer|owner|
        contentmanager|fileorganizer|
        contributor|writer|editor|
        commenter|
        viewer|reader
<DriveFileACLRoleList> ::= "<DriveFileACLRole>(,<DriveFileACLRole>)*"
<DriveFileACLType> ::= anyone|domain|group|user
<DriveFileACLTypeList> ::= "<DriveFileACLType>(,<DriveFileACLType>)*"
<DriveFilePermission> ::=
        anyone|anyonewithlink|
        user:<EmailAddress>|group:<EmailAddress>|
        domain:<DomainName>|domainwithlink:<DomainName>;<DriveFileACLRole>
<DriveFilePermissionID> ::=
        anyone|anyonewithlink|id:<String>
<DriveFilePermissionIDorEmail> ::=
        <DriveFilePermissionID>|<EmailAddress>
<DriveFilePermissionList> ::=
        "<DriveFilePermission>(,<DriveFilePermission)*"
<DriveFilePermissionIDList> ::=
        "<DriveFilePermissionID>(,<DriveFilePermissionID>)*"
<DriveFilePermissionEntity> ::=
         <DriveFilePermissionList> |
         (json [charset <Charset>] <JSONData>)|(json file <FileName> [charset <Charset>]) |
         <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<DriveFilePermissionIDEntity> ::=
         <DriveFilePermissionIDList> |
         (json [charset <Charset>] <JSONData>)|(json file <FileName> [charset <Charset>]) |
         <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
```
## GUI API permission name mapping

| GUI setting | API setting |
|------------|------------|
| Manager | organizer |
| Content manager | fileOrganizer |
| Contributor | writer |
| Commenter | commenter |
| Viewer | reader |

## Manage file permissions/sharing
### Process single ACLs.
### Create
```
gam <UserTypeEntity> create|add drivefileacl <DriveFileEntity>
        anyone|(user <UserItem>)|(group <GroupItem>)|(domain <DomainName>) (role <DriveFileACLRole>)
        [withlink|(allowfilediscovery|discoverable [<Boolean>])] [expiration <Time>]
        (mappermissionsdomain <DomainName> <DomainName>)*
        [movetonewownersroot [<Boolean>]]
        [sendemail] [emailmessage <String>]
        [updatesheetprotectedranges [<Boolean>]]
        [showtitles] [nodetails|(csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]])]
```
The option `mappermissionsdomain <DomainName1> <DomainName2>` maps `<DomainName1>` to `<DomainName2>` in the
`user <UserItem>)|(group <GroupItem>)|(domain <DomainName>)` options;
`<UserItem>` and `<GroupItem>` must specify email addresses for the mapping to succeed.
The option can be specified multiple times to provide different mappings. This option will be most useful
when reading a CSV file containing ACLs referencing `<DomainName1>` and you want a new ACL with the same options but in `<DomainName2>`.

From the Google Drive API documentation.
* `movetonewownersroot` - This parameter only takes effect if the item is not in a shared drive and the request is attempting to transfer the ownership of the item.
  * `false` - Parents are not changed. The file is an orphan for the new owner. This is the default.
  * `true` - The item is moved to the new owner's My Drive root folder and all prior parents removed. The file is in `Shared with me` for the old owner.

To transfer ownership of a file/folder and place it in a specific folder on the new owner's My Drive, do:
```
gam <UserTypeEntity> transfer ownership <DriveFileEntity> <UserItem> 
        [<DriveFileParentAttribute>] norecursion
```
See: https://github.com/GAM-team/GAM/wiki/Users-Drive-Ownership#transfer-ownership-of-files-that-a-source-user-owns-to-a-target-user

The options `withlink|allowfilediscovery|discoverable` are only valid for ACLs to `anyone` or `domain`.

The option `expiration <Time>` is only valid for `role commenter|contributor|viewer` for files and `commenter|viewer` for folders.
`<Time>` can not be more that one year in the future.

The option `updatesheetprotectedranges` only applies to items in `<DriveFileEntity>` that are Google Sheets.
* `updatesheetprotectedranges false` or option omitted
  * Sheet Protected Ranges are not updated
* `updatesheetprotectedranges` or `updatesheetprotectedranges true`
  * Sheet Protected Ranges are updated to reflect the new ACL; additional API calls are required.
    * ACLs with role reader or commenter will not be added to protected ranges
    * ACLs with role writer or higher will be added to existing protected ranges

By default, the file ID is displayed in the output; to see the file name, use the `showtitles`
option; this requires an additional API call per file.

By default, when an ACL is created, GAM outputs details of the ACL as indented keywords and values.
* `nodetails` - Suppress the details output.
* `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` - Output the details in CSV format.

### Update
```
gam <UserTypeEntity> update drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail>
        (role <DriveFileACLRole>) [expiration <Time>] [removeexpiration [<Boolean>]]
        [updatesheetprotectedranges [<Boolean>]]
        [showtitles] [nodetails|(csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]])]
```
There is no change of parents when a new user is updated to be a file's owner.

The option `expiration <Time>` is only valid for `role commenter|contributor|viewer` for files and `commenter|viewer` for folders.
`<Time>` can not be more that one year in the future.

The option `updatesheetprotectedranges` only applies to items in `<DriveFileEntity>` that are Google Sheets.
* `updatesheetprotectedranges false` or option omitted
  * Sheet Protected Ranges are not updated
* `updatesheetprotectedranges` or `updatesheetprotectedranges true`
  * Sheet Protected Ranges are updated to reflect the updated ACL; additional API calls are required.
    * ACLs with role reader or commenter will be removed from existing protected ranges
    * ACLs with role writer or higher will be added to existing protected ranges

By default, the file ID is displayed in the output; to see the file name, use the `showtitles`
option; this requires an additional API call per file.

By default, when an ACL is updated, GAM outputs details of the ACL as indented keywords and values.
* `nodetails` - Suppress the details output.
* `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` - Output the details in CSV format.

### Delete
```
gam <UserTypeEntity> delete|del drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail>
        [updatesheetprotectedranges [<Boolean>]]
        [showtitles]
```
The option `updatesheetprotectedranges` only applies to items in `<DriveFileEntity>` that are Google Sheets.
* `updatesheetprotectedranges false` or option omitted
  * Sheet Protected Ranges are not updated
* `updatesheetprotectedranges` or `updatesheetprotectedranges true`
  * Sheet Protected Ranges are updated to reflect the deleted ACL; additional API calls are required.
    * ACLs with any role will be removed from existing protected ranges

By default, the file ID is displayed in the output; to see the file name, use the `showtitles`
option; this requires an additional API call per file.

### Process multiple ACLs.
### Create
```
gam <UserTypeEntity> create|add permissions <DriveFileEntity> <DriveFilePermissionEntity>
        [expiration <Time>] [sendemail] [emailmessage <String>]
        [movetonewownersroot [<Boolean>]]
        <PermissionMatch>* [<PermissionMatchAction>]
```
The option `expiration <Time>` is only valid for `role commenter|reader|viewer`.

From the Google Drive API documentation.
* `movetonewownersroot` - This parameter only takes effect if the item is not in a shared drive and the request is attempting to transfer the ownership of the item.
  * `false` - Parents are not changed. The file is an orphan for the new owner. This is the default.
  * `true` - The item is moved to the new owner's My Drive root folder and all prior parents removed. The file is an orphan for the old owner.

Permission matching only applies when the `(json [charset <Charset>] <JSONData>)|(json file <FileName> [charset <Charset>])`
variant of `<DriveFilePermissionEntity>` and `<DriveFilePermissionIDEntity>` is used.

When adding permissions from JSON data, there is a default match: `pm not role owner em` that disables ownership changes.
If you want to process all permissions, enter `pm em` to clear the default match.

When adding permissions from JSON data, permissions with `deleted` true are never processed.

### Delete
```
gam <UserTypeEntity> delete permissions <DriveFileEntity> <DriveFilePermissionIDEntity>
        <PermissionMatch>* [<PermissionMatchAction>]
```
When deleting permissions from JSON data, permissions with role `owner` true are never processed.

## Display file permissions/sharing
```
gam <UserTypeEntity> info drivefileacl <DriveFileEntity> <DriveFilePermissionIDorEmail>
        [showtitles] [formatjson]
gam <UserTypeEntity> show drivefileacls <DriveFileEntity>
        (role|roles <DriveFileACLRoleList>)*
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [includepermissionsforview published]
        [oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        [showtitles|(addtitle <String>)]]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [formatjson]
gam <UserTypeEntity> print drivefileacls <DriveFileEntity> [todrive <ToDriveAttributes>*]
        (role|roles <DriveFileACLRoleList>)*
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [includepermissionsforview published]
        [oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        [showtitles|(addtitle <String>)]]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [formatjson [quotechar <Character>]]
```
By default, the file ID is displayed in the output; to see the file name, use the `showtitles`
option; this requires an additional API call per file. If you are reading the file IDs from a
CSV file that also includes the file name, you can use the `addtitle` option to supply the file name.

By default, all files specified are displayed; use the following option to select a subset of those files.
* `<PermissionMatch>* [<PermissionMatchAction>] pmselect` - Use permission matching to select files

By default, all ACLS are displayed; use the following option to select a subset of the ACLS to display.
* `role|roles <DriveFileACLRoleList>` - Display ACLs for the specified roles only.
* `<PermissionMatch>* [<PermissionMatchAction>]` - Use permission matching to display a subset of the ACLs for each file; this only applies when `pmselect` is not specified


With `print drivefileacls` or `show drivefileacls formatjson`, the ACLs selected for display are all output on one row/line as a repeating item with the matching file id.
When `oneitemperrow` is specified, each ACL is output on a separate row/line with the matching file id. This simplifies processing the CSV file with subsequent Gam commands.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

For example, to get the ACLs for your Team Drives with the Team Drive name included in the output:
```
gam redirect csv ./TeamDrives.csv print teamdrives
gam redirect csv ./TeamDriveACLs.csv multiprocess csv ./TeamDrives.csv gam print drivefileacls teamdriveid "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted
```

## Delete all ACLs except owner from a file
Get the current ACLs.
```
gam redirect csv ./Permissions.csv user <UserItem> print drivefileacls <DriveFileID> oneitemperrow
```
Inspect Permissions.csv, verify that you want to proceed.
```
gam config csv_input_row_drop_filter "permission.role:regex:(owner)|(organizer)" csv ./Permissions.csv gam user "~Owner" delete drivefileacl "~id" "id:~~permission.id~~"
```

## Change shares to User1 to shares to User2
```
# Get files shared to User1
gam redirect csv ./FilesSharedWithU1.csv user user1@domain.com print filelist choose sharedwithme fields id,name,mimetype,owners.emailaddress
# For each of these files, get the sharing settings for U1
gam redirect csv ./FilesSharedWithU1Settings.csv multiprocess csv FilesSharedWithU1.csv gam user "~owners.0.emailAddress" print drivefileacls "~id" pm emailaddress "~Owner" em
# For each of these files, delete the share to User1
gam redirect stdout ./DeleteU1Sharing.txt multiprocess redirect stderr stdout csv FilesSharedWithU1Settings.csv gam user "~Owner" delete drivefileacl "~id" "~permissions.0.emailAddress"
# For each of these files, add the share to User2 with the same role that User1 had
gam redirect stdout ./AddUser2Sharing.txt multiprocess redirect stderr stdout csv FilesSharedWithU1Settings.csv gam user "~Owner" create drivefileacl "~id" user user2@domain.com role "~permissions.0.role"
```

## Map All ACLs from an old domain to a new domain
* Get ACLs
```
gam redirect csv ./allUsersFiles.csv multiprocess all users print filelist fields name,id,basicpermissions oneitemperrow pmfilter pm domain olddomain.com em
```

* Delete ACLs with olddomain.com
```
gam redirect stdout ./DeleteOldDomainACLs.txt multiprocess redirect stderr stdout csv ./allUsersFiles.csv gam user "~Owner" delete drivefileacl "~id" "id:~~permission.id~~"
```

* Add user/group ACLs replacing olddomain.com with newdomain.com
```
gam config csv_input_row_filter "permission.type:regex:user|group" redirect stdout ./AddNewDomainACLsUserGroupShares.txt multiprocess redirect stderr stdout csv ./allUsersFiles.csv gam user "~Owner" create drivefileacl "~id" "~permission.type" "~permission.emailAddress" role "~permission.role" mappermissionsdomain olddomain.com newdomain.com
```

* Add domain ACLs replacing olddomain.com with newdomain.com
```
gam config csv_input_row_filter "permission.type:regex:domain" redirect stdout ./AddNewDomainACLsDomainShares.txt multiprocess redirect stderr stdout csv ./allUsersFiles.csv gam user "~Owner" create drivefileacl "~id" "~permission.type" "~permission.domain" role "~permission.role" allowfilediscovery "~permission.allowFileDiscovery" mappermissionsdomain olddomain.com newdomain.com
```
    
