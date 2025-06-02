# Users - Shared Drives
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [GUI API permission name mapping](#gui-api-permission-name-mapping)
- [Display Shared Drive themes](#display-shared-drive-themes)
- [Manage Shared Drives](#manage-shared-drives)
  - [Create a Shared Drive](#create-a-shared-drive)
    - [Bulk Create Shared Drives](#bulk-create-shared-drives)
  - [Update Shared Drive settings](#update-shared-drive-settings)
  - [Delete a Shared Drive](#delete-a-shared-drive)
  - [Change Shared Drive visibility](#change-shared-drive-visibility)
- [Display Shared Drives](#display-shared-drives)
- [Display Shared Drive Counts](#display-shared-drive-counts)
- [Display Shared Drive Organizers](#display-shared-drive-organizers)
- [Manage Shared Drive access](#manage-shared-drive-access)
- [Display Shared Drive access](#display-shared-drive-access)
  - [Display Shared Drive access for specific Shared Drives](#display-shared-drive-access-for-specific-shared-drives)
  - [Display Shared Drive access for selected Shared Drives](#display-shared-drive-access-for-selected-shared-drives)
- [Change single User1 Shared Drive access to User2](#change-single-user1-shared-drive-access-to-user2)
- [Bulk change User1 Shared Drive access to User2](#bulk-change-user1-shared-drive-access-to-user2)
- [Display empty folders on a Shared Drive](#display-empty-folders-on-a-shared-drive)
- [Delete empty folders on a Shared Drive](#delete-empty-folders-on-a-shared-drive)
- [Empty the trash on a Shared Drive](#empty-the-trash-on-a-shared-drive)
- [Commands not applicable to Shared Drives](#commands-not-applicable-to-shared-drives)

## API documentation
* [Drive API - Drives](https://developers.google.com/drive/api/reference/rest/v3/drives)
* [Drive API - Files](https://developers.google.com/drive/api/reference/rest/v3/files)
* [Manage Shared Drives](https://developers.google.com/drive/v3/web/manage-teamdrives#managing_team_drives_for_domain_administrators)
* [Move content to Shared Drives](https://support.google.com/a/answer/7374057)
* [Shared Drive Limits](https://support.google.com/a/users/answer/7338880)
* [Shared Drives in Org Units](https://support.google.com/a/answer/7337635)

## Query documentation
* [Shared Drives Search](https://developers.google.com/drive/api/guides/search-shareddrives)

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
<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<OrganizerType> ::= user|group
<OrganizerTypeList> ::= "<OrganizerType>(,<OrganizerType>)*"

<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String>)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

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

<DriveFileACLRole> ::=
        manager|organizer|owner|
        contentmanager|fileorganizer|
        contributor|writer|editor|
        commenter|
        viewer|reader
<DriveFileACLType> ::= anyone|domain|group|user
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
         <JSONData> |
         <FileSelector> |
         <CSVFileSelector> |
         <CSVkmdSelector> |
         <CSVDataSelector>
<DriveFilePermissionIDEntity> ::=
         <DriveFilePermissionIDList> |
         <JSONData> |
         <FileSelector> |
         <CSVFileSelector> |
         <CSVkmdSelector> |
         <CSVDataSelector>

<SharedDriveACLRole> ::=
        manager|organizer|owner|
        contentmanager|fileorganizer|
        contributor|writer|editor|
        commenter|
        viewer|reader
<SharedDriveACLRoleList> ::= "<SharedDriveACLRole>(,<SharedDriveACLRole>)*"
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<SharedDriveEntity> ::=
        <SharedDriveID>|
        (teamdriveid <SharedDriveID>)|(teamdriveid:<SharedDriveID>)|
        (teamdrive <SharedDriveName>)|(teamdrive:<SharedDriveName>)

<SharedDriveFieldName> ::=
        backgroundimagefile|
        backgroundimagelink|
        capabilities|
        colorrgb|
        createdtime|
        id|
        name|
        themeid
<SharedDriveFieldNameList> ::= "<SharedDriveFieldName>(,<SharedDriveFieldName>)*"

<SharedDriveIDEntity> ::= (teamdriveid <DriveFileItem>) | (teamdriveid:<DriveFileItem>)
<SharedDriveNameEntity> ::= (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
<SharedDriveFileNameEntity> ::= (teamdrivefilename <DriveFileName>) | (teamdrivefilename:<DriveFileName>)
<SharedDriveFileQueryEntity> ::= (teamdrivequery <QueryDriveFile>) | (teamdrivequery:<QueryDriveFile>)
<SharedDriveFileQueryShortcut> ::=
        all_files | all_folders | all_google_files | all_non_google_files | all_items

<SharedDriveFileEntity> ::=
        <SharedDriveIDEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveNameEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveFileNameEntity> |
        <SharedDriveFileQueryEntity> |
        <FileSelector> | <CSVkmdSelector> | <CSVSubkeySelector>) | <CSVDataSelector>)

<SharedDriveRestrictionsSubfieldName> ::=
        adminmanagedrestrictions|
        allowcontentmanagerstosharefolders|
        copyrequireswriterpermission|
        domainusersonly|
        drivemembersonly|teammembersonly|
        sharingfoldersrequiresorganizerpermission

Each pair of restrictions below are equivalent:

allowcontentmanagerstosharefolders true
sharingfoldersrequiresorganizerpermission false

allowcontentmanagerstosharefolders false
sharingfoldersrequiresorganizerpermission true
```

## GUI API permission name mapping

| GUI setting | API setting |
|------------|------------|
| Manager | organizer |
| Content manager | fileOrganizer |
| Contributor | writer |
| Commenter | commenter |
| Viewer | reader |

## Display Shared Drive themes
```
gam <UserTypeEntity> show shareddrivethemes
```
## Manage Shared Drives

## Create a Shared Drive
The user that creates a Shared Drive is given the permission role organizer for the Shared Drive,
```
gam <UserTypeEntity> create shareddrive <Name>
        [(theme|themeid <String>)|
         ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
        (<SharedDriveRestrictionsSubfieldName> <Boolean>)*
        [hide <Boolean>] [ou|org|orgunit <OrgUnitItem>]
        [errorretries <Integer>] [updateinitialdelay <Integer>] [updateretrydelay <Integer>]
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) | returnidonly]
```
* `themeid` - a Shared Drive themeId obtained from `show shareddrivethemes`
* `customtheme` - set the backgroundImageFile property described here:  https://developers.google.com/drive/v3/reference/teamdrives
  * `<Float>` - X coordinate, typically 0.0
  * `<Float>` - Y coordinate, typically 0.0
  * `<Float>` - width, typically 1.0
* `color` - set the Shared Drive color
* `<SharedDriveRestrictionsSubfieldName> <Boolean>` - Set Shared Drive Restrictions
* `hide <Boolean>` - Set Shared Drive visibility

If any attributes other than `themeid` are specified, GAM must create the Drive and then update the Drive attributes.
Even though the Create API returns success, the Update API fails and reports that the Drive does not exist. 
* `errorretries <Integer>` - Number of create/update error retries; default value 5, range 0-10
* `updateinitialdelay <Integer>` - Initial delay after create before update: default value 10, range 0-60
* `updateretrydelay <Integer>` - Retry delay when update fails; default value 10, range 0-60

For this reason, GAM waits `updateinitialdelay <Integer>` seconds after the create before attempting the update.
GAM repeats the update `errorretries <Integer>` times waiting `updateretrydelay <Integer>` between tries
if the Update API continues to fail.

This is acceptable when creating a single Shared Drive, for bulk Shared Drive creation see [Bulk Create Shared Drives](#bulk-create-shared-drives).

This option is only available when the command is run as an administrator.
* `ou|org|orgunit <OrgUnitItem>` - See: https://workspaceupdates.googleblog.com/2022/05/shared-drives-in-organizational-units-open-beta.html

By default, the user and Shared Drive name and ID values are displayed on stdout.
* `csv [todrive <ToDriveAttribute>*]` - Write user, Shared Drive name and ID values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output
* `returnidonly` - Display just the ID of the created Shared Drive as output
When either of these options is chosen, no infomation about Shared Drive restrictions or hiding will be displayed.

To retrieve the Shared Drive ID with `returnidonly`:
```
Linux/MacOS
teamDriveId=$(gam user user@domain.com create shareddrive ... returnidonly)
Windows PowerShell
$teamDriveId = & gam user user@domain.com create shareddrive ... returnidonly
```

## Bulk Create Shared Drives
Most Shared Drive attributes can't be applied as part of the create, the Drive must be created and then updated with the desired attributes.

As a newly created Drive can't be updated for 30+ seconds; split the operation into two commands: create and update.

Make a CSV file SharedDriveNames.csv with at least two columns, User and name.
```
gam redirect csv ./SharedDrivesCreated.csv multiprocess csv SharedDriveNames.csv gam user "~User" create shareddrive "~name" csv
```
This will create a three column CSV file SharedDriveNamesIDs.csv with columns: User,name,id
* There will be a row for each Shared Drive.

Use the SharedDrivesCreated.csv file to apply the desired options/attributes.
```
gam redirect stdout ./SharedDrivesUpdated.txt multiprocess redirect stderr stdout csv ./SharedDrivesCreated.csv gam user "~User" update shareddrive "~id" [options/attributes as desired]
```

## Update Shared Drive settings

This command is used to set basic Shared Drive settings.
```
gam <UserTypeEntity> update shareddrive <SharedDriveEntity> [adminaccess|asadmin] [name <Name>]
        [(theme|themeid <String>)|
         ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
        (<SharedDriveRestrictionsSubfieldName> <Boolean>)*
        [hide|hidden <Boolean>] [ou|org|orgunit <OrgUnitItem>]
```
* `themeid` - a Shared Drive themeId obtained from `show shareddrivethemes`
* `customtheme` - set the backgroundImageFile property described here:  https://developers.google.com/drive/v3/reference/teamdrives
* `color` - set the Shared Drive color
* `<SharedDriveRestrictionsSubfieldName> <Boolean>` - Set Shared Drive Restrictions
* `hidden <Boolean>` - Set Shared Drive visibility

This option is only available when the command is run as an administrator.
* `ou|org|orgunit <OrgUnitItem>` - See: https://workspaceupdates.googleblog.com/2022/05/shared-drives-in-organizational-units-open-beta.html

## Delete a Shared Drive
```
gam <UserTypeEntity> delete shareddrive <SharedDriveEntity> [allowitemdeletion] [adminaccess|asadmin]
```
By default, deleting a Shared Drive that contains any files/folders will fail.
The `allowitemdeletion` option allows a Super Admin to delete a non-empty Shared Drive.
This is not reversible, proceed with caution.

## Change Shared Drive visibility
```
gam <UserTypeEntity> hide shareddrive <SharedDriveEntity>
gam <UserTypeEntity> unhide shareddrive <SharedDriveEntity>
```
## Display Shared Drives
```
gam <UserTypeEntity> show shareddriveinfo <SharedDriveEntity>
gam <UserTypeEntity> info shareddrive <SharedDriveEntity>
        [fields <SharedDriveFieldNameList>]
        [guiroles [<Boolean>] [formatjson]
gam <UserTypeEntity> show shareddriveinfo <SharedDriveEntity>
        [fields <SharedDriveFieldNameList>]
        [guiroles [<Boolean>] [formatjson]
gam <UserTypeEntity> show shareddrives
        [matchname <REMatchPattern>] (role|roles <SharedDriveACLRoleList>)*
        [fields <SharedDriveFieldNameList>]
        [guiroles [<Boolean>] [formatjson]
```
By default, Gam displays all Teams Drives accessible by the user.
* `matchname <REMatchPattern>` - Display Shared Drives with names that match a pattern.
* `(role|roles <SharedDriveACLRoleList>)*` - Display Shared Drives where the user has one of the specified roles.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print shareddrives [todrive <ToDriveAttribute>*]
        [matchname <REMatchPattern>] (role|roles <SharedDriveACLRoleList>)*
        [fields <SharedDriveFieldNameList>] [formatjson [quotechar <Character>]]
```
By default, Gam displays all Teams Drives accessible by the user.
* `matchname <REMatchPattern>` - Display Shared Drives with names that match a pattern.
* `(role|roles <SharedDriveACLRoleList>)*` - Display Shared Drives where the user has one of the specified roles.

The Google Drive API does not list roles for Shared Drives so GAM generates a role from the capabilities:
* `commenter - canComment: True, canEdit: False`
* `reader - canComment: False, canEdit: False`
* `writer - canEdit: True, canTrashChildren: False`
* `fileOrganizer - canTrashChildren: True, canManageMembers: False`
* `organizer - canManageMembers: True`

By default, the Drive API role names are displayed, use `guiroles` to display the Google Drive GUI role names.
```
API: GUI
commenter: Commenter
fileOrganizer: Content manager
organizer: Manager
reader: Viewer
writer: Contributor
```

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Shared Drive Counts
Display the number of Shared Drives.
```
gam <UserTypeEntity> show|print shareddrives
        [teamdriveadminquery|query <QueryTeamDrive>]
        [matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        showitemcountonly
```
By default, all Shared Drives are counted; use the following options to select a subset of Shared Drives:
* `teamdriveadminquery|query <QueryTeamDrive>` - Use a query to select Shared Drives
* `matchname <REMatchPattern>` - Retrieve Shared Drives with names that match a pattern.
* `orgunit|org|ou <OrgUnitPath>` - Only Shared Drives in the specified Org Unit are selected

Example
```
$ gam user user@domain.com print shareddrives showitemcountonly                 
Getting all Shared Drives for user@domain.com 
Got 4 Shared Drives for user@domain.com ...
4
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam user user@domain.com print shareddrives showitemcountonly)
Windows PowerShell
count = & gam user user@domain.com print shareddrives showitemcountonly
```
## Display Shared Drive Organizers
The following command can be used instead of the `GetTeamDriveOrganizers.py` script.

```
gam <UserTypeEntity> print shareddriveorganizers [todrive <ToDriveAttribute>*]
        [adminaccess|asadmin]
        [(shareddriveadminquery|query <QuerySharedDrive>) |
         (shareddrives|teamdrives (<SharedDriveIDList>|(select <FileSelector>|<CSVFileSelector>)))]
        [orgunit|org|ou <OrgUnitPath>]
        [matchname <REMatchPattern>]
        [domainlist <DomainList>]
        [includetypes <OrganizerTypeList>]
        [oneorganizer [<Boolean>]]
        [shownorganizerdrives [false|true|only]]
        [includefileorganizers [<Boolean>]]
        [delimiter <Character>]
```
Options `shareddriveadminquery|query` and `shareddrives|teamdrives` are mutually exclusive.

Options `shareddriveadminquery|query` and `orgunit|org|ou` require `adminaccess|asadmin`.

By default, organizers for all Shared Drives are displayed; use the following options to select a subset of Shared Drives:
* `teamdriveadminquery|query <QueryTeamDrive>` - Use a query to select Shared Drives
* `shareddrives|teamdrives <SharedDriveIDList>` - Select the Shared Drive IDs specified in `<SharedDriveIDList>`
* `shareddrives|teamdrives select <FileSelector>|<CSVFileSelector>` - Select the Shared Drive IDs specified in `<FileSelector>|<CSVFileSelector>`
* `orgunit|org|ou <OrgUnitPath>` - Only Shared Drives in the specified Org Unit are selected
* `matchname <REMatchPattern>` - Retrieve Shared Drives with names that match a pattern.

For multiple organizers:
* `delimiter <Character>` - Separate `organizers` entries with `<Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.

The command defaults do not match the script defaults, they are set for the most common use case:
* `domainlist` - The workspace primary domain
* `includetypes` - user
* `oneorganizer` - True
* `shownoorganizerdrives` - True
* `includefileorganizers` - False

To select organizers from any domain, use: `domainlist ""`

For example, to get a single user organizer from your domain for all Shared Drives including no organizer drives:
```
gam redirect csv ./TeamDriveOrganizers.csv print shareddriveorganizers
```

## Manage Shared Drive access
These commands must be issued by a user with Shared Drive permission role organizer.
### Process single ACLs.
```
gam <UserTypeEntity> add drivefileacl <SharedDriveFileEntity>
        anyone|(user <UserItem>)|(group <GroupItem>)|(domain <DomainName>)
        (role <DriveFileACLRole>) [withlink|(allowfilediscovery|discoverable [<Boolean>])]
        [expires|expiration <Time>] [sendemail] [emailmessage <String>] [showtitles]
gam <UserTypeEntity> update drivefileacl <SharedDriveFileEntity> <DriveFilePermissionIDorEmail>
        (role <DriveFileACLRole>) [withlink|(allowfilediscovery|discoverable [<Boolean>])]
        [expires|expiration <Time>] [removeexpiration [<Boolean>]] [showtitles]
gam <UserTypeEntity> delete drivefileacl <SharedDriveFileEntity> <DriveFilePermissionIDorEmail>
        [showtitles]
```
By default, when an ACL is added/updated, GAM outputs details of the ACL. The `nodetails` option
suppresses this output.

By default, the file ID is displayed in the output; to see the file name, use the 'showtitles`
option; this requires an additional API call per file.

### Process multiple ACLs.
```
gam <UserTypeEntity> add permissions <DriveFileEntity> <DriveFilePermissionEntity>
        [expires|expiration <Time>] [sendemail] [emailmessage <String>]
        <PermissionMatch>* [<PermissionMatchAction>]
gam <UserTypeEntity> delete permissions <DriveFileEntity> <DriveFilePermissionIDEntity>
        <PermissionMatch>* [<PermissionMatchAction>]
```
Permission matching only applies when the `<JSONData>`
variant of `<DriveFilePermissionEntity>` and `<DriveFilePermissionIDEntity>` is used.

When adding permissions from JSON data, there is a default match: `pm not role owner em` that disables ownership changes.
If you want to process all permissions, enter `pm em` to clear the default match.

When adding permissions from JSON data, permissions with `deleted` true are never processed.

When deleting permissions from JSON data, permissions with role `owner` true are never processed.

## Display Shared Drive access

These commands are used to display the ACLs on Shared Drives themselves, not the files/folders on the Shared Drives.

## Display Shared Drive access for specific Shared Drives
```
gam <UserTypeEntity> show drivefileacls <DriveFileEntity>
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [showtitles] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [formatjson] [adminaccess|asadmin]
gam <UserTypeEntity> print drivefileacls <DriveFileEntity> [todrive <ToDriveAttribute>*]
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [showtitles] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [formatjson [quotechar <Character>]] [adminaccess|asadmin]
```
By default, all Shared Drives specified are displayed; use the following option to select a subset of those Shared Drives.
* `<PermissionMatch>* [<PermissionMatchAction>] pmselect` - Use permission matching to select Shared Drives

By default, all ACLS are displayed; use the following option to select a subset of the ACLS to display.
* `<PermissionMatch>* [<PermissionMatchAction>]` - Use permission matching to display a subset of the ACLs for each Shared Drive; this only applies when `pmselect` is not specified

With `print drivefileacls` or `show drivefileacls formatjson`, the ACLs selected for display are all output on one row/line as a repeating item with the matching file id.
When `oneitemperrow` is specified, each ACL is output on a separate row/line with the matching Shared Drive id and name. This simplifies processing the CSV file with subsequent Gam commands.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Shared Drive access for selected Shared Drives
```
gam <UserTypeEntity> show shareddriveacls
        adminaccess [teamdriveadminquery|query <QueryTeamDrive>]
        [matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        [user|group <EmailAddress> [checkgroups]] (role|roles <SharedDriveACLRoleList>)*
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        [formatjson [quotechar <Character>]]
gam <UserTypeEntity> print shareddriveacls [todrive <ToDriveAttribute>*]
        adminaccess [teamdriveadminquery|query <QueryTeamDrive>]
	[matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        [user|group <EmailAddress> [checkgroups]] (role|roles <SharedDriveACLRoleList>)*
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        [formatjson [quotechar <Character>]]
```
By default,only Shared Drives with `<UserTypeEntity>` as a member are displayed. To display all
Shared Drives in the workspace, `<UserTypeEntity>` should specify a super admin and the `adminaccess`
option shoud be used.

By default, all Shared Drives are displayed; use the following options to select a subset of Shared Drives:
* `teamdriveadminquery|query <QueryTeamDrive>` - Use a query to select Shared Drives
* `matchname <REMatchPattern>` - Retrieve Shared Drives with names that match a pattern.
* `orgunit|org|ou <OrgUnitPath>` - Only Shared Drives in the specified Org Unit are selected
* `<PermissionMatch>* [<PermissionMatchAction>] pmselect` - Use permission matching to select Shared Drives

By default, all ACLS are displayed; use the following options to select a subset of the ACLS to display.
* `user|group <EmailAddress> [checkgroups]` - Display ACLs for the specified `<EmailAddress>` only; if there is no ACL for `<EmailAddress>` and `checkgroups` is specified, display any ACLs for groups that have `<EmailAddress>` as a member.
* `role|roles <SharedDriveACLRoleList>` - Display ACLs for the specified roles only.
* `<PermissionMatch>* [<PermissionMatchAction>]` - Use permission matching to display a subset of the ACLs for each Shared Drive; this only applies when `pmselect` is not specified

With `print shareddriveacls` or `show shareddrivecls formatjson`, the ACLs selected for display are all output on one row/line as a repeating item with the matching Shared Drive id.
When `oneitemperrow` is specified, each ACL is output on a separate row/line with the matching Shared Drive id and name. This simplifies processing the CSV file with subsequent Gam commands.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display empty folders on a Shared Drive
This command must be issued by a user with Shared Drive permission role organizer.
```
gam <UserTypeEntity> print emptydrivefolders [todrive <ToDriveAttribute>*]
        select <SharedDriveEntity>
```

## Change single User1 Shared Drive access to User2
```
# Get Shared Drives for User1
gam redirect csv ./U1SharedDrives.csv user user1@domain.com print shareddriveacls pm emailaddress user1@domain.com em oneitemperrow
# For each of those Shared Drives, delete User1 access
gam redirect stdout ./DeleteU1SharedDriveAccess.txt multiprocess redirect stderr stdout csv ./U1SharedDrives.csv gam delete drivefileacl "~id" "~permission.emailAddress"
# For each of those Shared Drives, add User2 with the same role that User1 had
gam redirect stdout ./AddU2SharedDriveAccess.txt multiprocess redirect stderr stdout csv ./U1SharedDrives.csv gam create drivefileacl "~id" user user2@domain.com role "~permission.role"
```

## Bulk change User1 Shared Drive access to User2
This requires GAM version 6.79.09 or higher.

Make a CSV file Users.csv with two email address columns: User,Replace
```
# Get Shared Drives for all Users in CSV file
gam redirect csv ./U1SharedDrives.csv multiprocess csv Users.csv gam user "~User" print shareddriveacls pm emailaddress "~User" em oneitemperrow addscvdata Replace "~Replace"
# For each of those Shared Drives, delete User access
gam redirect stdout ./DeleteU1SharedDriveAccess.txt multiprocess redirect stderr stdout csv ./U1SharedDrives.csv gam delete drivefileacl "~id" "~permission.emailAddress"
# For each of those Shared Drives, add Replace with the same role that User had
gam redirect stdout ./AddU2SharedDriveAccess.txt multiprocess redirect stderr stdout csv ./U1SharedDrives.csv gam create drivefileacl "~id" user "~Replace" role "~permission.role"
```

## Delete empty folders on a Shared Drive
This command must be issued by a user with Shared Drive permission role organizer.
```
gam <UserTypeEntity> delete emptydrivefolders <SharedDriveEntity>
```
## Empty the trash on a Shared Drive
This command must be issued by a user with Shared Drive permission role organizer.
```
gam <UserTypeEntity> empty drivetrash <SharedDriveEntity>
```
## Commands not applicable to Shared Drives
```
    gam <UserTypeEntity> transfer drive <UserItem> [keepuser]
    gam <UserTypeEntity> transfer ownership <DriveFileEntity> <UserItem> [includetrashed] (orderby <DriveOrderByFieldName> [ascending|descending])* [preview] [filepath] [todrive <ToDriveAttribute>*]
    gam <UserTypeEntity> claim ownership <DriveFileEntity> [skipids <DriveFileEntity>] [skipusers <UserTypeEntity>] [subdomains <DomainNameEntity>] [includetrashed] [restricted [<Boolean>]] [writerscantshare [<Boolean>]] [preview] [filepath] [todrive <ToDriveAttribute>*]
    gam <UserTypeEntity> collect orphans (orderby <DriveOrderByFieldName> [ascending|descending])*
        [targetuserfoldername <DriveFileName>] [preview] [todrive <ToDriveAttribute>*]
```
