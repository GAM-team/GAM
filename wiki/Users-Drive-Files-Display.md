# Users - Drive Files Display
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Permission Matches](Permission-Matches)
- [Definitions](#definitions)
- [Return Codes](#return-codes)
- [File size fields](#file-size-fields)
- [Display file information](#display-file-information)
- [Display file paths](#display-file-paths)
- [Select files for Display file counts, list, tree](#select-files-for-display-file-counts-list-tree)
  - [File selection definitions](#file-selection-definitions)
  - [File selection defaults](#file-selection-defaults)
  - [File selection by query](#file-selection-by-query)
  - [File selection of Shared Drive](#file-selection-of-shared-drive)
  - [File selection by corpora](#file-selection-by-corpora)
  - [File selection by ownership](#file-selection-by-ownership)
  - [File selection by MIME type](#file-selection-by-mime-type)
  - [File selection by file size](#file-selection-by-file-size)
  - [File selection by file name pattern matching](#file-selection-by-file-name-pattern-matching)
  - [File selection by permission matching](#file-selection-by-permission-matching)
  - [File selection to exclude items in the trash](#file-selection-to-exclude-items-in-the-trash)
- [Display file counts](#display-file-counts)
- [Display file share counts](#display-file-share-counts)
- [Display file tree](#display-file-tree)
  - [File selection starting point for Display file tree](#file-selection-starting-point-for-display-file-tree)
- [Display file parent tree](#display-file-parent-tree)
- [Display file list](#display-file-list)
  - [File selection by name and entity shortcuts for Display file list](#file-selection-by-name-and-entity-shortcuts-for-display-file-list)
  - [File selection starting point for Display file list](#file-selection-starting-point-for-display-file-list)
  - [File selection with or without a particular drive label](#file-selection-with-or-without-a-particular-drive-label)
  - [Handle empty file lists](#handle-empty-file-lists)
- [Display disk usage](#display-disk-usage)
- [Display files published to the web](#display-files-published-to-the-web)
- [Display information about last modified file on a drive](#display-information-about-last-modified-file-on-a-drive)

## API documentation
* [Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
* [Third-party Apps](https://support.google.com/a/answer/6105699)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<CorporaAttribute> ::=
        alldrives |
        domain |
        onlyteamdrives |
        user
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today

<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<SharedDriveIDEntity> ::= (teamdriveid <SharedDriveID>) | (teamdriveid:<SharedDriveID>)
<SharedDriveNameEntity> ::= (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
<SharedDriveFileNameEntity> ::= (teamdrivefilename <DriveFileName>) | (teamdrivefilename:<DriveFileName>)

<SharedDriveEntity> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>

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
        gsite
<MimeTypeName> ::= application|audio|font|image|message|model|multipart|text|video
<MimeTypeNameList> ::= "<MimeTypeName>(,<MimeTypeName>)*"
<MimeType> ::= <MimeTypeShortcut>|(<MimeTypeName>/<String>)
<MimeTypeList> ::= "<MimeType>(,<MimeType>)*"
```
```
<DriveCapabilitiesSubfieldName> ::=
        capabilities.canacceptownership|
        capabilities.canaddchildren|
        capabilities.canaddfolderfromanotherdrive|
        capabilities.canaddmydriveparent|
        capabilities.canchangecopyrequireswriterpermission|
        capabilities.canchangecopyrequireswriterpermissionrestriction|
        capabilities.canchangedomainusersonlyrestriction|
        capabilities.canchangedrivebackground|
        capabilities.canchangedrivemembersonlyrestriction|
        capabilities.canchangesecurityupdateenabled|
        capabilities.canchangesharingfoldersrequiresorganizerpermissionrestriction|
        capabilities.canchangeviewerscancopycontent|
        capabilities.cancomment|
        capabilities.cancopy|
        capabilities.candelete|
        capabilities.candeletechildren|
        capabilities.candeletedrive|
        capabilities.candisableinheritedpermissions|
        capabilities.candownload|
        capabilities.canedit|
        capabilities.canenableinheritedpermissions|
        capabilities.canlistchildren|
        capabilities.canmanagemembers|
        capabilities.canmodifycontent|
        capabilities.canmodifycontentrestriction|
        capabilities.canmodifyeditorcontentrestriction|
        capabilities.canmodifylabels|
        capabilities.canmodifyownercontentrestriction|
        capabilities.canmovechildrenoutofdrive|
        capabilities.canmovechildrenoutofteamdrive|
        capabilities.canmovechildrenwithindrive|
        capabilities.canmovechildrenwithinteamdrive|
        capabilities.canmoveitemintodrive|
        capabilities.canmoveitemintoteamdrive|
        capabilities.canmoveitemoutofdrive|
        capabilities.canmoveitemoutofteamdrive|
        capabilities.canmoveitemwithindrive|
        capabilities.canmoveitemwithinteamdrive|
        capabilities.canmoveteamdriveitem|
        capabilities.canreaddrive|
        capabilities.canreadlabels|
        capabilities.canreadrevisions|
        capabilities.canreadteamdrive|
        capabilities.canremovechildren|
        capabilities.canremovecontentrestriction|
        capabilities.canremovemydriveparent|
        capabilities.canrename|
        capabilities.canrenamedrive|
        capabilities.canresetdriverestrictions|
        capabilities.canshare|
        capabilities.cantrash|
        capabilities.cantrashchildren|
        capabilities.canuntrash

<DriveContentRestrictionsSubfieldName> ::=
        contentrestrictions.ownerrestricted|
        contentrestrictions.readonly|
        contentrestrictions.reason|
        contentrestrictions.restrictinguser|
        contentrestrictions.restrictiontime|
        contentrestrictions.type

<DriveLabelInfoSubfieldName> ::=
        labels.id|              # modifiedByMe
        labels.revisionid|      # copyRequiresWriterPermission
        labels.fields           # viewedByMe

<DriveLabelsSubfieldName> ::=
        labels.modified|        # modifiedByMe
        labels.restricted|      # copyRequiresWriterPermission
        labels.starred|         # starred
        labels.trashed|         # trashed
        labels.viewed           # viewedByMe

<DriveOwnersSubfieldName> ::=
        owners.displayname|
        owners.emailaddress|
        owners.isauthenticateduser|
        owners.me|
        owners.permissionid|
        owners.photolink|
        owners.picture

<DriveParentsSubfieldName> ::=
        parents.id|
        parents.isroot

<DrivePermissionsSubfieldName> ::=
        permissions.additionalroles|
        permissions.allowfilediscovery|
        permissions.deleted|
        permissions.permissiondetails|
        permissions.displayname|
        permissions.domain|
        permissions.emailaddress|
        permissions.expirationdate|
        permissions.expirationtime|
        permissions.id|
        permissions.name|
        permissions.photolink|
        permissions.role|
        permissions.type|
        permissions.withlink

<DriveLastModifyingUserSubfieldName> ::=
        lastmodifyinguser.displayname|
        lastmodifyinguser.emailaddress|
        lastmodifyinguser.isauthenticateduser|
        lastmodifyinguser.me|
        lastmodifyinguser.name|
        lastmodifyinguser.permissionid|
        lastmodifyinguser.photolink|
        lastmodifyinguser.picture

<DriveSharingUserSubfieldName> ::=
        sharinguser.displayname|
        sharinguser.emailaddress|
        sharinguser.isauthenticateduser|
        sharinguser.me|
        sharinguser.name|
        sharinguser.permissionid|
        sharinguser.photolink|
        sharinguser.picture

<DriveTrashingUserSubfieldName> ::=
        trashinguser.displayname|
        trashinguser.emailaddress|
        trashinguser.isauthenticateduser|
        trashinguser.me|
        trashinguser.name|
        trashinguser.permissionid|
        trashinguser.photolink|
        trashinguser.picture

<DriveShortcutDetailsSubfieldName> ::=
        shortcutdetails.targetid|
        shortcutdetails.targetmimetype
        shortcutdetails.resourcekey
```
```
<DriveFieldName> ::=
        alternatelink|
        appdatacontents|
        appproperties|
        basicpermissions|
        cancomment|
        canreadrevisions|
        capabilities|
        <DriveCapabilitiesSubfieldName>|
        contenthints|
        contentrestrictions|
        <DriveContentRestrictionsSubfieldName>|
        copyable|
        copyrequireswriterpermission|
        createddate|createdtime|
        description|
        driveid|
        drivename|
        editable|
        explicitlytrashed|
        exportlinks|
        fileextension|
        filesize|
        foldercolorrgb|
        fullfileextension|
        hasaugmentedpermissions|
        hasthumbnail|
        headrevisionid|
        iconlink|
        id|
        imagemediametadata|
        inheritedpermissionsdisabled|
        isappauthorized|
        labelinfo|
        <DriveLabelInfoSubfieldName>|
        labels|
        <DriveLabelsSubfieldName>|
        lastmodifyinguser|
        <DriveLastModifyingUserSubfieldName>|
        lastmodifyingusername|
        lastviewedbyme|lastviewedbymedate|lastviewedbymetime|lastviewedbyuser|
        linksharemetadata|
        md5|md5checksum|md5sum|
        mime|mimetype|
        modifiedbyme|modifiedbymedate|modifiedbymetime|modifiedbyuser|
        modifieddate|modifiedtime|
        name|
        originalfilename|
        ownedbyme|
        ownernames|
        owners|
        <DriveOwnersSubfieldName>|
        parents|
        <DriveParentsSubfieldName>|
        permissionids|
        permissiondetails|
        permissions|
        <DrivePermissionsSubfieldName>|
        properties|
        quotabytesused|quotaused|
        resourcekey|
        restricted|
        shareable|
        shared|
        sharedwithmedate|sharedwithmetime|
        sharinguser|
        <DriveSharingUserSubfieldName>|
        shortcutdetails|
        <DriveShortcutDetailsSubfieldName>|
        sha1checksum|
        sha256checksum|
        size|
        spaces|
        starred|
        teamdriveid|
        teamdrivename|
        thumbnaillink|
        thumbnailversion|
        title|
        trashed|
        trasheddate|trashedtime|
        trashinguser|
        <DriveTrashingUserSubfieldName>|
        userpermission|
        version|
        videomediametadata|
        viewed|
        viewedbymedate|viewedbymetime|
        viewerscancopycontent|
        webcontentlink|
        webviewlink|
        writerscanshare
<DriveFieldNameList> ::= "<DriveFieldName>(,<DriveFieldName>)*"
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
```
## Return Codes
When a command involves a query:
* If any files match the query, a return code of 0 is returned.
* If no files match the query, a return code of 60 is returned.

### Examples
You want to test for the existance of a Google drive folder:
```
$ gam user user1@domain.com show fileinfo query "name = 'Top Folder' and mimeType ='application/vnd.google-apps.folder'" id
Getting all Drive Files/Folders that match query (name = 'Top Folder' and mimeType ='application/vnd.google-apps.folder') for user1@domain.com
Got 1 Drive File/Folder that matched query (name = 'Top Folder' and mimeType ='application/vnd.google-apps.folder') for user1@domain.com...
User: user1@domain.com, Show 1 Drive File/Folder
  Drive Folder: Top Folder (1kdHaDm2XOmGKVsyBgPBugWqdE3xTwxyz)
    id: 1kdHaDm2XOmGKVsyBgPBugWqdE3xTwxyz
$ echo $?
0
$ gam user user2@domain.com show fileinfo query "name = 'Top Folder' and mimeType ='application/vnd.google-apps.folder'" id
Getting all Drive Files/Folders that match query (name = 'Top Folder' and mimeType ='application/vnd.google-apps.folder') for user2@domain.com
Got 0 Drive Files/Folders that matched query (name = 'Top Folder' and mimeType ='application/vnd.google-apps.folder') for user2@domain.com...
User: user2@domain.com, Show 0 Drive Files/Folders
$ echo $?
60
```

## File size fields
The Drive API defines two fields that relate to file size: `quotaBytesUsed` and `size`.
```
quotaBytesUsed - The number of storage quota bytes used by the file.
    This includes the head revision as well as previous revisions with keepForever enabled.
size - Size in bytes of blobs and first party editor files.
```
Previously, GAM used the `size` field when totaling file sizes, it now uses the `quotaBytesUsed` field.
The option `sizefield quotabytesused|size` allows you to select which field to use.

For most MIME types, the values are the same; for the following MIME types, `quotabytesused` is larger.
```
application/pdf
application/vnd.ms-powerpoint
application/vnd.openxmlformats-officedocument.presentationml.presentation
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
application/vnd.openxmlformats-officedocument.wordprocessingml.document
application/zip
audio/mpeg
image/jpeg
image/png
```

## Display file information
Display file details in indented keyword: value format. The two forms are equivalent.
```
gam <UserTypeEntity> show fileinfo <DriveFileEntity>
        [returnidonly]
        [filepath|fullpath] [folderpathonly [<Boolean>]] [pathdelimiter <Character>]
        [allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [showdrivename] [showshareddrivepermissions]
        [(showlabels details|ids)|(includelabels <ClassificationLabelIDList>)]
        [showparentsidsaslist] [followshortcuts [<Boolean>]]
        [stripcrsfromname]
        [formatjson]
gam <UserTypeEntity> info drivefile <DriveFileEntity>
        [returnidonly]
        [filepath|fullpath] [folderpathonly [<Boolean>]] [pathdelimiter <Character>]
        [allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [showdrivename] [showshareddrivepermissions]
        [(showlabels details|ids)|(includelabels <ClassificationLabelIDList>)]
        [showparentsidsaslist] [followshortcuts [<Boolean>]]
        [stripcrsfromname]
        [formatjson]
```
Use `returnidonly` to display just the file ID of the files in `<DriveFileEntity>`.

Use `filepath` to display the path(s) to the files in `<DriveFileEntity>`.

Use `fullpath` to add additional path information indicating that a file is an Orphan or Shared with me.

By default, the path to a file includes the file name as the last element of the path.
Use `folderpathonly` to display only the folder names when displaying the path to a file. This folder only path
an be used in  `gam <UserTypeEntity> create drivefolderpath` to recreate the folder hierarchy.

By default, file path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

When `allfields` is specified (or no fields are specified), use `showdrivename` to display Shared(Team) Drive names.
An additional API call is required to get each Shared(Team) Drive name; the names are cached so there is only one additional
API call per Shared(Team) Drive.

When `allfields` is specified (or no fields are specified), use `showshareddrivepermissions` to display permissions
for `<DriveFileEntity>` when it is a shared drive file/folder. In this case, the Drive API returns the permission IDs
but not the permissions themselves so GAM makes an additional API call to get the permissions.

By default, when file parents are displayed, they are displayed in this form:
```
  parents:
    id: <DriveFileID>
      isRoot: <Boolean>
    id: <DriveFileID>
      isRoot: <Boolean>
    ...
```
The `showparentsidsaslist` option changes the output to this form:
```
  parentsIds: <DriveFileID> <DriveFileID> ...
```
There is no `isRoot` information displayed.

By default, no Drive Label information is displayed. Use the following options to display this information;
an API call per file is required to get the information.
* `showlabels details`
```
  labels:
    id: <ClassificationLabelID>
      revisionId: <Number>
    id: <ClassificationLabelID>
      revisionId: <Number>
```
* `showlabels ids`
```
  labelsIds: <ClassificationLabelID> <ClassificationLabelID> ...
```

Starting in version 6.27.02, you can get Drive label information without an extra API call
if you know the `<ClassificationLabelID>`s. Add `labelinfo` to your `fields` list and use `includelabels <ClassificationLabelIDList>`
to specify the Drive labels.
```
gam user user@domain.com show fileinfo <DriveFileEntity> fields id,name,mimetype,labelinfo includelabels "mRoha85IbwCRl490E00xGLvBsSbkwIiuZ6PRNNEbbFcb"
```

The `stripcrsfromname` option strips nulls, carriage returns and linefeeds from drive file names.
Use this option if you discover filenames containing these special characters; it is not common.

Starting in version 6.80.10, the option `followshortcuts [<Boolean>]` that when true and `<DriveFileEntity` is a shortcut,
causes GAM to display information about the target of the shortcut rather than the shortcut itself.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display file paths
```
gam <UserTypeEntity> show filepath <DriveFileEntity>
        [returnpathonly]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [stripcrsfromname]
        [folderpathonly [<Boolean>]] [fullpath] [pathdelimiter <Character>]
        [followshortcuts [<Boolean>]]
gam <UserTypeEntity> print filepath <DriveFileEntity> [todrive <ToDriveAttribute>*]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [stripcrsfromname] [oneitemperrow]
        [fullpath] [folderpathonly [<Boolean>]] [pathdelimiter <Character>]
        [followshortcuts [<Boolean>]]
```
Use `returnpathonly` to display just the file path of the files in `<DriveFileEntity>`.

Use `fullpath` to add additional path information indicating that a file is an Orphan or Shared with me.

By default, the path to a file includes the file name as the last element of the path.
Use `folderpathonly` to display only the folder names when displaying the path to a file. This folder only path
an be used in  `gam <UserTypeEntity> create drivefolderpath` to recreate the folder hierarchy.

By default, file path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

The `stripcrsfromname` option strips nulls, carriage returns and linefeeds from drive file names.
Use this option if you discover filenames containing these special characters; it is not common.

By default, when printing file paths, all paths for a file are displayed on the same row; use `oneitemperrow` to
have each file path displayed on a separate row.

Starting in version 6.80.10, the option `followshortcuts [<Boolean>]` that when true and `<DriveFileEntity` is a shortcut,
causes GAM to display path information for the target of the shortcut rather than the shortcut itself.

## Select files for Display file counts, list, tree
Most GAM commands that deal with files require a `<DriveFileEntity>` to be specified; the command
then processes those files. The `filecounts`, `filelist` and `filetree` commands don't process files, they just list them.
They offer more powerful methods to select the files to be displayed.

## File selection definitions
See: [Drive File Selection](Drive-File-Selection) for details of `<DriveFileNameEntity>`, `<DriveFileQueryShortcut>` and `<DriveFileEntity>`.
```
<DriveFileNameEntity> ::=
        (anyname <DriveFileName>) | (anyname:<DriveFileName>) |
        (anydrivefilename <DriveFileName>) | (anydrivefilename:<DriveFileName>) |
        (name <DriveFileName>) | (name:<DriveFileName>) |
        (drivefilename <DriveFileName>) | (drivefilename:<DriveFileName>) |
        (othername <DriveFileName>) | (othername:<DriveFileName>) |
        (otherdrivefilename <DriveFileName>) | (otherdrivefilename:<DriveFileName>)

<DriveFileQueryShortcut> ::=
        all_files |
        all_folders |
        all_forms |
        all_google_files |
        all_non_google_files |
        all_shortcuts |
        all_3p_shortcuts |
        all_items |
        my_docs |
        my_files |
        my_folders |
        my_forms |
        my_google_files |
        my_non_google_files |
        my_presentations |
        my_publishable_items |
        my_sheets |
        my_shortcuts |
        my_slides |
        my_3p_shortcuts |
        my_items |
        my_top_files |
        my_top_folders |
        my_top_items |
        others_files |
        others_folders |
        others_forms |
        others_google_files |
        others_non_google_files |
        others_shortcuts |
        others_3p_shortcuts |
        others_items |
        writable_files

<DriveFileEntity> ::=
        <DriveFileIDEntity> |
        <DriveFileNameEntity> |
        <DriveFileQueryEntity> |
        <DriveFileQueryShortcut> |
        root|mydrive |
        <SharedDriveIDEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveNameEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveFileNameEntity> |
        <SharedDriveFileQueryEntity> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector>) | <CSVDataSelector>)
```

## File selection defaults
By default, file selection starts with a query of "'me' in owners".
The sections below detail other methiods for selecting files.

## File selection by query
Select a subset of files by query.

This option is not available for `print|show filetree`.
```
((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>) (querytime<String> <Time>)*
```
* `query "xxx"` - ` and xxx` is appended to the current query; you can repeat the query argument to build up a longer query.
* `fullquery "xxx"` - The query is set to `xxx` eliminating the initial `'me' in owners`.
* `<DriveFileQueryShortcut>` - Predefined queries

Use the `querytime<String> <Time>` option to allow times, usually relative, to be substituted into the `query <QueryDriveFile>` option.
The `querytime<String> <Time>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers. This is most useful in scripts
where you can specify a relative date without having to change the script.

For example, query for files last modified more than 5 years ago:
```
querytime5years -5y query "modifiedTime<'#querytime5years#'"
```

## File selection of Shared Drive
You can limit the selection for files on a specific Shared drive.
```
select <SharedDriveEntity>
```

To apply a query to that Shared Drive.
```
select <SharedDriveEntity> shareddrivequery "xxx"
```

## File selection by corpora
Select files by corpora.

This option is not available for `print|show filetree`.
```
corpora <CorporaAttribute>
```
* `corpora alldrives` - Selects files on Shared Drives and files owned by or shared to the user.
* `corpora domain` - Selects files shared to the user's domain.
* `corpora onlyteamdrives` - Selects files on Shared Drives.
* `corpora user` - Selects files owned by or shared to the user.

## File selection by ownership
By default, files owned by the user are selected. These options update the current query with the desired ownership.
```
anyowner|(showownedby any|me|others)

```
* `showownedby me` - Select files owned by the user; this is the default
* `showownedby any` or `anyowner` - Select files accessible by the user
* `showownedby others` - Select files not owned by the user

## File selection by MIME type
By default, all types of files and folders are selected. You can specify a list of MIME types to display or a list of MIME types to suppress.
This option updates the current query.
```
showmimetype [not] <MimeTypeList>
showmimetype category <MimeTypeNameList>
```
* `showmimetype <MimeTypeList>` - Select files and folders with the specified MIME types
* `showmimetype not <MimeTypeList>` - Select files and folders with MIME types other than those specified
* `showmimetype category <MimeTypeNameList>` - Select files and folders with the specified MIME type categories

## File selection by file size
These options would typically be used with `showmimetype` to select files of a particular type. This
selection is performed by GAM, not the API.

* `minimumfilesize <Integer>` - Limit the selection to files with content of size >= `<Integer>`
* `maximumfilesize <Integer>` - Limit the selection to files with content of size <= `<Integer>`

## File selection by file name pattern matching
This option allows you to limit the display to files whose name matches `<REMatchPattern>`.
The Drive API supports basic file name selection via query; this selection by pattern matching
is performed by GAM. You could use a query to do broad file name matching and then fine tune it with
`filenamematchpattern`.
```
filenamematchpattern <REMatchPattern>
```

## File selection by permission matching
See: [Permission Matches](Permission-Matches)

## File selection to exclude items in the trash
This option excludes items in the trash from being selected.
```
excludetrashed
```

## Display file counts
Print or show file counts by MIME type and/or file name.
```
gam <UserTypeEntity> print filecounts [todrive <ToDriveAttribute>*]
        [((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>)
            (querytime<String> <Time>)*]
        [continueoninvalidquery [<Boolean>]]
        [corpora <CorporaAttribute>]
        [select <SharedDriveEntity>]
        [anyowner|(showownedby any|me|others)]
        [showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
        [sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
        [filenamematchpattern <REMatchPattern>]
        <PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
        [excludetrashed]
        [showsize] [showmimetypesize]
        [showlastmodification] [pathdelimiter <Character>]
        (addcsvdata <FieldName> <String>)*
        [summary none|only|plus] [summaryuser <String>]
gam <UserTypeEntity> show filecounts
        [((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>)
            (querytime<String> <Time>)*]
        [continueoninvalidquery [<Boolean>]]
        [corpora <CorporaAttribute>]
        [select <SharedDriveEntity>]
        [anyowner|(showownedby any|me|others)]
        [showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
        [sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
        [filenamematchpattern <REMatchPattern>]
        <PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
        [excludetrashed]
        [showsize] [showmimetypesize]
        [showlastmodification] [pathdelimiter <Character>]
        [summary none|only|plus] [summaryuser <String>]
```

By default, print filecounts displays counts of all files owned by the specified [`<UserTypeEntity>`](Collections-of-Users).

The option `continueoninvalidquery [<Boolean>] can be used in special cases where a query of the form
`query "'labels/mRoha85IbwCRl490E00xGLvBsSbkwIiuZ6PRNNEbwxyz' in labels" causes Google to issue an error
saying that the query is invalid when, in fact, it is but the user does not have a license that suppprts drive file labels.
When `continueoninvalidquery` is true, GAM prints an error message and proceeds to the next user rather that terminating
as it does now. Of course, if the query really is invalid, you will get the message for every user.

The `showsize` option displays the total size (in bytes) of the files counted.

The `showmimetypesize` option displays the total size (in bytes) of each MIME type counted.

The option `showlastmodification` displays the following fields:
`lastModifiedFileId,lastModifiedFileName,lastModifiedFileMimeType,lastModifiedFilePath,lastModifyingUser,lastModifiedTime`;
these are for the most recently modified file.

For print filecouts, add additional columns of data from the command line to the output:
* `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

See [Select files for Display file counts, list, tree](#select-files-for-display-file-counts-list-tree)

Use the `excludetrashed` option to suppress counting files in the trash.

By default, file counts for individual users are displayed; the `summary` option offers alternatives
that can display a summarization of file counts across all users specified in the command.
* `none` - No summary is displayed; this is the default
* `only` - Only the summary is displayed, no individual user file counts are displayed
* `plus` - The summary is displayed in addition to the individual user file counts

The `summaryuser <String>` option  replaces the default summary user `Summary` with `<String>`.

### Examples
Show file counts for a user.
```
$ gam user testuser@domain.com show filecounts showsize
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 261 Drive Files/Folders that matched query ('me' in owners) for testuser@domain.com...
User: testuser@domain.com, Drive Files/Folders: 261, Size: 13822521
  application/octet-stream: 8
  application/pdf: 1
  application/vnd.google-apps.document: 98
  application/vnd.google-apps.drawing: 2
  application/vnd.google-apps.drive-sdk.423565144751: 1
  application/vnd.google-apps.folder: 68
  application/vnd.google-apps.form: 3
  application/vnd.google-apps.jam: 1
  application/vnd.google-apps.presentation: 1
  application/vnd.google-apps.shortcut: 14
  application/vnd.google-apps.site: 1
  application/vnd.google-apps.spreadsheet: 24
  application/vnd.openxmlformats-officedocument.spreadsheetml.sheet: 1
  application/vnd.openxmlformats-officedocument.wordprocessingml.document: 3
  application/vnd.openxmlformats-officedocument.wordprocessingml.template: 1
  application/x-gzip: 4
  application/zip: 2
  image/jpeg: 8
  image/vnd.adobe.photoshop: 1
  text/csv: 2
  text/plain: 13
  text/rtf: 3
  text/x-sh: 1
```
Show file counts for a user including sizes for each MIME type.
```
$ gam user testuser@domain.com show filecounts showmimetypesize
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 261 Drive Files/Folders that matched query ('me' in owners) for testuser@domain.com...
User: testuser@domain.com, Drive Files/Folders: 261, Size: 13822521
  application/octet-stream: 8, 17
  application/pdf: 1, 9879
  application/vnd.google-apps.document: 98, 52858
  application/vnd.google-apps.drawing: 2, 2048
  application/vnd.google-apps.drive-sdk.423565144751: 1, 0
  application/vnd.google-apps.folder: 68, 0
  application/vnd.google-apps.form: 3, 0
  application/vnd.google-apps.jam: 1, 1024
  application/vnd.google-apps.presentation: 1, 0
  application/vnd.google-apps.shortcut: 14, 0
  application/vnd.google-apps.site: 1, 0
  application/vnd.google-apps.spreadsheet: 24, 11264
  application/vnd.openxmlformats-officedocument.spreadsheetml.sheet: 1, 8157
  application/vnd.openxmlformats-officedocument.wordprocessingml.document: 3, 34407
  application/vnd.openxmlformats-officedocument.wordprocessingml.template: 1, 25906
  application/x-gzip: 4, 2768
  application/zip: 2, 765
  image/jpeg: 8, 16498
  image/vnd.adobe.photoshop: 1, 13613198
  text/csv: 2, 397
  text/plain: 13, 41461
  text/rtf: 3, 1738
  text/x-sh: 1, 136
```
Print file counts for a user.
```
$ gam user testuser@domain.com print filecounts showsize
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 261 Drive Files/Folders that matched query ('me' in owners) for testuser@domain.com...
User,Total,Size,application/octet-stream,application/pdf,application/vnd.google-apps.document,application/vnd.google-apps.drawing,application/vnd.google-apps.drive-sdk.423565144751,application/vnd.google-apps.folder,application/vnd.google-apps.form,application/vnd.google-apps.jam,application/vnd.google-apps.presentation,application/vnd.google-apps.shortcut,application/vnd.google-apps.site,application/vnd.google-apps.spreadsheet,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.wordprocessingml.template,application/x-gzip,application/zip,image/jpeg,image/vnd.adobe.photoshop,text/csv,text/plain,text/rtf,text/x-sh
testuser@domain.com,261,13822521,8,1,98,2,1,68,3,1,1,14,1,24,1,3,1,4,2,8,1,2,13,3,1
```
Print file counts for a user including sizes for each MIME type.
```
$ gam user testuser@domain.com print filecounts showmimetypesize
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 261 Drive Files/Folders that matched query ('me' in owners) for testuser@domain.com...
User,Total,Size,application/octet-stream,application/octet-stream-size,application/pdf,application/pdf-size,application/vnd.google-apps.document,application/vnd.google-apps.document-size,application/vnd.google-apps.drawing,application/vnd.google-apps.drawing-size,application/vnd.google-apps.drive-sdk.423565144751,application/vnd.google-apps.drive-sdk.423565144751-size,application/vnd.google-apps.folder,application/vnd.google-apps.folder-size,application/vnd.google-apps.form,application/vnd.google-apps.form-size,application/vnd.google-apps.jam,application/vnd.google-apps.jam-size,application/vnd.google-apps.presentation,application/vnd.google-apps.presentation-size,application/vnd.google-apps.shortcut,application/vnd.google-apps.shortcut-size,application/vnd.google-apps.site,application/vnd.google-apps.site-size,application/vnd.google-apps.spreadsheet,application/vnd.google-apps.spreadsheet-size,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet-size,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.wordprocessingml.document-size,application/vnd.openxmlformats-officedocument.wordprocessingml.template,application/vnd.openxmlformats-officedocument.wordprocessingml.template-size,application/x-gzip,application/x-gzip-size,application/zip,application/zip-size,image/jpeg,image/jpeg-size,image/vnd.adobe.photoshop,image/vnd.adobe.photoshop-size,text/csv,text/csv-size,text/plain,text/plain-size,text/rtf,text/rtf-size,text/x-sh,text/x-sh-size
testuser@domain.com,261,13822521,8,17,1,9879,98,52858,2,2048,1,0,68,0,3,0,1,1024,1,0,14,0,1,0,24,11264,1,8157,3,34407,1,25906,4,2768,2,765,8,16498,1,13613198,2,397,13,41461,3,1738,1,136
```
Print file counts for a Shared Drive
```
$ gam user testuser@domain.com print filecounts select <SharedDriveID> showsize
Getting all Drive Files/Folders for testuser@domain.com
Got 261 Drive Files/Folders for testuser@domain.com...
User,id,name,Total,Size,Item cap,application/octet-stream,application/pdf,application/vnd.google-apps.document,application/vnd.google-apps.drawing,application/vnd.google-apps.drive-sdk.423565144751,application/vnd.google-apps.folder,application/vnd.google-apps.form,application/vnd.google-apps.jam,application/vnd.google-apps.presentation,application/vnd.google-apps.shortcut,application/vnd.google-apps.site,application/vnd.google-apps.spreadsheet,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.wordprocessingml.template,application/x-gzip,application/zip,image/jpeg,image/vnd.adobe.photoshop,text/csv,text/plain,text/rtf,text/x-sh
testuser@domain.com,0AMzwfhFBpwLHUkWXYZ,Shared Drive Name,261,13822521,3.45%,8,1,98,2,1,68,3,1,1,14,1,24,1,3,1,4,2,8,1,2,13,3,1
```
Get file count summaries by OU; top level selector is ou, sub level selectors are ou_and_children
```
gam redirect csv ./TopLevelOUs.csv print ous showparent toplevelonly parentselector ou childselector ou_and_children fields orgunitpath
gam redirect csv ./FileCounts.csv multiprocess csv ./TopLevelOUs.csv gam "~orgUnitSelector" "~orgUnitPath" print filecounts excludetrashed summary only summaryuser "~orgUnitPath"
```

## Display file share counts
Print or show the share type counts of a user's files. These fields are displayed:
* Owner - The file owner
* Total - Total number of files
* Shared - Number of files shared
* Shared External - Number of files shared externally
* Shared Internal - Number of files shared internally
* anyone - Number of ACLs of type anyone, allowFileDiscovery = True
* anyoneWithLink - Number of ACLs of type anyone, allowFileDiscovery = False
* externalDomain - Number of ACLs of type domain, external domains, allowFileDiscovery = True
* externalDomainWithLink - Number of ACLs of type domain, external domains,  allowFileDiscovery = False
* internalDomain - Number of ACLs of type domain, internal domains, allowFileDiscovery = True
* internalDomainWithLink - Number of ACLs of type domain, internal domains, allowFileDiscovery = False
* externalGroup - Number of ACLs of type group, external domains
* internalGroup - Number of ACLs of type group, internal domains
* externalUser - Number of ACLs of type user, external domains
* internalUser - Number of ACLs of type user, internal domains
* deletedGroup - Number of ACLs to a deleted group
* deletedUser - Number of ACLs to a deleted user
```
gam <UserTypeEntity> print filesharecounts [todrive <ToDriveAttribute>*]
        [excludetrashed]
        [internaldomains <DomainNameList>]
        [summary none|only|plus] [summaryuser <String>]
gam <UserTypeEntity> show filesharecounts
        [excludetrashed]
        [internaldomains <DomainNameList>]
        [summary none|only|plus] [summaryuser <String>]
```

By default, print|show filesharecounts displays share type counts of all files owned by the specified `<UserTypeEntity>`.

Use the `excludetrashed` option to suppress counting files in the trash.

By default, `internaldomains <DomainNameList>` defaults to your primary domain; if you have other domains that
you consider internal, list all of them in `<DomainNameList>`.

By default, share type counts for individual users are displayed; the `summary` option offers alternatives
that can display a summarization of share type counts across all users specified in the command.
* `none` - No summary is displayed; this is the default
* `only` - Only the summary is displayed, no individual user share type counts are displayed
* `plus` - The summary is displayed in addition to the individual user share type counts

The `summaryuser <String>` option  replaces the default summary user `Summary` with `<String>`.

### Example
```
$ gam users testuser0,testuser1 show filesharecounts
Getting all Drive Files/Folders that match query ('me' in owners) for testuser0@domain.com (1/2)
Got 100 Drive Files/Folders that matched query ('me' in owners) for testuser0@domain.com...
Got 200 Drive Files/Folders that matched query ('me' in owners) for testuser0@domain.com...
Got 251 Drive Files/Folders that matched query ('me' in owners) for testuser0@domain.com...
User: testuser0@domain.com, Drive File/Folder: 251 (1/2)
  Total: 251
  Shared: 124
  Shared External: 27
  Shared Internal: 114
  anyone: 2
  anyoneWithLink: 7
  externalDomain: 1
  externalDomainWithLink: 2
  internalDomain: 1
  internalDomainWithLink: 8
  externalGroup: 1
  internalGroup: 5
  externalUser: 17
  internalUser: 167
  deletedGroup: 0
  deletedUser: 0
Getting all Drive Files/Folders that match query ('me' in owners) for testuser1@domain.com (2/2)
Got 100 Drive Files/Folders that matched query ('me' in owners) for testuser1@domain.com...
Got 186 Drive Files/Folders that matched query ('me' in owners) for testuser1@domain.com...
User: testuser1@domain.com, Drive File/Folder: 186 (2/2)
  Total: 186
  Shared: 85
  Shared External: 27
  Shared Internal: 72
  anyone: 2
  anyoneWithLink: 5
  externalDomain: 0
  externalDomainWithLink: 1
  internalDomain: 4
  internalDomainWithLink: 37
  externalGroup: 0
  internalGroup: 14
  externalUser: 20
  internalUser: 44
  deletedGroup: 0
  deletedUser: 0

$ gam users testuser0,testuser1 print filesharecounts summary plus
Getting all Drive Files/Folders that match query ('me' in owners) for testuser0@domain.com (1/2)
Got 100 Drive Files/Folders that matched query ('me' in owners) for testuser0@domain.com...
Got 200 Drive Files/Folders that matched query ('me' in owners) for testuser0@domain.com...
Got 251 Drive Files/Folders that matched query ('me' in owners) for testuser0@domain.com...
Getting all Drive Files/Folders that match query ('me' in owners) for testuser1@domain.com (2/2)
Got 100 Drive Files/Folders that matched query ('me' in owners) for testuser1@domain.com...
Got 186 Drive Files/Folders that matched query ('me' in owners) for testuser1@domain.com...
Owner,Total,Shared,Shared External,Shared Internal,anyone,anyoneWithLink,externalDomain,externalDomainWithLink,internalDomain,internalDomainWithLink,externalGroup,internalGroup,externalUser,internalUser,deletedGroup,deletedUser
testuser0@domain.com,251,124,27,114,2,7,1,2,1,8,1,5,17,167,0,0
testuser1@domain.com,186,85,27,72,2,5,0,1,4,37,0,14,20,44,0,0
Summary,437,209,54,186,4,12,1,3,5,45,1,19,37,211,0,0
```

## Display file tree
Display a list of file/folder names indented to show structure.
```
<FileTreeFieldName> ::=
        explicitlytrashed|
        filesize|
        id|
        mimetype|
        owners|
        parents|
        size|
        trashed|
        webviewlink
<FileTreeFieldNameList> ::= "<FileTreeFieldName>(,<FileTreeFieldName>)*"

gam <UserTypeEntity> print filetree [todrive <ToDriveAttribute>*]
        [select <DriveFileEntity> [selectsubquery <QueryDriveFile>]
            [depth <Number>]]
        [anyowner|(showownedby any|me|others)]
        [showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
        [sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
        [filenamematchpattern <REMatchPattern>]
        <PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
        [excludetrashed]
        [fields <FileTreeFieldNameList>]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])* [delimiter <Character>]
        [noindent] [stripcrsfromname]
gam <UserTypeEntity> show filetree
        [select <DriveFileEntity> [selectsubquery <QueryDriveFile>]
            [depth <Number>]]
        [anyowner|(showownedby any|me|others)]
        [showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
        [sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
        [filenamematchpattern <REMatchPattern>]
        <PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
        [excludetrashed]
        [fields <FileTreeFieldNameList>]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])* [delimiter <Character>]
        [stripcrsfromname]
```
By default, the file tree starting at the root and all orphans are shown.

See [Select files for Display file counts, list, tree](#select-files-for-display-file-counts-list-tree)

## File selection starting point for Display file tree
You can specify a specific folder from which to select files.
```
        [select <DriveFileEntity> [selectsubquery <QueryDriveFile>]
            [depth <Number>]]
```
* `select <DriveFileEntity>` - All files in the selected folder and below are shown.
* `selectsubquery <QueryDriveFile>` - Only the files in the selected folder that match the query are shown.

The `depth <Number>` argument controls which files or folders within a selected folder are listed.
* `depth -1` - all files and folders in the selected folder and below are listed; this is the default.
* `depth 0` - the files or folders within a selected folder are listed, no descendants are listed.
* `depth N` - the files and folders within the selected folder and those files and folders N levels below the selected folder are listed.

## Choose what fields to display
By default, only the file/folder name is displayed; use the following options to display additional fields.
* `fields <FileTreeFieldNameList>` - Display the selected fields.
* `delimiter <Character>` - If any field has multiple values, separate them with `<Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.

For fields `explicitlytrashed` and `trashed`, only True values are shown with `show filetree`; True and False values are shown with `print filetree`.

For `print filetree`, use the `noindent` option to eliminate the indentation in front of the file name.

The `stripcrsfromname` option strips nulls, carriage returns and linefeeds from drive file names.
This option is special purpose and will not generally be used.

### Examples
Show full file tree including the file id and MIME type:
```
gam user testuser show filetree fields id,mimetype
```
Show file tree starting at the folder named "Middle Folder" and 2 levels deeper
```
gam user testuser show filetree select drivefilename "Middle Folder" depth 2
```
## Display file parent tree
Print the parent tree of file/folder.
```
gam <UserTypeEntity> print fileparenttree <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [stripcrsfromname]
```
### Examples
```
# My Drive file
$ gam user user@domain.com print fileparenttree 1tDGtnaBXc1qx_9NjBSZOUUNZ7FoRc2u6
User: user@domain.com, Print 1 File Parent Tree
Owner,id,name,parentId,depth,isRoot
user@domain.com,1tDGtnaBXc1qx_9NjBSZOUUNZ7FoRc2u6,Bottom Folder,1HvAJtmQ2KZrKJhzY8aeZVScHhZ3HBJLp,4,False
user@domain.com,1HvAJtmQ2KZrKJhzY8aeZVScHhZ3HBJLp,Middle Folder,1CVqOJJLNQtxX4QEPdpDfbkjiq1oUsxne,3,False
user@domain.com,1CVqOJJLNQtxX4QEPdpDfbkjiq1oUsxne,TopCopy,0AHYenC8f12ALUk9PVA,2,False
user@domain.com,0AHYenC8f12ALUk9PVA,My Drive,,1,True

# Shared Drive file
$ gam user user@domain.com print fileparenttree 1kAHa7Q801KXRF1DfoofNlW05UWDzddhVP_u_L2xGfFQ
User: user@domain.com, Print 1 File Parent Tree
Owner,id,name,parentId,depth,isRoot
user@domain.com,1kAHa7Q801KXRF1DfoofNlW05UWDzddhVP_u_L2xGfFQ,Middle Doc,1DShPJ6iG1TnNsgiBn-Oy1OVE2BahYlPr,4,False
user@domain.com,1DShPJ6iG1TnNsgiBn-Oy1OVE2BahYlPr,Middle Folder,1s3g64uWfuQrpXRPf82B-bWCB5VuyrOmQ,3,False
user@domain.com,1s3g64uWfuQrpXRPf82B-bWCB5VuyrOmQ,Top Folder,0AL5LiIe4dqxZUk9PVA,2,False
user@domain.com,0AL5LiIe4dqxZUk9PVA,TS Shared Drive 1,,1,True

# Shared with Me file
$ gam user user@domain.com print fileparenttree 1S2D97pyG1vAil4hgNnGGLD2ldCwTOzXUM9D7XbeUv0s
User: user@domain.com, Print 1 File Parent Tree
Owner,id,name,parentId,depth,isRoot
user@domain.com,1S2D97pyG1vAil4hgNnGGLD2ldCwTOzXUM9D7XbeUv0s,GooGoo,0B0NlVEBUkz-hfjVudlF4VHlYYWlmOEdCUUxDaHdLdXhJTF84YWQwbmpRWmZ3Qm0wZnpHSGs,2,False
user@domain.com,0B0NlVEBUkz-hfjVudlF4VHlYYWlmOEdCUUxDaHdLdXhJTF84YWQwbmpRWmZ3Qm0wZnpHSGs,FooBar,,1,False
```

## Display file list
Display a list of file/folder details in CSV format.
```
gam <UserTypeEntity> print|show filelist [todrive <ToDriveAttribute>*]
        [((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>)
            (querytime<String> <Time>)*]
        [continueoninvalidquery [<Boolean>]]
        [choose <DriveFileNameEntity>|<DriveFileEntityShortcut>]
        [corpora <CorporaAttribute>]
        [select <DriveFileEntity> [selectsubquery <QueryDriveFile>]
            [(norecursion [<Boolean>])|(depth <Number>)] [showparent]]
        [anyowner|(showownedby any|me|others)]
        [showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>] [mimetypeinquery [<Boolean>]]
        [sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
        [filenamematchpattern <REMatchPattern>]
        <PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>] [pmfilter] [oneitemperrow]
        [excludetrashed]
        [maxfiles <Integer>] [nodataheaders <String>]
        [countsonly [summary none|only|plus] [summaryuser <String>]
                    [showsource] [showsize] [showmimetypesize]]
        [countsrowfilter]
        [filepath|fullpath [folderpathonly [<Boolean>]] [pathdelimiter <Character>] [addpathstojson] [showdepth]] [buildtree]
        [allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)]
        [showdrivename] [showshareddrivepermissions]
        [(showlabels details|ids)|(includelabels <ClassificationLabelIDList>)]
        [showparentsidsaslist] [showpermissionslast]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])* [delimiter <Character>]
        [stripcrsfromname]
        (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
By default, `print filelist` displays all files owned by the specified [`<UserTypeEntity>`](https://github.com/GAM-team/GAM/wiki/Collections-of-Users)

The option `continueoninvalidquery [<Boolean>] can be used in special cases where a query  of the form
`query "'labels/mRoha85IbwCRl490E00xGLvBsSbkwIiuZ6PRNNEbwxyz' in labels" causes Google to issue an error
saying that the query is invalid when, in fact, it is but the user does not have a license that suppprts drive file labels.
When `continueoninvalidquery` is true, GAM prints an error message and proceeds to the next user rather that terminating
as it does now. Of course, if the query really is invalid, you will get the message for every user.

When `allfields` is specified (or no fields are specified), use `showshareddrivepermissions` to display permissions
when shared drives are queried/selected. In this case, the Drive API returns the permission IDs
but not the permissions themselves so GAM makes an additional API call per file to get the permissions.

By default, when `showimimetype` and `filepath|fullpath`are both specified, GAM locally filters files by MimeType;
this may be slow if the user has a large number of files. Adding the option `mimetypeinquery` or `mimetypeinquery true`
causes GAM to have Google filter files by MimeType; this will increase performance.

See [Select files for Display file counts, list, tree](#select-files-for-display-file-counts-list-tree)

## File selection by name and entity shortcuts for Display file list
Select a subset of files by pre-defined queries.

These options define a complete query, eliminating the initial "`me` in owners".
```
<DriveFileNameEntity> ::=
        (anyname <DriveFileName>) | (anyname:<DriveFileName>) |
        (anydrivefilename <DriveFileName>) | (anydrivefilename:<DriveFileName>) |
        (name <DriveFileName>) | (name:<DriveFileName>) |
        (drivefilename <DriveFileName>) | (drivefilename:<DriveFileName>) |
        (othername <DriveFileName>) | (othername:<DriveFileName>) |
        (otherdrivefilename <DriveFileName>) | (otherdrivefilename:<DriveFileName>)

<DriveFileEntityShortcut> ::=
        alldrives |
        mydrive |
        mydrive_any |
        mydrive_me |
        mydrive_others |
        mydrive_with_orphans |
        onlyteamdrives|onlyshareddrives |
        orphans |
        ownedby_any |
        ownedby_me |
        ownedby_others |
        root |
        root_with_orphans |
        sharedwithme |
        sharedwithme_mydrive |
        sharedwithme_notmydrive

choose <DriveFileNameEntity>|<DriveFileEntityShortcut>
```
Definition of `<DriveFileEntityShortcut>`:
* `alldrives` - All files accessible by the user; `My Drive` including orphans, `Shared with me`, `Shared drives`
* `mydrive` - All files in `My Drive` excluding orphans; ownership controlled by `showownedby`
* `mydrive_any` - All files in `My Drive` including orphans owned by anyone
* `mydrive_me` - All files in `My Drive` including orphans owned by the user; `'me' in owners`
* `mydrive_others` - All files in `My Drive` excluding orphans owned by others; `not 'me' in owners`
* `mydrive_with_orphans` - All files in `My Drive` including orphans; ownership controlled by `showownedby`
* `onlyshareddrives` - All files in `Shared drives` accessible by the user
* `onlyteamdrives` - All files in `Shared drives` accessible by the user
* `orphans` - All files in `My Drive` whose parentage doesn't lead to `My Drive`; `'me' in owners`
* `ownedby_any` - All files in `My Drive` including orphans and `Shared with me` owned by anyone
* `ownedby_me` - All files in `My Drive` including orphans owned by the user; `'me' in owners`
* `ownedby_others` - All files in `My Drive` excluding orphans and `Shared with me` owned by others; `not 'me' in owners`
* `root` - All files in `My Drive` excluding orphans; ownership controlled by `showownedby`
* `root_with_orphans` - All files in `My Drive` including orphans; ownership controlled by `showownedby`
* `sharedwithme` - All files in `My Drive` and `Shared with me` owned by others; `not 'me' in owners`
* `sharedwithme_mydrive` - All files in `My Drive` owned by others; `not 'me' in owners`
* `sharedwithme_notmydrive` - All files in `Shared with me` but not in `My Drive`; `not 'me' in owners`

## File selection based on permission matching
Use the following option to select a subset of files based on their permissions.
* `<PermissionMatch>* [<PermissionMatchAction>]` - Use permission matching to select files

## File selection starting point for Display file list
You can limit the selection for files on a specific Shared drive.
Any query will be applied to the Shared drive.
```
select <SharedDriveEntity>
```

You can specify a specific folder from which to select files.
```
select <DriveFileEntity> [selectsubquery <QueryDriveFile>]
    [norecursion|(depth <Number>)] [showparent]
```
These options can be used instead of the query options to select a specific folder to display.
* `select <DriveFileEntity>` - All files in the selected folder and below are shown.
  * To select the root folder of My Drive, use its `<DriveFolderID>` obtained by `gam user <UserItem> show fileinfo root id`
    * `select <IDfrom Above>`
  * Starting in version 6.22.14, you can select the root folder of My Drive with `rootid`.
    * `select rootid`
* `selectsubquery <QueryDriveFile>` - Only the files in the selected folder that match the query are shown.

The `norecursion` and `depth <Number>` arguments control which files or folders within a selected folder are listed.
* `norecursion` or `norecursion true` - no files and folders in the selected folder and below are listed
* `depth -1` - all files and folders in the selected folder and below are listed; this is the default.
* `depth 0` - the files or folders within the selected folder are listed, no descendants are listed.
* `depth N` - the files and folders within the selected folder and those files and folders N levels below the selected folder are listed.

By default, when a folder is selected, only its contents are displayed.
* `showparent` - The selected folder is also displayed.

## Choose what fields to display
If no query or select is performed, use these options to get file path information:
* `filepath|fullpath` - For files and folders, display the full path(s) to them starting at the root (My Drive)
* `addpathstojson` - When this option and `formatjson` are specified, the path information will be included in the
JSON data rather than as additional columns
* `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output

When used with `filepath` or `fullpath`, `showdepth` will display a `depth` column.
Files/folders directly in `My Drive` are at depth 0, the depth increases by 1
for each containing folder.

If a query or select is performed, use these options to get file path information:
* `filepath` - For files, no path information is shown; for folders, the paths of all of its children are shown starting at the selected folder
* `fullpath` - For files and folders, display the full path(s) to them starting at the root (My Drive or Shared Drive)
* `addpathstojson` - When this option and `formatjson` are specified, the path information will be included in the
JSON data rather than as additional columns

By default, the path to a file includes the file name as the last element of the path.
Use `folderpathonly` to display only the folder names when displaying the path to a file. This folder only path
an be used in  `gam <UserTypeEntity> create drivefolderpath` to recreate the folder hierarchy.

By default, file path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

By default, only the fields `id` and `webViewLink` are displayed.
* `allfields` - Display all file fields
* `<DriveFieldName>*` - Select individual fields for display
* `fields <DriveFieldNameList>` - Select a list of fields for display
* `orderby <DriveFileOrderByFieldName> [ascending|descending])*` - Select the order in which the files are displayed
* `delimiter <Character>` - Specifiy the `<Character>` to separate items in the fields: `parentsIds, permissionIds, spaces`; the default value is `csv_output_field_delimiter` from `gam.cfg`.

When `allfields` is specified, use `showdrivename` to display Shared(Team) Drive names.
An additional API call is required to get each Shared(Team) Drive name; the names are cached so there is only one additional
API call per Shared(Team) Drive.

By default, when file parents are displayed, the columns displayed are:
```
...,parents,parents.0.id`,parents.0.isRoot,parents.1.id,parents.1.isRoot,...
```
The `parents` column indicates the number of parents a file has and there are discrete entries for each parent.

The `showparentsidsaslist` option changes the output to be only two columns:
```
...,parents,parentsIds,...
```
The `parents` column indicates the number of parents a file has and the `parentsIds` column is a list of the parent IDs
separated by `delimiter <Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.
There is no `isRoot` information displayed. This option allows you to reference all of a files parents with
`addparents <DriveFolderIDList>` or `removeparents <DriveFolderIDList>` wn updating a file.

By default, no Drive Label information is displayed. Use the following options to display this information;
an API call per file is required to get the information.
* `showlabels details`
The columns displayed are:
```
...labels,labels.0.id,labels.0.revisionId,labels.1.id,labels.1.revisionId,...
```
The `labels` column indicates the number of drive labels a file has and there are discrete entries for each label.

* `showlabels ids`
```
...labels,labelsIds,...
```
The `labels` column indicates the number of drive labels a file has and the `labelsIds` column is a list of the drive label IDs
separated by `delimiter <Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.

By default, all ACLS are displayed; use the following option in conjunction with `<PermissionMatch>* [<PermissionMatchAction>]`
to select a subset of files based on their permissions and to display only those permissions.
* `pmfilter` - Use permission matching to display a subset of the ACLs for each file

By default, all ACLs are displayed sorted with the other fields, the `showpermissionslast` option
causes GAM to display all `permissions` fields as the right-most columns in the CSV file. This option does not apply
when `formatjson` is specified.

By default, all ACLs are displayed with the other file fields on a single row.
* `oneitemperrow` - Display each of a files ACls on a separate row with all of the other file fields.
This produces a CSV file that can be used in subsequent commands without further script processing.

The `countsonly` option doesn't display any indididual file data, it lists the total number of files that the user can access
and the mumber of files by MIME type.

The `countsonly` suboption `summary none|only|plus` specifies display of a summarization of file counts across all users specified in the command.
* `none` - No summary is displayed; this is the default
* `only` - Only the summary is displayed, no individual user file counts are displayed
* `plus` - The summary is displayed in addition to the individual user file counts

The `summaryuser <String>` option  replaces the default summary user `Summary` with `<String>`.

The `countsonly` suboption `showsource` adds additional columns `Source` and `Name` that identify the top level folder ID and Name from which the counts are derived.

The `countsonly` suboption `showsize` adds an additional column `Size` that indicates the total size (in bytes) of the files represented on the row.

The `countsonly` suboption `showmimetypesize` adds additional columns `<MimeType>:Size` that indicate the total size (in bytes) of each MIME type.

By default, when `countsonly` is specified, GAM applies `config csv_output_row_filter` to the file details to select which files are counted.
Use the `countsrowfilter` option to have GAM to apply `config csv_output_row_filter` to the file counts rather than the file details.

The `stripcrsfromname` option strips nulls, carriage returns and linefeeds from drive file names.
This option is special purpose and will not generally be used.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Examples
List all files/folders owned by the user:
```
gam user testuser print filelist
```
List all files/folders owned by the user that begin with the word 'Test':
```
gam user testuser print filelist query "title contains 'Test'"
```
List all files/folders owned by any user that are starred and have been modified in the last year:
```
gam user testuser print filelist fullquery "starred = true and modifiedTime >= '#querytimelastyear#'" querytimelastyear -1y
```
List the file with the most recent modification date:
```
gam user testuser print filelist orderby modifiedtime descending maxfiles 1
```
List the file with the oldest modification date:
```
gam user testuser print filelist orderby modifiedtime ascending maxfiles 1
```
List all files/folders without a parent, owned by anyone, do not show their descendants:
```
gam user testuser print filelist select orphans showownedby any depth 0
```
List all files/folders and their descendents, owned by the user, in the folder 'Top Folder':
```
gam user testuser print filelist select drivefilename 'Top Folder' showownedby me
```
List all files whose name ends in ".exe" that are in the folder named "Folder Name" and its sub-folders:
```
gam user testuser print filelist select drivefilename "Folder Name" filenamematchpattern ".*\.exe"
```
If you only want files whose name ends in ".exe" that are directly in the folder named "Folder Name":
```
gam user testuser print filelist select drivefilename "Folder Name" depth 0 filenamematchpattern ".*\.exe"
```
List all Meet recordings older than 30 days.
```
gam user testuser print filelist select drivefilename "Meet Recordings" querytime30d -30d selectsubquery "modifiedTime<'#querytime30d#'"
```
List all files owned by the user and shared with others; i.e., files with ACLs with a role other than owner.
```
gam user testuser print filelist fields id,name,basicpermissions pm not role owner em
```
List all files owned by the user and shared with others; i.e., files with ACLs with a role other than owner.
Display a separate row for each ACL.
```
gam user testuser print filelist fields id,name,basicpermissions pm not role owner em onitemperrow
```
List all files owned by the user and shared with others; i.e., files with ACLs with a role other than owner.
Display a separate row for each ACL; only display the matching ACLS.
```
gam user testuser print filelist fields id,name,basicpermissions pm not role owner em onitemperrow pmfilter
```
List a user's shortcuts and information about the target files.
```
gam redirect csv ./TSShortcuts.csv user user@domain.com print filelist fields id,name,parents,shortcutdetails showmimetype gshortcut
Headers
Owner,id,name,parents,parents.0.id,parents.0.isRoot,shortcutDetails.targetId,shortcutDetails.targetMimeType

For each shortcut, get the target file information; add the shortcut id, name and parent to the output
gam redirect csv ./TSShortcutFiles.csv multiprocess csv ./TSShortcuts.csv gam user user@domain.com print filelist select "~shortcutDetails.targetId" norecursion showownedby any
    fields id,name,mimetype,parents,owners.emailaddress addcsvdata shortcut.id "~id" addcsvdata shortcut.name "~name" addcsvdata shortcut.parents "~parents.0.id"
Headers
Owner,id,name,mimeType,owners,owners.0.emailAddress,parents,parents.0.id,parents.0.isRoot,shortcut.id,shortcut.name,shortcut.parents
```

### Examples using csv_output_row_filter
Display file counts for users with files of size greater that 100MB, `csv_output_row_filter`
is applied to the file details.
```
gam config csv_output_row_filter "size:count>100000000" all users print filelist countsonly fields size
```
Display file counts for users with more than 100 `video/mp4` files, `csv_output_row_filter`
is applied to the file counts.
```
gam config csv_output_row_filter "video/mp4:count>100" csv_output_header_filter "Owner,video/mp4" all users print filelist countsonly countsrowfilter
```

### Examples showing file paths
All files, no file path
```
$ gam user testuser print filelist title
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 11 Drive Files/Folders for testuser@domain.com...
Owner,title
testuser@domain.com,Bottom Sheet 12
testuser@domain.com,Bottom Sheet 11
testuser@domain.com,Bottom Doc 22
testuser@domain.com,Bottom Doc 21
testuser@domain.com,Bottom Folder 22
testuser@domain.com,Bottom Folder 21
testuser@domain.com,Bottom Folder 12
testuser@domain.com,Bottom Folder 11
testuser@domain.com,Middle Folder 2
testuser@domain.com,Middle Folder 1
testuser@domain.com,Top Folder
```
No `select` or `query`, `filepath` and `fullpath` give same result
```
$ gam user testuser print filelist title filepath
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 11 Drive Files/Folders for testuser@domain.com...
Owner,title,paths,path.0
testuser@domain.com,Bottom Sheet 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12/Bottom Sheet 12
testuser@domain.com,Bottom Sheet 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11/Bottom Sheet 11
testuser@domain.com,Bottom Doc 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22/Bottom Doc 22
testuser@domain.com,Bottom Doc 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21/Bottom Doc 21
testuser@domain.com,Bottom Folder 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22
testuser@domain.com,Bottom Folder 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21
testuser@domain.com,Bottom Folder 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12
testuser@domain.com,Bottom Folder 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11
testuser@domain.com,Middle Folder 2,1,My Drive/Top Folder/Middle Folder 2
testuser@domain.com,Middle Folder 1,1,My Drive/Top Folder/Middle Folder 1
testuser@domain.com,Top Folder,1,My Drive/Top Folder

$ gam user testuser print filelist title fullpath
Getting all Drive Files/Folders that match query ('me' in owners) for testuser@domain.com
Got 11 Drive Files/Folders for testuser@domain.com...
Owner,title,paths,path.0
testuser@domain.com,Bottom Sheet 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12/Bottom Sheet 12
testuser@domain.com,Bottom Sheet 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11/Bottom Sheet 11
testuser@domain.com,Bottom Doc 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22/Bottom Doc 22
testuser@domain.com,Bottom Doc 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21/Bottom Doc 21
testuser@domain.com,Bottom Folder 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22
testuser@domain.com,Bottom Folder 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21
testuser@domain.com,Bottom Folder 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12
testuser@domain.com,Bottom Folder 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11
testuser@domain.com,Middle Folder 2,1,My Drive/Top Folder/Middle Folder 2
testuser@domain.com,Middle Folder 1,1,My Drive/Top Folder/Middle Folder 1
testuser@domain.com,Top Folder,1,My Drive/Top Folder
```
Select a folder, no file path
```
$ gam user testuser print filelist title select drivefilename "Top Folder"
Getting all Drive Files/Folders that match query ('me' in owners and title = 'Top Folder') for testuser@domain.com
Got 1 Drive File/Folder for testuser@domain.com...
Owner,title
testuser@domain.com,Middle Folder 2
testuser@domain.com,Bottom Folder 22
testuser@domain.com,Bottom Doc 22
testuser@domain.com,Bottom Folder 21
testuser@domain.com,Bottom Doc 21
testuser@domain.com,Middle Folder 1
testuser@domain.com,Bottom Folder 12
testuser@domain.com,Bottom Sheet 12
testuser@domain.com,Bottom Folder 11
testuser@domain.com,Bottom Sheet 11
```
Select a folder, no file path, show parent (selected) folder
```
$ gam user testuser print filelist title select drivefilename "Top Folder" showparent
Getting all Drive Files/Folders that match query ('me' in owners and title = 'Top Folder') for testuser@domain.com
Got 1 Drive File/Folder for testuser@domain.com...
Owner,title
testuser@domain.com,Top Folder
testuser@domain.com,Middle Folder 2
testuser@domain.com,Bottom Folder 22
testuser@domain.com,Bottom Doc 22
testuser@domain.com,Bottom Folder 21
testuser@domain.com,Bottom Doc 21
testuser@domain.com,Middle Folder 1
testuser@domain.com,Bottom Folder 12
testuser@domain.com,Bottom Sheet 12
testuser@domain.com,Bottom Folder 11
testuser@domain.com,Bottom Sheet 11
```
Select a folder, partial file path
```
$ gam user testuser print filelist title select drivefilename "Top Folder" filepath
Getting all Drive Files/Folders that match query ('me' in owners and title = 'Top Folder') for testuser@domain.com
Got 1 Drive File/Folder for testuser@domain.com...
Owner,title,paths,path.0
testuser@domain.com,Middle Folder 2,1,Top Folder/Middle Folder 2
testuser@domain.com,Bottom Folder 22,1,Top Folder/Middle Folder 2/Bottom Folder 22
testuser@domain.com,Bottom Doc 22,1,Top Folder/Middle Folder 2/Bottom Folder 22/Bottom Doc 22
testuser@domain.com,Bottom Folder 21,1,Top Folder/Middle Folder 2/Bottom Folder 21
testuser@domain.com,Bottom Doc 21,1,Top Folder/Middle Folder 2/Bottom Folder 21/Bottom Doc 21
testuser@domain.com,Middle Folder 1,1,Top Folder/Middle Folder 1
testuser@domain.com,Bottom Folder 12,1,Top Folder/Middle Folder 1/Bottom Folder 12
testuser@domain.com,Bottom Sheet 12,1,Top Folder/Middle Folder 1/Bottom Folder 12/Bottom Sheet 12
testuser@domain.com,Bottom Folder 11,1,Top Folder/Middle Folder 1/Bottom Folder 11
testuser@domain.com,Bottom Sheet 11,1,Top Folder/Middle Folder 1/Bottom Folder 11/Bottom Sheet 11
```
Select a folder, partial file path, show parent (selected) folder
```
$ gam user testuser print filelist title select drivefilename "Top Folder" filepath showparent
Getting all Drive Files/Folders that match query ('me' in owners and title = 'Top Folder') for testuser@domain.com
Got 1 Drive File/Folder for testuser@domain.com...
Owner,title,paths,path.0
testuser@domain.com,Top Folder,1,Top Folder
testuser@domain.com,Middle Folder 2,1,Top Folder/Middle Folder 2
testuser@domain.com,Bottom Folder 22,1,Top Folder/Middle Folder 2/Bottom Folder 22
testuser@domain.com,Bottom Doc 22,1,Top Folder/Middle Folder 2/Bottom Folder 22/Bottom Doc 22
testuser@domain.com,Bottom Folder 21,1,Top Folder/Middle Folder 2/Bottom Folder 21
testuser@domain.com,Bottom Doc 21,1,Top Folder/Middle Folder 2/Bottom Folder 21/Bottom Doc 21
testuser@domain.com,Middle Folder 1,1,Top Folder/Middle Folder 1
testuser@domain.com,Bottom Folder 12,1,Top Folder/Middle Folder 1/Bottom Folder 12
testuser@domain.com,Bottom Sheet 12,1,Top Folder/Middle Folder 1/Bottom Folder 12/Bottom Sheet 12
testuser@domain.com,Bottom Folder 11,1,Top Folder/Middle Folder 1/Bottom Folder 11
testuser@domain.com,Bottom Sheet 11,1,Top Folder/Middle Folder 1/Bottom Folder 11/Bottom Sheet 11
```
Select a folder, full file path
```
$ gam user testuser print filelist title select drivefilename "Top Folder" fullpath
Getting all Drive Files/Folders that match query ('me' in owners and title = 'Top Folder') for testuser@domain.com
Got 1 Drive File/Folder for testuser@domain.com...
Owner,title,paths,path.0
testuser@domain.com,Middle Folder 2,1,My Drive/Top Folder/Middle Folder 2
testuser@domain.com,Bottom Folder 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22
testuser@domain.com,Bottom Doc 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22/Bottom Doc 22
testuser@domain.com,Bottom Folder 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21
testuser@domain.com,Bottom Doc 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21/Bottom Doc 21
testuser@domain.com,Middle Folder 1,1,My Drive/Top Folder/Middle Folder 1
testuser@domain.com,Bottom Folder 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12
testuser@domain.com,Bottom Sheet 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12/Bottom Sheet 12
testuser@domain.com,Bottom Folder 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11
testuser@domain.com,Bottom Sheet 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11/Bottom Sheet 11
```
Select a folder, full file path, show parent (selected) folder
```
$ gam user testuser print filelist title select drivefilename "Top Folder" fullpath showparent
Getting all Drive Files/Folders that match query ('me' in owners and title = 'Top Folder') for testuser@domain.com
Got 1 Drive File/Folder for testuser@domain.com...
Owner,title,paths,path.0
testuser@domain.com,Top Folder,1,My Drive/Top Folder
testuser@domain.com,Middle Folder 2,1,My Drive/Top Folder/Middle Folder 2
testuser@domain.com,Bottom Folder 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22
testuser@domain.com,Bottom Doc 22,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 22/Bottom Doc 22
testuser@domain.com,Bottom Folder 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21
testuser@domain.com,Bottom Doc 21,1,My Drive/Top Folder/Middle Folder 2/Bottom Folder 21/Bottom Doc 21
testuser@domain.com,Middle Folder 1,1,My Drive/Top Folder/Middle Folder 1
testuser@domain.com,Bottom Folder 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12
testuser@domain.com,Bottom Sheet 12,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 12/Bottom Sheet 12
testuser@domain.com,Bottom Folder 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11
testuser@domain.com,Bottom Sheet 11,1,My Drive/Top Folder/Middle Folder 1/Bottom Folder 11/Bottom Sheet 11
```

## File selection with or without a particular drive label
The Drive API doesn't support querying for a drive label, so GAM must do the filtering.

Get the label id.
```
gam show drivelabels
```

Find the label with properties:title: XXX where XXX is the desired label title, then get its id: value

List the files with the label
```
gam config csv_output_row_filter "labels:count>0" user user@domain.com print filelist fields id,name,mimetype showlabels ids includelabels PutLabelIdHere
```
List the files without the label
```
gam config csv_output_row_filter "labels:count=0" user user@domain.com print filelist fields id,name,mimetype showlabels ids includelabels PutLabelIdHere
```

Adjust the `fields` list as desired.

## Handle empty file lists
When you execute a `gam print filelist` command with a query or permission match, there may be no files output;
in this case, there is only a header row: `Owner`. Subsequent gam commands to process the file will fail.
```
$ gam redirect csv ./Files.csv user user@domain.com print filelist query "name contains 'abcd'" fields id,name
Getting all Drive Files/Folders that match query ('me' in owners and name contains 'abcd') for user@domain.com
Got 0 Drive Files/Folders that matched query ('me' in owners and name contains 'abcd') for user@domain.com...
$ more Files.csv
Owner
$ gam csv Files.csv gam user "~Owner" show fileinfo "~id" permissions
Command: /Users/admin/bin/gam csv Files.csv gam user "~Owner" show fileinfo >>>~id<<< permissions

ERROR: Header "id" not found in CSV headers of "Owner".
Help: Syntax in file /Users/admin/bin/gam/GamCommands.txt
Help: Documentation is at https://github.com/GAM-team/GAM/wiki
```

Now, the fields you select will be output on the header row and the subsequent command will not fail.
```
$ gam redirect csv ./Files.csv user user@domain.com print filelist query "name contains 'abcd'" fields id,name
Getting all Drive Files/Folders that match query ('me' in owners and name contains 'abcd') for user@domain.com
Got 0 Drive Files/Folders that matched query ('me' in owners and name contains 'abcd') for user@domain.com...
$ more Files.csv
Owner,id,name
$ gam csv Files.csv gam user "~Owner" show fileinfo "~id" permissions
$
```

If you specify `allfields`, a predefined set of headers are output.
```
$ gam redirect csv ./Files.csv user user@domain.com print filelist query "name contains 'abcd'" allfields
Getting all Drive Files/Folders that match query ('me' in owners and name contains 'abcd') for user@domain.com
Got 0 Drive Files/Folders that matched query ('me' in owners and name contains 'abcd') for user@domain.com...
$ more Files.csv
Owner,id,name,owners.0.emailAddress,permissions,permissions.0.allowFileDiscovery,permissions.0.deleted,permissions.0.displayName,permissions.0.domain,permissions.0.emailAddress,permissions.0.expirationTime,permissions.0.id,permissions.0.permissionDetails,permissions.0.photoLink,permissions.0.role,permissions.0.teamDrivePermissionDetails,permissions.0.type
```

You can also specify the headers you want in the case that there are no files selected; your script could test for this value.
```
$ gam redirect csv ./Files.csv user user@domain.com print filelist query "name contains 'abcd'" allfields nodataheaders "BadNews-NoData"
Getting all Drive Files/Folders that match query ('me' in owners and name contains 'abcd') for user@domain.com
Got 0 Drive Files/Folders that matched query ('me' in owners and name contains 'abcd') for user@domain.com...
$ more Files.csv
BadNews-NoData
```
## Display disk usage
```
gam <UserTypeEntity> print diskusage <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [anyowner|(showownedby any|me|others)]
        [sizefield quotabytesused|size]
        [pathdelimiter <Character>] [excludetrashed] [stripcrsfromname]
        (addcsvdata <FieldName> <String>)*
        [noprogress] [show all|summary|summaryandtrash]
```
For each folder in `<DriveFileEntity>`, the following items are displayed:
* `User` - The email address of the user in `<UserTypeEntity>`
* `Owner` - The email address of the owner of the folder; omitted when displaying disk usage on Shared Drives
* `ownedByMe` - True if the folder is owned by `User`, False otherwise; omitted when displaying disk usage on Shared Drives
* `id` - The folder ID
* `name` - The Folder name
* `trashed` - True if the folder has been trashed, either explicitly or from a trashed parent folder, False otherwise
* `explicitlyTrashed` - True if the folder has been explicitly trashed, as opposed to recursively trashed from a parent folder, False otherwise
* `directFileCount` - The number of files directly in the folder
* `directFileSize` - The sum of the sizes of the files directly in the folder
* `directFolderCount` - The number of folders directly in the folder
* `totalFileCount` - The number of files directly in the folder and all of its subfolders
* `totalFileSize` - The sum of the sizes of the files directly in the folder and all of its subfolders
* `totalFolderCount` - The number of folders directly in the folder and all of its subfolders
* `depth` - The depth of the folder
  * `-1` - The top level folder
  * `0` - Immediate children of the top level folder
  * `1` - Immediate children of level 0 folders
* `path` - The path of the folder

There is a final row detailing files and folders in the trash; it is omitted if `excludetrashed` or `show summary` are specified.
* `User` - The email address of the user in `<UserTypeEntity>`
* `Owner` - The email address of the user in `<UserTypeEntity>`
* `ownedByMe` - True
* `id` - Trash
* `name` - Trash
* `trashed` - True if there are any items in the trash
* `explicitlyTrashed` - True if any items have been explicitly trashed
* `directFileCount` - The number of explicitly trashed files
* `directFileSize` - The sum of the sizes of the explicitly trashed files 
* `directFolderCount` - The number of explicitly trashed folders
* `totalFileCount` - The number of files in the trash
* `totalFileSize` - The sum of the sizes of the files in the trash
* `totalFolderCount` - The number of folders in the trash
* `depth` - Always -1
* `path` - Trash

GAM version `6.71.17` added the `depth` column that can be used to filter the depth of the folders displayed.
Depth `-1` is the top level folder, depth `0` are its immediate children, depth `2` are the children of depth `1` and so forth.
For example to limit the display to the top folder and its immediate children, use `config csv_output_row_filter depth:count<1`.

By default, files owned by the user are counted. These options update the current query with the desired ownership.
* `showownedby me` - Count files owned by the user; this is the default
* `showownedby any` or `anyowner` - Count files accessible by the user
* `showownedby others` - Count files not owned by the user

All folders are counted, regardless of ownership.

By default, file path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

Use the `excludetrashed` option to suppress counting files and folders in the trash.

The `stripcrsfromname` option strips nulls, carriage returns and linefeeds from drive file names.
Use this option if you discover filenames containing these special characters; it is not common.

Add additional columns of data from the command line to the output:
* `addcsvdata <FieldName> <String>`

By default, progress messages are displayed for each folder, use `noprogress` to suppress these messages.

Use the `show` option to control the display of data:
* `show all` - Display a row for every folder in `<DriveFileEntity>` and a row detailing items in the trash when `excludetrashed` is omitted. This is the default.
* `show summary` - Display a single row for the first folder in `<DriveFileEntity>`
* `show summaryandtrash` - Display a single row for the first folder in `<DriveFileEntity>` and a row detailing items in the trash when `excludetrashed` is omitted.

### Examples
```
$ gam redirect csv ./MyDriveUsage.csv user user@domain.com print diskusage mydrive 
User: user@domain.com, Print 1 Drive Disk Usage
$ more MyDriveUsage.csv
User,Owner,id,name,ownedByMe,trashed,explicitlyTrashed,directFileCount,directFileSize,directFolderCount,totalFileCount,totalFileSize,totalFolderCount,depth,path
user@domain.com,user@domain.com,012YenC8f12ALUk9PVA,My Drive,,False,False,100,138212,24,167,189598,79,-1,My Drive
user@domain.com,user@domain.com,456YenC8f12ALfndaQ1NHc0RtUG92Y1BIUUl4bjVBRmNkWG5oakNqVVFDcXJWOHNmdFlwZmc,Classroom,True,False,False,0,0,15,9,6840,17,0,My Drive/Classroom
user@domain.com,user@domain.com,0B3YenC8f12ALfmRuX3I4WFlqaTRnMGhXNkVvWV9UUG1zRDQwY1BwVkJhUGx5WHVIcjJKZUU,TestUpdate,True,False,False,2,3420,0,2,3420,0,1,My Drive/Classroom/TestUpdate
user@domain.com,user@domain.com,1MT5xJ897oYa0Q2OuzBDfLHvig6k_b0EKaovVA2imGYcnrmqZu5hjlJkEPMH-rHKj4qDyy9_j,TS Course,True,False,False,0,0,0,0,0,0,1,My Drive/Classroom/TS Course
user@domain.com,user@domain.com,1gsbqsbhhwBx9hCF0sqtE213tpUn6Ebj2klLFhHb4xkzBKIdEFkvvwCVtZpYWPgOA796fIPEN,TS Course 2,True,False,False,0,0,0,0,0,0,1,My Drive/Classroom/TS Course 2
...
user@domain.com,user@domain.com,1bHS_Tp77W3KSGRNSs_jP1RhAJhIGRCaI,XferFolder,True,False,False,1,1024,0,1,1024,0,0,My Drive/XferFolder
user@domain.com,user@domain.com,Trash,Trash,,True,True,0,0,1,3,3072,9,-1,Trash

$ gam config csv_output_row_filter "depth:count<1" redirect csv ./MyDriveUsage.csv user user@domain.com print diskusage mydrive 
User: user@domain.com, Print 1 Drive Disk Usage
$ more MyDriveUsage.csv
User,Owner,id,name,ownedByMe,trashed,explicitlyTrashed,directFileCount,directFileSize,directFolderCount,totalFileCount,totalFileSize,totalFolderCount,depth,path
user@domain.com,user@domain.com,012YenC8f12ALUk9PVA,My Drive,,False,False,100,138212,24,167,189598,79,-1,My Drive
user@domain.com,user@domain.com,456YenC8f12ALfndaQ1NHc0RtUG92Y1BIUUl4bjVBRmNkWG5oakNqVVFDcXJWOHNmdFlwZmc,Classroom,True,False,False,0,0,15,9,6840,17,0,My Drive/Classroom
...
user@domain.com,user@domain.com,1bHS_Tp77W3KSGRNSs_jP1RhAJhIGRCaI,XferFolder,True,False,False,1,1024,0,1,1024,0,0,My Drive/XferFolder
user@domain.com,user@domain.com,Trash,Trash,,True,True,0,0,1,3,3072,9,-1,Trash

$ gam redirect csv ./MyDriveUsage.csv user user@domain.com print diskusage mydrive show summaryandtrash
User: user@domain.com, Print 1 Drive Disk Usage
$ more MyDriveUsage.csv 
User,Owner,id,name,ownedByMe,trashed,explicitlyTrashed,directFileCount,directFileSize,directFolderCount,totalFileCount,totalFileSize,totalFolderCount,depth,path
user@domain.com,user@domain.com,012YenC8f12ALUk9PVA,My Drive,,False,False,100,138212,24,167,189598,79,-1,My Drive
user@domain.com,user@domain.com,Trash,Trash,,True,True,0,0,1,3,3072,9,-1,Trash

$ gam redirect csv ./MyDriveUsage.csv user user@domain.com print diskusage shareddriveid 0AL5LiIe4dqxZUk9PVA  show summaryandtrash
User: user@domain.com, Print 1 Drive Disk Usage
$ more MyDriveUsage.csv 
User,id,name,trashed,explicitlyTrashed,directFileCount,directFileSize,directFolderCount,totalFileCount,totalFileSize,totalFolderCount,depth,path
user@domain.com,0125LiIe4dqxZUk9PVA,TS Shared Drive 1,False,False,16,6144,7,42,73799,25,-1,SharedDrives/TS Shared Drive 1
user@domain.com,Trash,Trash,True,True,1,1024,0,1,1024,0,-1,Trash
```

## Display files published to the web
Ths requires version 6.80.13 or later.

You can display files published to the web.
```
# Get the published files
gam config csv_output_header_filter "Owner,id,revisions.0.published,revisions.0.publishedOutsideDomain" csv_output_row_filter "revisions.0.published:boolean:true" auto_batch_min 1 num_threads 20 redirect csv ./PublishedDocs.csv multiprocess redirect stderr - multiprocess <UserTypeEntity> print filerevisions my_publishable_items select last 1
# Get the files name, MIMEtype and path
gam redirect csv ./PublishedDocsWithName.csv multiprocess redirect stderr - multiprocess csv ./PublishedDocs.csv gam user "~Owner" print filelist select "~id" fields id,name,mimetype fullpath addcsvdata published "~revisions.0.published" addcsvdata publishedOutsideDomain "~revisions.0.publishedOutsideDomain" 
```

You can display files published to the web internally for your domain only.
```
# Get the internally only published files
gam config csv_output_header_filter "Owner,id,revisions.0.published,revisions.0.publishedOutsideDomain" csv_output_row_filter "revisions.0.published:boolean:true,revisions.0.publishedOutsideDomain:boolean:false" auto_batch_min 1 num_threads 20 redirect csv ./PublishedDocs.csv multiprocess redirect stderr - multiprocess <UserTypeEntity> print filerevisions my_publishable_items select last 1
# Get the files name, MIMEtype and path
gam redirect csv ./PublishedDocsWithName.csv multiprocess redirect stderr - multiprocess csv ./PublishedDocs.csv gam user "~Owner" print filelist select "~id" fields id,name,mimetype fullpath addcsvdata published "~revisions.0.published" addcsvdata publishedOutsideDomain "~revisions.0.publishedOutsideDomain" 
```

You can display files published to the web externally outside of your domain.
```
# Get the externally published files
gam config csv_output_header_filter "Owner,id,revisions.0.published,revisions.0.publishedOutsideDomain" csv_output_row_filter "revisions.0.published:boolean:true,revisions.0.publishedOutsideDomain:boolean:true" auto_batch_min 1 num_threads 20 redirect csv ./PublishedDocs.csv multiprocess redirect stderr - multiprocess <UserTypeEntity> print filerevisions my_publishable_items select last 1
# Get the files name, MIMEtype and path
gam redirect csv ./PublishedDocsWithName.csv multiprocess redirect stderr - multiprocess csv ./PublishedDocs.csv gam user "~Owner" print filelist select "~id" fields id,name,mimetype fullpath addcsvdata published "~revisions.0.published" addcsvdata publishedOutsideDomain "~revisions.0.publishedOutsideDomain" 
```

## Display information about last modified file on a drive
Use these commands to display information about the most recently modified file on a drive.

By default, a user's My Drive is processed; optionally, a Shared Drive can be processed.
```
gam <UserTypeEntity> print drivelastmodification [todrive <ToDriveAttribute>*]
        [select <SharedDriveEntity>]
        [pathdelimiter <Character>]
        (addcsvdata <FieldName> <String>)*
gam <UserTypeEntity> show drivelastmodification
        [select <SharedDriveEntity>]
        [pathdelimiter <Character>]
```
In addition to the user and optional Shared Drive information, The following fields are displayed
`lastModifiedFileId,lastModifiedFileName,lastModifiedFileMimeType,lastModifiedFilePath,lastModifyingUser,lastModifiedTime`

By default, file path components are separated by `/`; use `pathdelimiter <Character>` to use `<Character>` as the separator.

For print drivelastmodification, add additional columns of data from the command line to the output:
* `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output
