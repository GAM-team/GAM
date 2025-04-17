# Domain Administrators - Shared Drives
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [Introduction](#introduction)
- [GUI API permission name mapping](#gui-api-permission-name-mapping)
- [Display Shared Drive themes](#display-shared-drive-themes)
- [Manage Shared Drives](#manage-shared-drives)
  - [Create a Shared Drive](#create-a-shared-drive)
    - [Bulk Create Shared Drives](#bulk-create-shared-drives)
  - [Update Shared Drive settings](#update-shared-drive-settings)
  - [Delete a Shared Drive](#delete-a-shared-drive)
  - [Change Shared Drive visibility](#change-shared-drive-visibility)
- [Display Shared Drives](#display-shared-drives)
- [Display List of Shared Drives in an Organizational Unit other than /](#display-list-of-shared-drives-in-an-organizational-unit-other-than-)
- [Display List of Shared Drives in an Organizational Unit](#display-list-of-shared-drives-in-an-organizational-unit)
- [Display all Shared Drives with no members](#display-all-shared-drives-with-no-members)
- [Display all Shared Drives with no organizers](#display-all-shared-drives-with-no-organizers)
- [Display all Shared Drives with a specific organizer](#display-all-shared-drives-with-a-specific-organizer)
- [Display all Shared Drives without a specific organizer](#display-all-shared-drives-without-a-specific-organizer)
- [Manage Shared Drive access](#manage-shared-drive-access)
- [Transfer Shared Drive access](#transfer-shared-drive-access)
- [Display Shared Drive access](#display-shared-drive-access)
  - [Display Shared Drive access for specific Shared Drives](#display-shared-drive-access-for-specific-shared-drives)
  - [Display Shared Drive access for selected Shared Drives](#display-shared-drive-access-for-selected-shared-drives)
  - [Display members of all Shared Drives](#display-members-of-all-shared-drives)
  - [Display external members of all Shared Drives](#display-external-members-of-all-shared-drives)
- [Display ACLs for Shared Drives with no organizers](#display-acls-for-shared-drives-with-no-organizers)
- [Display ACLs for Shared Drives with all organizers outside of your domain](#display-acls-for-shared-drives-with-all-organizers-outside-of-your-domain)
- [Display ACLs for Shared Drives with all ACLs outside of your domain](#display-acls-for-shared-drives-with-all-acls-outside-of-your-domain)
- [Clean up scammed Shared Drives](#clean-up-scammed-shared-drives)

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
         <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<DriveFilePermissionIDEntity> ::=
         <DriveFilePermissionIDList> |
         <JSONData> |
         <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<DrivePermissionsFieldName> ::=
        additionalroles|
        allowfilediscovery|
        deleted|
        displayname|name
        domain|
        emailaddress|
        expirationdate|
        expirationtime|
        id|
        permissiondetails|
        photolink|
        role|
        teamdrivepermissiondetails|
        type|
        withlink
<DrivePermissionsFieldNameList> ::= "<DrivePermissionsFieldName>(,<DrivePermissionsFieldName>)*"

<QueryTeamDrive> ::= <String> See: https://developers.google.com/drive/api/v3/search-parameters
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

<SharedDriveIDEntity> ::=
        <DriveFileItem>|(teamdriveid <DriveFileItem>)|(teamdriveid:<DriveFileItem>)
<SharedDriveNameEntity> ::=
        (teamdrive <SharedDriveName>)|(teamdrive:<SharedDriveName>)
<SharedDriveAdminQueryEntity> ::=
        (teamdriveadminquery <QueryTeamDrive>)|(teamdriveadminquery:<QueryTeamDrive>)

<SharedDriveEntityAdmin> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity> |
        <SharedDriveAdminQueryEntity>

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
## Introduction
A domain administrator with the Drive and Docs administrator privilege can search for Shared Drives or update permissions for Shared Drives
owned by their organization, regardless of the admin's membership in any given Shared Drive.

Three forms of the commands are available:
* `gam action ...` - The administrator named in oauth2.txt is used, domain administrator access implied
* `gam <UserTypeEntity> action ... adminaccess` - The user named in `<UserTypeEntty>` is used, adminaccess indicates that the user is a domain administrator
* `gam <UserTypeEntity> action ...` - The user named in `<UserTypeEntty>` is used, access is limited to drives for which they are an organizer

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
gam show teamdrivethemes
```
## Manage Shared Drives

## Create a Shared Drive
The user that creates a Shared Drive is given the permission role organizer for the Shared Drive,
```
gam [<UserTypeEntity>] create teamdrive <Name>
        [(theme|themeid <String>)|
         ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
        (<SharedDriveRestrictionsSubfieldName> <Boolean>)*
        [hide <Boolean>] [ou|org|orgunit <OrgUnitItem>]
        [errorretries <Integer>] [updateinitialdelay <Integer>] [updateretrydelay <Integer>]
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*) | returnidonly]
        [adminaccess|asadmin]
```
* `themeid` - a Shared Drive themeId obtained from `show teamdrivethemes`
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

By default, the Google Administrator and Shared Drive name and ID values are displayed on stdout.
* `csv [todrive <ToDriveAttribute>*]` - Write Google Administrator, Shared Drive name and ID values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output
* `returnidonly` - Display just the ID of the created Shared Drive as output
When either of these options is chosen, no infomation about Shared Drive restrictions or hiding will be displayed.

To retrieve the Shared Drive ID with `returnidonly`:
```
Linux/MacOS
teamDriveId=$(gam create teamdrive ... returnidonly)
Windows PowerShell
$teamDriveId = & gam create teamdrive ... returnidonly
```

## Bulk Create Shared Drives
Most Shared Drive attributes can't be applied as part of the create, the Drive must be created and then updated with the desired attributes.

As a newly created Drive can't be updated for 30+ seconds; split the operation into two commands: create and update.

Make a CSV file SharedDriveNames.csv with at least one column, name.
```
gam redirect csv ./SharedDrivesCreated.csv multiprocess csv SharedDriveNames.csv gam create teamdrive "~name" csv
```
This will create a three column CSV file SharedDrivesCreated.csv with columns: User,name,id
* There will be a row for each Shared Drive.
* User will be the Google Administrator.

Use the SharedDrivesCreated.csv file to apply the desired options/attributes.
```
gam redirect stdout ./SharedDrivesUpdated.txt multiprocess redirect stderr stdout csv ./SharedDrivesCreated.csv gam update shareddrive "~id" [options/attributes as desired]
```

Make Shared Drives for students
```
StudentSharedDrives.csv
primaryEmail,Name
bob@domain.com,Bob Jones
mary@domain.com,Mary Smith
...

# Create the student Shared Drives
gam redirect stdout ./StudentSharedDrivesCreated.txt multiprocess redirect stderr stdout redirect csv ./StudentSharedDrivesCreated.csv multiprocess csv StudentSharedDrives.csv gam create shareddrive "~Name" csv addcsvdata primaryEmail "~primaryEmail"
# Update attributes/options
gam redirect stdout ./StudentSharedDrivesUpdated.txt multiprocess redirect stderr stdout csv ./StudentSharedDrivesCreated.csv gam update shareddrive "~id" [options/attributes as desired]
# Add ACLs granting the students organizer access to their Shared Drives.
gam redirect stdout ./StudentSharedDrivesAccess.txt multiprocess redirect stderr stdout csv StudentSharedDrivesCreated.csv gam add drivefileacl "~id" user "~primaryEmail" role organizer
```

## Update Shared Drive settings

These commands are used to set basic Shared Drive settings.
```
gam [<UserTypeEntity>] update teamdrive <SharedDriveEntity> [name <Name>]
        [adminaccess|asadmin]
        [(theme|themeid <String>)|
         ([customtheme <DriveFileID> <Float> <Float> <Float>] [color <ColorValue>])]
        (<SharedDriveRestrictionsSubfieldName> <Boolean>)*
        [hide|hidden <Boolean>] [ou|org|orgunit <OrgUnitItem>]
```
* `themeid` - a Shared Drive themeId obtained from `show teamdrivethemes`
* `customtheme` - set the backgroundImageFile property described here:  https://developers.google.com/drive/v3/reference/teamdrives
* `color` - set the Shared Drive color
* `<SharedDriveRestrictionsSubfieldName> <Boolean>` - Set Shared Drive Restrictions
* `hidden <Boolean>` - Set Shared Drive visibility

* `ou|org|orgunit <OrgUnitItem>` - See: https://workspaceupdates.googleblog.com/2022/05/shared-drives-in-organizational-units-open-beta.html

This option is only available when the command is run as an administrator.

## Delete a Shared Drive
```
gam [<UserTypeEntity>] delete teamdrive <SharedDriveEntity>
        [adminaccess|asadmin] [allowitemdeletion]
```
By default, deleting a Shared Drive that contains any files/folders will fail.
The `allowitemdeletion` option allows a Super Admin to delete a non-empty Shared Drive.
This is not reversible, proceed with caution.

## Change Shared Drive visibility
```
gam [<UserTypeEntity>] hide teamdrive <SharedDriveEntity>
gam [<UserTypeEntity>] unhide teamdrive <SharedDriveEntity>
```

## Display Shared Drives
These commands are used to get information about Shared Drives themselves, not the files/folders on the Shared Drives.
```
gam [<UserTypeEntity>] info teamdrive <SharedDriveEntity>
        [adminaccess|asadmin]
        [fields <SharedDriveFieldNameList>] [formatjson]
gam [<UserTypeEntity>] show teamdriveinfo <SharedDriveEntity>
        [adminaccess|asadmin]
        [fields <SharedDriveFieldNameList>] [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam [<UserTypeEntity>] show teamdrives
        [adminaccess|asadmin] [teamdriveadminquery|query <QueryTeamDrive>]
        [matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        [fields <SharedDriveFieldNameList>] [formatjson]
```
By default, all Shared Drives are displayed; use the following options to select a subset of Shared Drives:
* `teamdriveadminquery|query <QueryTeamDrive>` - Use a query to select Shared Drives
* `matchname <REMatchPattern>` - Retrieve Shared Drives with names that match a pattern.
* `orgunit|org|ou <OrgUnitPath>` - Only Shared Drives in the specified Org Unit are selected

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam [<UserTypeEntity>] print teamdrives [todrive <ToDriveAttribute>*]
        [adminaccess|asadmin] [teamdriveadminquery|query <QueryTeamDrive>]
        [matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        [fields <SharedDriveFieldNameList>] [formatjson [quotechar <Character>]]
```
By default, all Shared Drives are displayed; use the following options to select a subset of Shared Drives:
* `teamdriveadminquery|query <QueryTeamDrive>` - Use a query to select Shared Drives
* `matchname <REMatchPattern>` - Retrieve Shared Drives with names that match a pattern.
* `orgunit|org|ou <OrgUnitPath>` - Only Shared Drives in the specified Org Unit are selected

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Examples
Print information about all Shared Drives in the organization.
```
gam print teamdrives
gam user admin@domain.com print teamdrives adminaccess
```
Print information about Shared Drives that have admin@domain.com as a member.
```
gam user admin@domain.com print teamdrives
```

## Display all Shared Drives with no members
```
gam print teamdrives query "memberCount = 0"
```

## Display all Shared Drives with no organizers
```
gam print teamdrives query "organizerCount = 0"
```

## Display all Shared Drives with a specific organizer
Substitute actual email address for `organizer@domain.com`.
```
gam config csv_output_header_filter "id,name" print teamdriveacls pm emailaddress organizer@domain.com role organizer em pma process pmselect
```

## Display all Shared Drives without a specific organizer
Substitute actual email address for `organizer@domain.com`.
```
gam config csv_output_header_filter "id,name" print teamdriveacls pm emailaddress organizer@domain.com role organizer em pma skip pmselect
```

## Display List of Shared Drives in an Organizational Unit other than /
Get the orgUnitID of OU / and use it (without the id:) in the print|show command. Adjust fields as desired.
```
gam info ou / nousers
gam show teamdrives query "orgUnitId!='00gjdgxs2p9cxyz'" fields id,name,orgunit,createdtime
gam print teamdrives query "orgUnitId!='00gjdgxs2p9cxyz'" fields id,name,orgunit,createdtime
```

## Display List of Shared Drives in an Organizational Unit
Get the orgUnitID of the desired OU and use it (without the id:) in the print|show command. Adjust fields as desired.
```
gam info ou <OrgUnitPath> nousers
gam show teamdrives query "orgUnitId='03ph8a2z21rexy'" fields id,name,orgunit,createdtime
gam print teamdrives query "orgUnitId='03ph8a2z21rexy'" fields id,name,orgunit,createdtime
```
Alternative method; `<OrgUnitPath>` defaults to `/`.
```
gam show oushareddrives
        [ou|org|orgunit <OrgUnitPath>]
        [formatjson]
gam print oushareddrives [todrive <ToDriveAttribute>*]
        [ou|org|orgunit <OrgUnitPath>]
        [formatjson [quotechar <Character>]]
```

## Manage Shared Drive access
These commands are used to manage the ACLs on Shared Drives themselves, not the files/folders on the Shared Drives.

### Process single ACLs.
```
gam [<UserTypeEntity>] add drivefileacl <SharedDriveEntityAdmin>
        anyone|(user <UserItem>)|(group <GroupItem>)|(domain <DomainName>)
        (role <DriveFileACLRole>) [withlink|(allowfilediscovery|discoverable [<Boolean>])]
        [expires|expiration <Time>] [sendemail] [emailmessage <String>]
        [showtitles] [nodetails]
        [adminaccess|asadmin]
gam [<UserTypeEntity>] update drivefileacl <SharedDriveEntityAdmin> <DriveFilePermissionIDorEmail>
        (role <DriveFileACLRole>) [expires|expiration <Time>] [removeexpiration [<Boolean>]]
        [adminaccess|asadmin]
        [showtitles] [nodetails]
gam [<UserTypeEntity>] delete drivefileacl <SharedDriveEntityAdmin> <DriveFilePermissionIDorEmail>
        [showtitles]
        [adminaccess|asadmin]
```
By default, when an ACL is added/updated, GAM outputs details of the ACL. The `nodetails` option
suppresses this output.

By default, the file ID is displayed in the output; to see the file name, use the `showtitles`
option; this requires an additional API call per file.

### Process multiple ACLs.
```
gam [<UserTypeEntity>] add permissions <SharedDriveEntityAdmin> <DriveFilePermissionEntity>
        [expires|expiration <Time>] [sendemail] [emailmessage <String>]
        <PermissionMatch>* [<PermissionMatchAction>]
        [adminaccess|asadmin]
gam [<UserTypeEntity>] delete permissions <SharedDriveEntityAdmin> <DriveFilePermissionIDEntity>
        <PermissionMatch>* [<PermissionMatchAction>]
        [adminaccess|asadmin]
```
Permission matching only applies when the `<JSONData>`
variant of `<DriveFilePermissionEntity>` and `<DriveFilePermissionIDEntity>` is used.

When adding permissions from JSON data, there is a default match: `pm not role owner em` that disables ownership changes.
If you want to process all permissions, enter `pm em` to clear the default match.

When adding permissions from JSON data, permissions with `deleted` true are never processed.

When deleting permissions from JSON data, permissions with role `owner` true are never processed.

## Transfer Shared Drive access

These commands are used to transfer ACLs from one Shared Drive to another.
* `copy` - Copy all ACLs from the source Shared Drive to the target Shared Drive. The role of an existing ACL in the target Shared Drive will never be reduced.
* `sync` - Add/delete/update ACLs in the target Shared Drive to match those in the source Shared Drive.
```
gam [<UserTypeEntity>] copy teamdriveacls <SharedDriveEntity> to <SharedDriveEntity>
        [showpermissionsmessages [<Boolean>]]
        [excludepermissionsfromdomains|includepermissionsfromdomains <DomainNameList>]
        (mappermissionsdomain <DomainName> <DomainName>)*
        [adminaccess|asadmin]
gam [<UserTypeEntity>] sync teamdriveacls <SharedDriveEntity> with <SharedDriveEntity>
        [showpermissionsmessages [<Boolean>]]
        [excludepermissionsfromdomains|includepermissionsfromdomains <DomainNameList>]
        (mappermissionsdomain <DomainName> <DomainName>)*
        [adminaccess|asadmin]
```
When `excludepermissionsfromdomains <DomainNameList>` is specified, any ACL that references a domain in `<DomainNameList>` will not be copied.

When `includepermissionsfromdomains <DomainNameList>` is specified, only ACLs that reference a domain in `<DomainNameList>` will be copied.

When `mappermissionsdomain <DomainName> <DomainName>` is specifed, any ACL that references the first `<DomainName>` will be modified
to reference the second `<DonainName>` when copied; the original ACL is not modified. The option can be repeated if multiple domain names are to me mapped.

## Display Shared Drive access

These commands are used to display the ACLs on Shared Drives themselves, not the files/folders on the Shared Drives.

## Display Shared Drive access for specific Shared Drives
```
gam [<UserTypeEntity>] info drivefileacl <SharedDriveEntityAdmin> <DriveFilePermissionIDorEmail>
        [showtitles] [formatjson]
        [adminaccess|asadmin]
gam [<UserTypeEntity>] show drivefileacls <SharedDriveEntityAdmin>
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [showtitles] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [formatjson]
        [adminaccess|asadmin]
gam [<UserTypeEntity>] print drivefileacls <SharedDriveEntityAdmin> [todrive <ToDriveAttribute>*]
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [showtitles] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [formatjson [quotechar <Character>]]
        [adminaccess|asadmin]
```
### Examples:
Find all the organizers and file organizers on the Golgafrincham shared drive in CSV form.
```
 gam print drivefileacls teamdrive "Golgafrincham" pm role organizer em pm role fileorganizer em oneitemperrow
```

By default, all Shared Drives specified are displayed; use the following option to select a subset of those Shared Drives.
* `<PermissionMatch>* [<PermissionMatchAction>] pmselect` - Use permission matching to select Shared Drives; all ACLs are displayed for the selected Shared Drives

By default, all ACLS are displayed; use the following option to select a subset of the ACLS to display.
* `<PermissionMatch>* [<PermissionMatchAction>]` - Use permission matching to display a subset of the ACLs for each Shared Drive; this only applies when `pmselect` is not specified

With `print drivefileacls` or `show drivefileacls formatjson`, the ACLs selected for display are all output on one row/line as a repeating item with the matching Shared Drive id.
When `oneitemperrow` is specified, each ACL is output on a separate row/line with the matching Shared Drive id. This simplifies processing the CSV file with subsequent Gam commands.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display members of all Shared Drives
```
gam config csv_output_header_drop_filter "User,createdTime,permission.photoLink,permission.permissionDetails" redirect csv ./SharedDriveMembers.csv print shareddriveacls oneitemperrow
```

## Display external members of all Shared Drives
Replace `<InternalDomainList>` with your list of internal domains.
```
gam config csv_output_header_drop_filter "User,createdTime,permission.photoLink,permission.permissionDetails" redirect csv ./SharedDriveExternalMembers.csv print shareddriveacls pm notdomainlist <InternalDomainList> em oneitemperrow
```

## Display Shared Drive access for selected Shared Drives
```
gam [<UserTypeEntity>] show teamdriveacls
        [adminaccess|asadmin] [teamdriveadminquery|query <QueryTeamDrive>]
        [matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        [user|group <EmailAddress> [checkgroups]] (role|roles <SharedDriveACLRoleList>)*
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        [shownopermissionsdrives false|true|only]
        [formatjson]

gam [<UserTypeEntity>] print teamdriveacls [todrive <ToDriveAttribute>*]
        [adminaccess|asadmin] [teamdriveadminquery|query <QueryTeamDrive>]
        [matchname <REMatchPattern>] [orgunit|org|ou <OrgUnitPath>]
        [user|group <EmailAddress> [checkgroups]] (role|roles <SharedDriveACLRoleList>)*
        <PermissionMatch>* [<PermissionMatchAction>] [pmselect]
        [oneitemperrow] [<DrivePermissionsFieldName>*|(fields <DrivePermissionsFieldNameList>)]
        [shownopermissionsdrives false|true|only]
        [formatjson [quotechar <Character>]]

```
By default, all Shared Drives are displayed; use the following options to select a subset of Shared Drives:
* `teamdriveadminquery|query <QueryTeamDrive>` - Use a query to select Shared Drives
* `matchname <REMatchPattern>` - Retrieve Shared Drives with names that match a pattern.
* `orgunit|org|ou <OrgUnitPath>` - Only Shared Drives in the specified Org Unit are selected
* `<PermissionMatch>* [<PermissionMatchAction>] pmselect` -  Use permission matching to select Shared Drives; all ACLs are displayed for the selected Shared Drives

By default, Shared Drives with no permissions are not displayed; use the `shownopermissionsdrives` to control whether
Shared Drives with no permissions are displayed.
* `false` - Do not display Shared Drives with no permissions; this is the default
* `true` - Display Shared Drives with no permissions in addition to Shared Drives with permissions
* `only` - Display only Shared Drives with no permissions

By default, all ACLS are displayed; use the following options to select a subset of the ACLS to display.
* `user|group <EmailAddress> [checkgroups]` - Display ACLs for the specified `<EmailAddress>` only; if there is no ACL for `<EmailAddress>` and `checkgroups` is specified, display any ACLs for groups that have `<EmailAddress>` as a member.
* `role|roles <SharedDriveACLRoleList>` - Display ACLs for the specified roles only.
* `<PermissionMatch>* [<PermissionMatchAction>]` - Use permission matching to display a subset of the ACLs for each Shared Drive; this only applies when `pmselect` is not specified

With `print teamdriveacls` or `show teamdrivecls formatjson`, the ACLs selected for display are all output on one row/line as a repeating item with the matching Shared Drive id.
When `oneitemperrow` is specified, each ACL is output on a separate row/line with the matching Shared Drive id and name. This simplifies processing the CSV file with subsequent Gam commands.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Examples
Find all organizers and viewers on the shared drive Heart of Gold in CSV form.
```
 gam print teamdriveacls matchname "Heart of Gold" role organizer,reader oneitemperrow
```

Print ACLs for all Shared Drives in the organization created after November 1, 2017.
```
gam print teamdriveacls teamdriveadminquery "createdTime > '2017-11-01T00:00:00'"
```

Print ACLs for all Shared Drives in the organization with foo@bar.com as an organizer.
```
gam print teamdriveacls user foo@bar.com role organizer
```

Print ACLs for all Shared Drives in the organization with foo@bar.com or groups that contain foo@bar.com as a reader.
```
gam print teamdriveacls user foo@bar.com role reader checkgroups
```

## Display ACLs for Shared Drives with no organizers
### For all Shared Drives
```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsNoOrganizers.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted query "organizerCount = 0"

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsNoOrganizers.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted query "organizerCount = 0" oneitemperrow
```
### For selected Shared Drives
Create a CSV file TeamDrives.csv with at least two columns (id, name) for the selected Shared Drives.
```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsNoOrganizers.csv multiprocess csv ./SharedDrives.csv gam print drivefileacls "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted pm role organizer em pma skip pmselect

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsNoOrganizersOIPR.csv multiprocess csv ./SharedDrives.csv gam print drivefileacls "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted pm role organizer em pma skip pmselect oneitemperrow
```

## Display ACLs for Shared Drives with all organizers outside of your domain
### For all Shared Drives
```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsAllExternalOrganizers.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted role organizer pm role organizer domainlist domain.com,... em pma skip pmselect

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsAllExternalOrganizers.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted role organizer pm role organizer domainlist domain.com,... em pma skip pmselect
```
### For selected Shared Drives
Create a CSV file TeamDrives.csv with at least two columns (id, name) for the selected Shared Drives.
```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsAllExternalOrganizers.csv multiprocess csv ./SharedDrives.csv gam print drivefileacls "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted pm role organizer domainlist domain.com,... em pma skip pmselect

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsAllExternalOrganizersOIPR.csv multiprocess csv ./SharedDrives.csv gam print drivefileacls "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted pm role organizer domainlist domain.com,... em pma skip pmselect
```

## Display ACLs for Shared Drives with all ACLs outside of your domain
### For all Shared Drives
Include a permission match `pm domainlist domain.com,... em` that lists your internal domain(s).
```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsAllExternal.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted pm domainlist domain.com,... em pma skip pmselect

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsAllExternalOIPR.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted pm domainlist domain.com,... em pma skip pmselect oneitemperrow
```
### For selected Shared Drives
Create a CSV file TeamDrives.csv with at least two columns (id, name) for the selected Shared Drives.

Include a permission match `pm domainlist domain.com,... em` that lists your internal domain(s).
```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsAllExternal.csv multiprocess csv ./SharedDrives.csv gam print drivefileacls "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted pm domainlist domain.com,... em pma skip pmselect

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsAllExternalOIPR.csv multiprocess csv ./SharedDrives.csv gam print drivefileacls "~id" addtitle "~name" fields id,domain,emailaddress,role,type,deleted pm domainlist domain.com,... em pma skip pmselect oneitemperrow
```

## Clean up scammed Shared Drives

There is a scam where people are offered "Free Google Drive Space"; someone from your domain signed up for "Free Google Drive Space" and gave their domain credentials.
The scammers build a Shared Drive under those credentials, give themseleves access and then delete the original domain users credentials.
You are now hosting "Free Google Drive Space" for multiple non-domain users on this Shared Drive.

### Get scammed Shared Drive ACLs
Use the commands in [Display ACLs for Shared Drives with all ACLs outside of your domain](#display-acls-for-shared-drives-with-all-acls-outside-of-your-domain)
to get the Shared Drive ACLs for the scammed Shared Drives.

```
One row per Shared Drive, all ACLs on the same row
gam redirect csv ./SharedDriveACLsAllExternal.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted pm domainlist domain.com,... em pma skip pmselect

A row per Shared Drive/ACL combination
gam redirect csv ./SharedDriveACLsAllExternalOIPR.csv print teamdriveacls fields id,domain,emailaddress,role,type,deleted pm domainlist domain.com,... em pma skip pmselect oneitemperrow
```

### Add an organizer from your domain
Sustitute an appropriate value for `admin@domain.com`.
```
gam redirect stdout ./AddOrganizer.txt multiprocess redirect stderr stdout csv ./SharedDriveACLsAllExternal.csv gam add drivefileacl teamdriveid "~id" user admin@domain.com role organizer
```

### Delete non domain ACLs
Inspect `SharedDriveACLsAllExternal.csv` and verify that the list makes sense; delete any rows that could potentially be legitimate. If you delete a row,
you must delete all rows in `SharedDriveACLsAllExternalOIPR.csv` that have the same Shared Drive id value.

This will disable all non-domain users access to the Shared Drive.
```
gam redirect stdout ./DeleteExternalACLs.txt multiprocess redirect stderr stdout csv ./SharedDriveACLsAllExternalOIPR.csv gam delete drivefileacl teamdriveid "~id" "id:~~permission.id~~"
```

### Delete the Shared Drives
The `allowitemdeletion` option allows deletion of non-empty Shared Drives. This option requires a Super Admin user.

This is not reversible, proceed with caution.
```
gam redirect stdout ./DeleteSharedDrives.txt multiprocess redirect stderr stdout csv ./SharedDriveACLsAllExternal.csv gam delete teamdrive "~id" allowitemdeletion
```
