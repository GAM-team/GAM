# Collections of Items
- [Python Regular Expressions](Python-Regular-Expressions) Search function
- [Definitions](#definitions)
- [ListSelector](#listselector)
- [FileSelector](#fileselector)
- [CSVFileSelector](#csvfileselector)
- [CSVkmdSelector](#csvkmdselector)
- [CSVSubkeySelector](#csvsubkeyselector)
- [CSVDataSelector](#csvdataselector)
- [Named Collections](#named-collections)
- [Examples](#examples)

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
<UserGoogleSheet> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>) <SheetEntity>

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |
```
## ListSelector
A list of items
```
<Item> ::= <String>
<ItemList> ::= "<Item>(,<Item>)*"
<ListSelector> ::= list <ItemList>
```

## FileSelector
A flat file containing a single Item per row.
```
<FileSelector> ::=
        file ((<FileName> [charset <Charset>])|
              (gdoc <UserGoogleDoc>)|
              (gcsdoc <StorageBucketObjectName>))
             [delimiter <Character>]
```
* `<FileName>` - A flat file containing Items
* `gdoc <UserGoogleDoc>` - A Google Doc containing Items
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing Items
* `delimiter <Character>` - There are multiple Items per row separated by `<Character>`; if not specified, there is single item per row

## CSVFileSelector
A CSV file with one or more columns per row that contain Items.
```
<CSVFileSelector> ::=
        csvfile ((<FileName>(:<FieldName>)+ [charset <Charset>] )|
                 (gsheet(:<FieldName>)+ <UserGoogleSheet>)|
                 (gdoc(:<FieldName>)+ <UserGoogleDoc>)|
                 (gcscsv(:<FieldName>)+ <StorageBucketObjectName>)|
                 (gcsdoc(:<FieldName>)+ <StorageBucketObjectName>))
                [warnifnodata] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
                [endcsv|(fields <FieldNameList>)]
                (matchfield|skipfield <FieldName> <RESearchPattern>)*
                [delimiter <Character>]
```
* `<FileName>(:<FieldName>)+` - A CSV file and the one or more columns that contain Items
* `gsheet(:<FieldName>)+ <UserGoogleSheet>` - A Google Sheet and the one or more columns that contain Items
* `gdoc(:<FieldName>)+ <UserGoogleDoc>` - A Google Doc and the one or more columns that contain Items
* `gcscsv(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain Items
* `gcsdoc(:<FieldName>)+ <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object and the one or more columns that contain Items
* `warnifnodata` - Issue message 'No CSV file data found' and exit with return code 60 if there is no data selected from the file
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `endcsv` - Use this option to signal the end of the csvfile parameters in the case that the next argument on the command line is `fields` but is specifying the output field list for the command not column headings
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `delimiter <Character>` - There are multiple Items per column separated by `<Character>`; if not specified, there is single item per column

## CSVkmdSelector
A CSV file with a key column that contains an Item and optional subkey and data columns that contain data related to the key Item.
```
<CSVkmdSelector> ::=
        csvkmd ((<FileName>|
                 (gsheet <UserGoogleSheet>)|
                 (gdoc <UserGoogleDoc>)|
                 (gcscsv <StorageBucketObjectName>)|
                 (gcsdoc <StorageBucketObjectName>))
                 [charset <Charset>] [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>] [fields <FieldNameList>])
                keyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
                subkeyfield <FieldName> [keypattern <RESearchPattern>] [keyvalue <RESubstitution>] [delimiter <Character>]
                (matchfield|skipfield <FieldName> <RESearchPattern>)*
                [datafield <FieldName>(:<FieldName>)* [delimiter <Character>]]
```
* `<FileName>` - A CSV file containing rows with columns of items
* `gsheet <UserGoogleSheet>` - A Google Sheet containing rows with columns of items
* `gdoc <UserGoogleDoc>` - A Google Doc containing rows with columns of items
* `gcscsv <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing rows with columns of items
* `gcsdoc <StorageBucketObjectName>` - A Google Cloud Storage Bucket Object containing rows with columns of items
* `columndelimiter <Character>` - Columns are  separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
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

## CSVSubkeySelector
A subkey field identified in a `csvkmd` argument.
```
<CSVSubkeySelector> ::=
        csvsubkey <FieldName>
```

## CSVDataSelector
Data fields identified in a `csvkmd` argument.
```
<CSVDataSelector> ::=
        csvdata <FieldName>(:<FieldName)*
```
## Named Collections
```
<BrowserEntity> ::=
        <DeviceIDList> |
        (query:<QueryBrowser>)|(query:orgunitpath:<OrgUnitPath>)|(query <QueryBrowser>) |
        (browserou <OrgUnitItem>) | (browserous <OrgUnitList>) |
        <FileSelector> | <CSVFileSelector>
<CalendarACLScopeEntity> ::=
        <CalendarACLScopeList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<CalendarEntity> ::=
        <CalendarList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<CIPolicyNameEntity> ::=
        <CIPolicyNameList> | <FileSelector> | <CSVFileSelector>
<ClassificationLabelNameEntity> ::=
        <ClassificationLabelNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
<ClassificationLabelPermissionNameEntity> ::=
        <ClassificationLabelPermissionNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
<ClassroomInvitationIDEntity> ::=
        <ClassroomInvitationIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<ContactEntity> ::=
        <ContactIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<ContactGroupEntity> ::=
        <ContactGroupList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<CourseAliasEntity> ::=
        <CourseAliasList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<CourseEntity> ::=
        <CourseIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector>
<CourseAnnouncementIDEntity> ::=
        <CourseAnnouncementIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>
<CourseSubmissionIDEntity> ::=
        <CourseSubmissionIDList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
<CourseTopicIDEntity> ::=
        <CourseTopicIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>
<CourseWorkIDEntity> ::=
        <CourseWorkIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>
<CourseMaterialIDEntity> ::=
        <CourseMaterialIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>
<CrOSEntity> ::=
        <CrOSIDList> | (cros_sn <SerialNumberList>) |
        (query:<QueryCrOS>) | (query:orgunitpath:<OrgUnitPath>) | (query <QueryCrOS>)
<DeviceIDEntity> ::=
        <DeviceIDList> | (device_sn <SerialNumber>)
        (query:<QueryDevice>) | (query <QueryDevice>)
<DeviceFileEntity> ::=
        <TimeList> |
        (first|last|allexceptfirst|allexceptlast <Number>) |
        (before|after <Time>) | (range <Time> <Time>) |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<DomainNameEntity> ::=
        <DomainNameList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<DriveFileIDEntity> ::=
        <DriveFileItem> |
        (id <DriveFileItem>) | (id:<DriveFileItem>) |
        (ids <DriveFileList>) | (ids:<DriveFileList>)
<DriveFileNameEntity> ::=
        (anyname <DriveFileName>) | (anyname:<DriveFileName>) |
        (anydrivefilename <DriveFileName>) | (anydrivefilename:<DriveFileName>) |
        (name <DriveFileName>) | (name:<DriveFileName>) |
        (drivefilename <DriveFileName>) | (drivefilename:<DriveFileName>) |
        (othername <DriveFileName>) | (othername:<DriveFileName>) |
        (otherdrivefilename <DriveFileName>) | (otherdrivefilename:<DriveFileName>)
<DriveFileQueryEntity> ::=
        (query <QueryDriveFile>) | (query:<QueryDriveFile>) |
        (fullquery <QueryDriveFile>)
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
<DriveFileEntityShortcut> ::=
        alldrives |
        mydrive_any |
        mydrive_me |
        mydrive_others |
        onlyteamdrives|onlyshareddrives |
        orphans |
        ownedby_any |
        ownedby_me |
        ownedby_others |
        root | mydrive |
        rootwithorphans|mydrivewithorphans |
        sharedwithme_all |
        sharedwithme_mydrive |
        sharedwithme_notmydrive
<DriveFileEntity> ::=
        <DriveFileIDEntity> |
        <DriveFileNameEntity> |
        <DriveFileQueryEntity> |
        <DriveFileQueryShortcut> |
        mydrive | mydriveid |
        root | rootid |
        <SharedDriveIDEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveNameEntity> [<SharedDriveFileQueryShortcut>] |
        <SharedDriveFileNameEntity> |
        <SharedDriveFileQueryEntity> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>)
<DriveFilePermissionEntity> ::=
        <DriveFilePermissionList> |
        <JSONData> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<DriveFilePermissionIDEntity> ::=
        <DriveFilePermissionIDList> |
        <JSONData> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<DriveFileRevisionIDEntity> ::=
        (<DriveFileRevisionID>) | (id[ |:]<DriveFileRevisionID>) (ids[ |:]<DriveFileRevisionIDList>)
        (first|last|allexceptfirst|allexceptlast <Number>)|
        (before|after <Time>) | (range <Time> <Time>)|
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<EmailAddressEntity> ::=
        <EmailAddressList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<FilterIDEntity> ::=
        <FilterIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<EventIDEntity> ::=
        (id|eventid <EventId>) |
        (event|events <EventIdList> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>)
<GroupEntity> ::=
        <GroupList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<GuardianEntity> ::=
        <GuardianList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<GuardianInvitationIDEntity> ::=
        <GuardianInvitationIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<LabelIDEntity> ::=
        <LabelIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<LabelNameEntity> ::=
        <LabelNameList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<LookerStudioAssetIDEntity> ::=
        <LookerStudioAssetIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<LookerStudioPermissionEntity> ::=
        <LookerStudioPermissionList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<MessageIDEntity> ::=
        <MessageIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<MobileEntity> ::=
        <ResourceIDList> |
        (query:<QueryMobile>) | (query <QueryMobile>)
<NotesNameEntity> ::=
        <NotesNameList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<OrgUnitEntity> ::=
        <OrgUnitList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector>
<OtherContactsResourceNameEntity> ::=
        <OtherContactsResourceNameNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
<PeopleResourceNameEntity> ::=
        <PeopleResourceNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
<ProjectIDEntity> ::=
        current | gam | <ProjectID> | (filter <String>) |
        (select <ProjectIDList> | <FileSelector> | <CSVFileSelector>)
<PrinterIDEntity> ::=
        <PrinterIDList> | <FileSelector> | <CSVFileSelector>
<RecipientEntity> ::=
        <EmailAddressEntity> | (select <UserTypeEntity>)
<ResourceEntity> ::=
        <ResourceIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector>
<SchemaEntity> ::=
        <SchemaNameList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector>
<SerialNumberEntity> ::=
        <SerialNumberList> | <FileSelector> | <CSVFileSelector>
<SharedDriveIDEntity> ::=
        <DriveFileItem> |
        (teamdriveid <DriveFileItem>) | (teamdriveid:<DriveFileItem>)
<SharedDriveNameEntity> ::=
        (teamdrive <SharedDriveName>) | (teamdrive:<SharedDriveName>)
<SharedDriveEntity> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>
<SharedDriveAdminQueryEntity> ::=
        (teamdriveadminquery <QueryTeamDrive>) | (teamdriveadminquery:<QueryTeamDrive>)
<SharedDriveEntityAdmin> ::=
        <SharedDriveIDEntity> |
        <SharedDriveNameEntity>|
        <SharedDriveAdminQueryEntity>
<SharedDriveFileNameEntity> ::=
        (teamdrivefilename <DriveFileName>) | (teamdrivefilename:<DriveFileName>)
<SharedDriveFileQueryEntity> ::=
        (teamdrivequery <QueryDriveFile>) | (teamdrivequery:<QueryDriveFile>)
<SharedDriveFileQueryShortcut> ::=
        all_files | all_folders | all_google_files | all_non_google_files | all_items
<SiteACLScopeEntity> ::=
        <SiteACLScopeList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<SiteEntity> ::=
        <SiteList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<TasklistEntity> ::=
        <TasklistIDList> | <TaskListTitleList> | <FileSelector> | <CSVFileSelector>
<TasklistIDTaskIDEntity> ::=
        <TasklistIDTaskIDList> | <FileSelector> | <CSVFileSelector>
<ThreadIDEntity> ::=
        <ThreadIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
<UserEntity> ::=
        <UserList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
```
## Examples

You want to update the membership of a collection of parent groups at your school, the data is coming from a database in a fixed format.

Example 1, CSV File GroupP1P2.csv, exactly the data you want, `keypattern` and `keyvalue` are not required.
```
Group,P1Email,P2Email
2017-parents@domain.com,g1member11@domain.com,g1member12@domain.com
2017-parents@domain.com,g1member21@domain.com,g1member22@domain.com
2018-parents@domain.com,g2member11@domain.com,g2member11@domain.com
2018-parents@domain.com,g2member21@domain.com,g2member22@domain.com
...
```
For each row, the value from the Group column is used as the group name.

`gam update groups csvkmd GroupP1P2.csv keyfield Group datafield P1Email:P2Email sync member csvdata P1Email:P2Email`

Example 2, CSV File GradYearP1P2.csv, you have to convert GradYear to group name `GradYear-parents@domain.com`, `keyvalue` is required.
```
GradYear,P1Email,P2Email
2017,g1member11@domain.com,g1member12@domain.com
2017,g1member21@domain.com,g1member22@domain.com
2018,g2member11@domain.com,g2member11@domain.com
2018,g2member21@domain.com,g2member22@domain.com
...
```
For each row, the value from the GradYear column replaces the keyField name in the `keyvalue` argument and that value is used as the group name.

`gam update groups csvkmd GradYearP1P2.csv keyfield GradYear keyvalue GradYear-parents@domain.com datafield P1Email:P2Email sync member csvdata P1Email:P2Email`

Example 3, CSV File GradYearP1P2.csv, you have to convert GradYear to group name `LastTwoDigitsOfGradYear-parents@domain.com`, `keypattern` and `keyvalue` are required.
```
GradYear,P1Email,P2Email
2017,g1member11@domain.com,g1member12@domain.com
2017,g1member21@domain.com,g1member22@domain.com
2018,g2member11@domain.com,g2member11@domain.com
2018,g2member21@domain.com,g2member22@domain.com
...
```
For each row, the value from the GradYear column is matched against the `keypattern`, the matched segments are substituted into the `keyvalue` argument and that value is used as the group name.

`gam update groups csvkmd GradYearP1P2.csv keyfield GradYear keypattern '20(..)' keyvalue '\1-parents@domain.com' datafield P1Email:P2Email sync member csvdata P1Email:P2Email`
