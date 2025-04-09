# Collections of Users
- [Python Regular Expressions](Python-Regular-Expressions) Search function
- [Definitions](#definitions)
- [User Type Entity](#user-type-entity)
  - [All non-suspended Users](#all-non-suspended-users)
  - [All suspended Users](#all-suspended-Users)
  - [All non-suspended and suspended Users](#all-non-suspended-and-suspended-users)
  - [A single User](#a-single-user)
  - [A list of Users](#a-list-of-users)
  - [The admin user referenced in oauth2.txt](#the-admin-user-referenced-in-oauth2txt)
  - [Users in the domains `<DomainNameList>`](#users-in-the-domains-domainnamelist)
  - [Users directly in the group `<GroupItem>`](#users-directly-in-the-group-groupitem)
  - [Users directly in the groups `<GroupList>`](#users-directly-in-the-groups-grouplist)
  - [Users directly and indirectly in the group `<GroupItem>`](#users-directly-and-indirectly-in-the-group-groupitem)
  - [Users directly and indirectly in the groups `<GroupList>`](#users-directly-and-indirectly-in-the-groups-grouplist)
  - [Selected Users from groups](#selected-users-from-groups)
  - [Users directly in the Cloud Identity group `<GroupItem>`](#users-directly-in-the-cloud-identity-group-groupitem)
  - [Users directly in the Cloud Identity groups `<GroupList>`](#users-directly-in-the-cloud-identity-groups-grouplist)
  - [Selected Users from Cloud Identity groups](#selected-users-from-cloud-identity-groups)
  - [Users directly in the Organization Unit `<OrgUnitItem>`](#users-directly-in-the-organization-unit-orgunititem)
  - [Users in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units](#users-in-the-organization-unit-orgunititem-and-all-of-its-sub-organization-units)
  - [Users directly in the Organization Units `<OrgUnitList>`](#users-directly-in-the-organization-units-orgunitlist)
  - [Users in the Organization Units `<OrgUnitList>` and all of their sub Organization Units](#users-in-the-organization-units-orgunitlist-and-all-of-their-sub-organization-units)
  - [All of the students and teachers in the courses specified in `<CourseIDList>`](#all-of-the-students-and-teachers-in-the-courses-specified-in-courseidlist)
  - [All of the students in the courses specified in `<CourseIDList>`](#all-of-the-students-in-the-courses-specified-in-courseidlist)
  - [All of the teachers in the courses specified in `<CourseIDList>`](#all-of-the-teachers-in-the-courses-specified-in-courseidlist)
  - [All Users with any of the licenses specified in `<SKUIDList>`](#all-users-with-any-of-the-licenses-specified-in-skuidlist)
  - [Users that match a query](#users-that-match-a-query)
  - [Users that match any query in a list of queries](#users-that-match-any-query-in-a-list-of-queries)
  - [Users in a flat file/Google Doc/Google Cloud Storage Object](#users-in-a-flat-filegoogle-docgoogle-cloud-storage-object)
  - [Selected users in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object](#selected-users-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [Users from groups/OUs/courses in a flat file/Google Doc/Google Cloud Storage Object](#users-from-groupsouscourses-in-a-flat-filegoogle-docgoogle-cloud-storage-object)
  - [Users from groups/OUs/courses in a CSV file/Google Sheet/Google Doc](#users-from-groupsouscourses-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [Users directly in or from groups/OUs/courses in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object](#users-directly-in-or-from-groupsouscourses-in-a-csv-filegoogle-sheetgoogle-docgoogle-cloud-storage-object)
  - [Users from data fields identified in a `csvkmd` argument](#users-from-data-fields-identified-in-a-csvkmd-argument)
- [Examples using CSV files and Google Sheets to update the membership of a group](#examples-using-csv-files-and-google-sheets-to-update-the-membership-of-a-group)
- [Examples using CSV files to print users from groups](#examples-using-CSV-files-to-print-users-from-groups)
- [Examples using multiple queries](#examples-using-multiple-queries)

## Definitions
* [Basic Items](Basic-Items)

* [List Items](List-Items)

* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
```
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>

<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)

<SheetEntity> ::= <String>|id:<Number>
<UserGoogleSheet> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>) <SheetEntity>
```
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
<DriveFileList> ::= "<DriveFileItem>(,<DriveFileItem>)*"
<DriveFileName> ::= <String>
<DriveFileIDEntity> ::=
        (<DriveFileItem>)|(id( |:)<DriveFileItem>)|(ids( |:)<DriveFileList>)
<DriveFileNameEntity> ::=
        (drivefilename <DriveFileName>)|(drivefilename:<DriveFileName>)|
        (anydrivefilename <DriveFileName>)|(anydrivefilename:<DriveFileName>)
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<SharedDriveIDEntity> ::= (teamdriveid <DriveFileItem>) | (teamdriveid:<DriveFileItem>)
<SharedDriveNameEntity> ::= (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
<SharedDriveFileNameEntity> ::= (teamdrivefilename <DriveFileName>) | (teamdrivefilename:<DriveFileName>)
<SharedDriveEntity> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>

<UserTypeEntity> ::=
        (all users|users_ns|users_susp|users_ns_susp)|
        (user <UserItem>)|
        (users <UserList>)|
        (oauthuser)
        (domains|domains_ns|domains_susp <DomainNameList>)|
        (group|group_ns|group_susp|group_inde <GroupItem>)|
        (groups|groups_ns|groups_susp|groups_inde <GroupList>)|
        (group_inde <GroupItem>)|(groups_inde <GroupList>)|
        (group_users|group_users_ns|group_users_susp <GroupList>
                [members] [managers] [owners]
                [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end)|
        (group_users_select <GroupList>
                [members] [managers] [owners]
                [notsuspended|suspended] [notarchived|archived]
                [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end)|
        (ou|ou_ns|ou_susp <OrgUnitItem>)|
        (ou_and_children|ou_and_children_ns|ou_and_children_susp <OrgUnitItem>)|
        (ous|ous_ns|ous_susp <OrgUnitList>)|
        (ous_and_children|ous_and_children_ns|ous_and_children_susp <OrgUnitList>)|
        (courseparticipants <CourseIDList>)|
        (students <CourseIDList>)|
        (teachers <CourseIDList>)|
        (license|licenses|licence|licences <SKUIDList>)|
        (query <QueryUser>)|
        (queries <QueryUserList>)|
        (file
            ((<FileName> [charset <Charset>])|
             (gdoc <UserGoogleDoc>)|
             (gcsdoc <StorageBucketObjectName>))
            [delimiter <Character>])|
        (csvfile
            ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
             (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
             (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
             (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
             (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
            [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>][quotechar <Character>]
            [endcsv|(fields <FieldNameList>)]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [delimiter <Character>])|
        (datafile
            users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|
            ous_and_children|ous_and_children_ns|ous_and_children_susp|
            courseparticipants|students|teachers
            ((<FileName> [charset <Charset>])|
              (gdoc <UserGoogleDoc>)|
              (gcsdoc <StorageBucketObjectName>))
             [delimiter <Character>])|
        (csvdatafile
            users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|
            ous_and_children|ous_and_children_ns|ous_and_children_susp|
            courseparticipants|students|teachers
            ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
              (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
              (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
              (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
              (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
            [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>][quotechar <Character>]
            [endcsv|(fields <FieldNameList>)]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [delimiter <Character>])|
        (csvkmd
            users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|
            ous_and_children|ous_and_children_ns|ous_and_children_susp|
            courseparticipants|students|teachers
            ((<FileName>|
              (gsheet <UserGoogleSheet>)|
              (gdoc <UserGoogleDoc>)|
              (gcscsv <StorageBucketObjectName>)|
              (gcsdoc <StorageBucketObjectName>))
             [charset <Charset>] [columndelimiter <Character>] [noescapechar <Boolean>][quotechar <Character>] [fields <FieldNameList>])
            keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
            subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
            (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [datafield <FieldName>(:<FieldName>)* [delimiter <Character>]])
        (csvdata <FieldName>(:<FieldName>*))
```

## User Type Entity

Use these options to select users for GAM commands.

## All non-suspended Users
* `all users`
* `all users_ns`

## All suspended Users
* `all users_susp`

## All non-suspended and suspended Users
* `all users_ns_susp`

## A single User
* `user <UserItem>`

## A list of Users
* `users <UserList>`

## The admin user referenced in oauth2.txt
* `oauthuser`

## Users in the domains `<DomainNameList>`
* `domains|domains_ns|domains_susp <DomainNameList>`
    * `domains` - All users
    * `domains_ns` - Non-suspended users
    * `domains_susp` - Suspended users

## Users directly in the group `<GroupItem>`
* `group|group_ns|group_susp <GroupItem>`
    * `group` - All user members
    * `group_ns` - Non-suspended user members
    * `group_susp` - Suspended user members

## Users directly in the groups `<GroupList>`
* `groups|groups_ns|groups_susp <GroupList>`
    * `groups` - All user members
    * `groups_ns` - Non-suspended user members
    * `groups_susp` - Suspended user members

## Users directly and indirectly in the group `<GroupItem>`
    * `group_inde` - All user members including those from all subgroups

## Users directly and indirectly in the groups `<GroupList>`
    * `groups_inde` - All user members including those from all subgroups

## Selected Users from groups
* `group_users|group_users_ns|group_users_susp <GroupList> [members] [managers] [owners] [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end`
    * `group_users` - All user members
    * `group_users_ns` - Non-suspended user members
    * `group_users_susp` - Suspended user members
    * `[members] [managers] [owners]` - The desired roles; if roles are not specified, all roles are included
    * `primarydomain` - Select Users from the primary domain
    * `domains <DomainNameList>` - Select Users from the list of domains
    * `recursive` - Select Users from all subgroups; do not select Users from a member of type CUSTOMER (all users in a domain); GAM performs the recursion
    * `includederivedmembership` - Select Users from all subgroups; do select Users from a member of type CUSTOMER (all users in a domain); the API performs the recursion but produces inconsistent results, use with caution
    * `end` - Terminate the selection
* `group_users_select <GroupList> [members] [managers] [owners] [notsuspended|suspended] [notarchived|archived] [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end`
    * `[members] [managers] [owners]` - The desired roles; if roles are not specified, all roles are included
    * By default, memebers of all statuses are included
      * `notsuspended` - Do not include suspended users, this is common
      * `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users
      * `notarchived` - Do not include archived members
      * `archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
      * `notsuspended notarchived` - Do not include suspended and archived members
      * `suspended archived` - Include only suspended or archived members
      * `notsuspended archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
      * `suspended notarchived` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users
    * `primarydomain` - Select Users from the primary domain
    * `domains <DomainNameList>` - Select Users from the list of domains
    * `recursive` - Select Users from all subgroups; do not select Users from a member of type CUSTOMER (all users in a domain); GAM performs the recursion
    * `includederivedmembership` - Select Users from all subgroups; do select Users from a member of type CUSTOMER (all users in a domain); the API performs the recursion but produces inconsistent results, use with caution
    * `end` - Terminate the selection

## Users directly in the Cloud Identity group `<GroupItem>`
* `cigroup <GroupItem>`
    * `cigroup` - All user members

## Users directly in the Cloud Identity groups `<GroupList>`
* `cigroups <GroupList>`
    * `cigroups` - All user members

## Selected Users from Cloud Identity groups
* `cigroup_users <GroupList> [members] [managers] [owners>] [recursive] end`
    * `cigroup_users` - All user members
    * `[members] [managers] [owners]` - The desired roles; if roles are not specified, all roles are included
    * `recursive` - Select Users from all subgroups; do not select Users from a member of type CUSTOMER (all users in a domain); GAM performs the recursion
    * `end` - Terminate the selection

## Users directly in the Organization Unit `<OrgUnitItem>`
* `ou|ou_ns|ou_susp <OrgUnitItem>`
    * `ou` - All users
    * `ou_ns` - Non-Suspended users
    * `ou_susp` - Suspended users

## Users in the Organization Unit `<OrgUnitItem>` and all of its sub Organization Units
* `ou_and_children|ou_and_children_ns|ou_and_children_susp <OrgUnitItem>`
    * `ou_and_children` - All  users
    * `ou_and_children_ns` - Non-suspended users
    * `ou_and_children_susp` - Suspended users

## Users directly in the Organization Units `<OrgUnitList>`
* `ous|ous_ns|ous_susp <OrgUnitList>` - Users directly in the Organization Units `<OrgUnitList>`
    * `ous` - All users
    * `ous_ns` - Non-suspended users
    * `ous_susp` - Suspended users

`<OrgUnitList>` may require special quoting based on whether the OUs contain spaces, commas or single quotes.

For quoting rules, see: [List Quoting Rules](Command-Line-Parsing)

## Users in the Organization Units `<OrgUnitList>` and all of their sub Organization Units
* `ous_and_children|ous_and_children_ns|ous_and_children_susp <OrgUnitList>` - Users in the Organization Units `<OrgUnitList>` and all of their sub Organization Units
    * `ous_and_children` - All users
    * `ous_and_children_ns` - Non-suspended users
    * `ous_and_children_susp` - Suspended users

`<OrgUnitList>` may require special quoting based on whether the OUs contain spaces, commas or single quotes.

For quoting rules, see: [List Quoting Rules](Command-Line-Parsing)

## All of the students and teachers in the courses specified in `<CourseIDList>`
* `courseparticipants <CourseIDList>`

## All of the students in the courses specified in `<CourseIDList>`
* `students <CourseIDList>`

## All of the teachers in the courses specified in `<CourseIDList>`
* `teachers <CourseIDList>`

## All Users with any of the licenses specified in `<SKUIDList>`
* `license|licenses|licence|licences <SKUIDList>`

## Users that match a query
* `query <QueryUser>`

See https://developers.google.com/admin-sdk/directory/v1/guides/search-users

## Users that match any query in a list of queries
* `queries <QueryUserList>`

See https://developers.google.com/admin-sdk/directory/v1/guides/search-users

`<QueryUserList>` may require special quoting based on whether the queries contain spaces, commas or single quotes.

For quoting rules, see: [List Quoting Rules](Command-Line-Parsing)

Note that the results are all users who match one or more of the queries. In other words this is "OR" logic, and you get the union of all matching results.

## Users in a flat file/Google Doc/Google Cloud Storage Object
```
file
   ((<FileName> [charset <Charset>])|
    (gdoc <UserGoogleDoc>)|
    (gcsdoc <StorageBucketObjectName>))
   [delimiter <Character>]
```
* `<FileName>` - A flat file containing a single User per row
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gdoc <UserGoogleDoc>` - A Google Doc containing a single User per row
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing a single User per row
* `delimiter <Character>` - There are multiple Users per row separated by `<Character>`; if not specified, there is single user per row

## Selected users in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
csvfile
   ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
    (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
    (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
    (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
    (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
   [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>][quotechar <Character>]
   [endcsv|(fields <FieldNameList>)]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
   [delimiter <Character>]
```
* `<FileName>(:<FieldName>)+` - A CSV file and the one or more columns that contain Users
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet(:<FieldName>)+ <UserGoogleSheet>` - A Google Sheet and the one or more columns that contain Users
* `gdoc(:<FieldName>)+ <UserGoogleDoc>` - A Google Doc and the one or more columns that contain Users
* `gcscsv(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain Users
* `gcsdoc(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain Users
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote character is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `delimiter <Character>` - There are multiple Users per column separated by `<Character>`; if not specified, there is single user per column

## Users from groups/OUs/courses in a flat file/Google Doc/Google Cloud Storage Object
```
datafile
   users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|
   ous_and_children|ous_and_children_ns|ous_and_children_susp|
   courseparticipants|students|teachers
   ((<FileName> [charset <Charset>])|
     (gdoc <UserGoogleDoc>)|
     (gcsdoc <StorageBucketObjectName>))
    [delimiter <Character>]
```
* `users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|ous_and_children|ous_and_children_ns|ous_and_children_susp|courseparticipants|students|teachers` - The type of item in the file
* `<FileName>` - A flat file containing rows of the type of item specified
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gdoc <UserGoogleDoc>` - A Google Doc containing rows of the type of item specified
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing rows of the type of item specified
* `delimiter <Character>` - There are multiple items per row separated by `<Character>`; if not specified, there is single item per row

## Users from groups/OUs/courses in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
csvdatafile
   users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|
   ous_and_children|ous_and_children_ns|ous_and_children_susp|
   courseparticipants|students|teachers
   ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
     (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
     (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
     (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
     (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
   [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>][quotechar <Character>]
   [endcsv|(fields <FieldNameList>)]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
   [delimiter <Character>]
```
* `users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|ous_and_children|ous_and_children_ns|ous_and_children_susp|courseparticipants|students|teachers` - The type of item in the file
* `<FileName>(:<FieldName>)+` - A CSV file and the one or more columns contain the type of item specified
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet(:<FieldName>)+ <UserGoogleSheet>` - A Google Sheet and the one or more columns contain the type of item specified
* `gdoc(:<FieldName>)+ <UserGoogleDoc>` - A Google Doc and the one or more columns contain the type of item specified
* `gcscsv(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns contain the type of item specified
* `gcsdoc(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns contain the type of item specified
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote character is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `delimiter <Character>` - There are multiple Users per column separated by `<Character>`; if not specified, there is single user per column

## Users directly in or from groups/OUs/courses in a CSV file/Google Sheet/Google Doc/Google Cloud Storage Object
```
csvkmd
   users|groups|groups_ns|groups_susp|groups_inde|ous|ous_ns|ous_susp|
   ous_and_children|ous_and_children_ns|ous_and_children_susp|
   courseparticipants|students|teachers
   ((<FileName>|
     (gsheet <UserGoogleSheet>)|
     (gdoc <UserGoogleDoc>)|
     (gcscsv <StorageBucketObjectName>)|
     (gcsdoc <StorageBucketObjectName>))
    [charset <Charset>] [columndelimiter <Character>] [noescapechar <Boolean>][quotechar <Character>] [fields <FieldNameList>])
   keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
   subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
   (matchfield|skipfield <FieldName> <RESearchPattern>)*
            [datafield <FieldName>(:<FieldName>)* [delimiter <Character>]]
```
* `users|groups|groups_ns_|groups_susp|groups_inde|ous|ous_ns|ous_susp|ous_and_children|ous_and_children_ns|ous_and_children_susp|courseparticipants|students|teachers` - The type of item in the file
* `<FileName>` - A CSV file containing rows with columns of the type of item specified
  * `charset <Charset>` - The character aset of the file if it isn't UTF-8
* `gsheet <UserGoogleSheet>` - A Google Sheet containing rows with columns of the type of item specified
* `gdoc <UserGoogleDoc>` - A Google Doc containing rows with columns of the type of item specified
* `gcscsv <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object with columns of the type of item specified
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object with columns of the type of item specified
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote character is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>])+`
    * `keyfield <FieldName>` - The column containing key values
    * `[keypattern <RESearchPattern>] [keyvalue <RESubstitution>]` - Allows transforming the value(s) in the `keyfield` column. If only `keyvalue <RESubstitution>` is specified, all instances of `<FieldName>` in `keyvalue <RESubstitution>` will be replaced by the item value. If `keypattern <RESearchPattern>` is specified, the item value is matched against `<RESearchPattern>` and the matched segments are substituted into `keyvalue <RESubstitution>`
    * `delimiter <Character>` - There are multiple values per keyfield column separated by `<Character>`; if not specified, there is single value per keyfield column
* `(subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>])*`
    * `subkeyfield <FieldName>` - The column containing subkey values
    * `[keypattern <RESearchPattern>] [keyvalue <RESubstitution>]` - Allows transforming the value(s) in the `subkeyfield` column. If only `keyvalue <RESubstitution>` is specified, all instances of `<FieldName>` in `keyvalue <RESubstitution>` will be replaced by the item value. If `keypattern <RESearchPattern>` is specified, the item value is matched against `<RESearchPattern>` and the matched segments are substituted into `keyvalue <RESubstitution>`
    * `delimiter <Character>` - There are multiple values per subkeyfield column separated by `<Character>`; if not specified, there is single value per subkeyfield column
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `(datafield <FieldName>(:<FieldName)* [delimiter <Character>])*`
    * `datafield <FieldName>(:<FieldName)*` - The column(s) containing data values
    * `delimiter <Character>` - There are multiple values per datafield column separated by `<Character>`; if not specified, there is single value per datafield column

## Users from data fields identified in a `csvkmd` argument
* `csvdata <FieldName>(:<FieldName>*)`

## Examples using CSV files and Google Sheets to update the membership of a group

### Example 1
The file Users.csv has a single column of email addresses, there is no header row.
```
user1@domain.com
user2@domain.com
...

gam update group group@domain.com sync members file Users.csv
```

The Google Sheet `user@domain.com <DriveFileID> <SheetEntity>` has a single column of email addresses, there is no header row.
Define an implicit header with the `fields Email` option.
```
user1@domain.com
user2@domain.com
...

gam update group group@domain.com sync members csvfile gsheet:Email user@domain.com <DriveFileID> <SheetEntity> fields Email
```

The Google Doc `user@domain.com <DriveFileID>` has a single column of email addresses, there is no header row.
```
user1@domain.com
user2@domain.com
...

gam update group group@domain.com sync members file gdoc user@domain.com <DriveFileID>
```

### Example 2
The CSV file Users.csv has one column of email addresses labelled Email.
```
Email
user1@domain.com
user2@domain.com
...

gam update group group@domain.com sync members csvfile Users.csv:Email
```

The Google Sheet `user@domain.com <DriveFileID> <SheetEntity>` has one column of email addresses labelled Email.
```
Email
user1@domain.com
user2@domain.com
...

gam update group group@domain.com sync members csvfile gsheet:Email user@domain.com <DriveFileID> <SheetEntity>
```

### Example 3
The CSV file Users.csv has two columns of email addresses labelled Email1 and Email2.
```
Email1,Email2
user1@domain.com,user2@domain.com
user3@domain.com,user4@domain.com
...

gam update group group@domain.com sync members csvfile Users.csv:Email1:Email2
```

The Google Sheet `user@domain.com <DriveFileID> <SheetEntity>` has two columns of email addresses labelled Email1 and Email2.
```
Email1,Email2
user1@domain.com,user2@domain.com
user3@domain.com,user4@domain.com
...

gam update group group@domain.com sync members csvfile gsheet:Email1:Email2 user@domain.com <DriveFileID> <SheetEntity>
```

### Example 4
The file Groups.txt has a single column of group email addresses, there is no header row.
You want to sync with the members of those groups.
```
group1@domain.com
group2@domain.com
...

gam update group group@domain.com sync members datafile groups Groups.txt
```

The Google Doc `user@domain.com <DriveFileID>` has a single column of group email addresses, there is no header row.
You want to sync with the members of those groups.
```
group1@domain.com
group2@domain.com
...

gam update group group@domain.com sync members datafile groups gdoc user@domain.com <DriveFileID>
```

### Example 5
The CSV file Groups.csv has a single column of group email addresses labelled Group.
You want to sync with the members of those groups.
```
Group
group1@domain.com
group2@domain.com
...

gam update group group@domain.com sync members csvdatafile groups Groups.csv:Group
```

The Google Sheet `user@domain.com <DriveFileID> <SheetEntity>` has a single column of group email addresses labelled Group.
You want to sync with the members of those groups.
```
Group
group1@domain.com
group2@domain.com
...

gam update group group@domain.com sync members csvdatafile groups gsheet:Group user@domain.com <DriveFileID> <SheetEntity>
```

### Example 6
The CSV file GroupMembers.csv has headers: group,role,email

Each row contains a group email address, member role (OWNER, MEMBER, MANAGER) and a member email address.

The following command will synchronize the membership for all groups and roles.
```
gam redirect stdout ./MemberUpdates.txt redirect stderr stdout update group csvkmd GroupMembers.csv keyfield group subkeyfield role datafield email sync csvdata email
```

The Google Sheet `user@domain.com <DriveFileID> <SheetEntity>` has headers: group,role,email

Each row contains a group email address, member role (OWNER, MEMBER, MANAGER) and a member email address.

The following command will synchronize the membership for all groups and roles.
```
gam redirect stdout ./MemberUpdates.txt redirect stderr stdout update group csvkmd gsheet user@domain.com <DriveFileID> <SheetEntity> keyfield group subkeyfield role datafield email sync csvdata email
```

## Examples using CSV files to print users from groups

You want to print the membership of a collection of parent groups at your school based on graduation year.

### Example 1
The CSV File Group.csv has exactly the data you want, `keypattern` and `keyvalue` are not required.
```
Group
2020-parents@domain.com
2021-parents@domain.com
...
```
For each row, the value from the Group column is used as the group name.
```
gam csvkmd groups Group.csv keyfield Group print users
```

### Example 2
The CSV File GradYear.csv has graduation years; you have to convert GradYear to group name `GradYear-parents@domain.com`, `keyvalue` is required.
```
GradYear
2020
2021
...
```
For each row, the value from the GradYear column replaces the keyField name in the `keyvalue` argument and that value is used as the group name.
```
gam csvkmd group GradYear.csv keyfield GradYear keyvalue GradYear-parents@domain.com print users
```

### Example 3
The CSV File GradYear.csv has graduation years; you have to convert GradYear to group name `LastTwoDigitsOfGradYear-parents@domain.com`, `keypattern` and `keyvalue` are required.
```
GradYear
2020
2021
...
```
For each row, the value from the GradYear column is matched against the `keypattern` and the matched segments are substituted into the `keyvalue` argument and that value is used as the group name.
```
gam csvkmd group GradYear.csv keyfield GradYear keypattern '20(..)' keyvalue '\1-parents@domain.com' print users
```

## Examples using multiple queries

### Example 1
Print users who are specialists or technicians:
```
gam queries "orgTitle=Specialist,orgTitle=Technician" print users allfields
```

### Example 2
Print users who are have the title Manager in the sales org or anyone in the marketing org:
```
gam queries "\"orgName='Sales Org' orgTitle=Manager\",\"orgName='Marketing Org'\"" print users allfields
````

### Example 3
Print users in either of two Org Units that contain spaces in their names.
```
gam queries "\"orgUnitPath='/Students/Middle School/2021'\",\"orgUnitPath='/Students/Middle School/2020'\"" print users allfields
```

This is equivaluent to:
```
gam ous "'/Students/Middle School/2021','/Students/Middle School/2020'" print users allfields
```
