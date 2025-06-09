 Groups - Membership
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Collections of Users](#collections-of-users)
  - [Select users based on suspension state](#select-users-based-on-suspension-state)
  - [Select users based on archived state](#select-users-based-on-archived-state)
- [Add members to a group](#add-members-to-a-group)
- [Delete members from a group](#delete-members-from-a-group)
- [Synchronize members in a group](#synchronize-members-in-a-group)
- [Delete members from a group by role or status](#delete-members-from-a-group-by-role-or-status)
- [Update member roles and delivery options](#update-member-roles-and-delivery-options)
- [Bulk membership changes](#bulk-membership-changes)
- [Display user group member options](#display-user-group-member-options)
- [Display group membership in CSV format](#display-group-membership-in-csv-format)
- [Display group membership in hierarchical format](#display-group-membership-in-hierarchical-format)

## API documentation
* [Directory API - Members](https://developers.google.com/admin-sdk/directory/reference/rest/v1/members)

## Query documentation
* [Directory API - Search Groups](https://developers.google.com/admin-sdk/directory/v1/guides/search-groups)
* [Cloud Identity API - Search Dynamic Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery)

## Definitions
See [Collections of Items](Collections-of-Items)

* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

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
<DeliverySetting> ::=
        allmail|
        abridged|daily|
        digest|
        disabled|
        none|nomail
<DomainName> ::= <String>(.<String>)+
<DomainNameList> ::= "<DomainName>(,<DomainName>)*"
<DomainNameEntity> ::=
        <DomainNameList> | <FileSelector> | <CSVFileSelector>
<EmailAddress> ::= <String>@<DomainName>
<EmailItem> ::= <EmailAddress>|<UniqueID>|<String>
<UniqueID> ::= id:<String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<GroupList> ::= "<GroupItem>(,<GroupItem>)*"
<GroupEntity> ::=
        <GroupList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<GroupRole> ::= owner|manager|member
<GroupRoleList> ::= "<GroupRole>(,<GroupRole>)*"
<GroupMemberType> ::= customer|group|user
<GroupMemberTypeList> ::= "<GroupMemberType>(,<GroupMemberType>)*"
<QueryGroup> ::= <String>
        See: https://developers.google.com/admin-sdk/directory/v1/guides/search-groups
<QueryGroupList> ::= "<QueryGroup>(,<QueryGroup>)*"

<MembersFieldName> ::=
        delivery|deliverysettings|
        email|useremail|
        group|groupemail|
        id|
        name|
        role|
        status|
        type
<MembersFieldNameList> ::= "<MembersFieldName>(,<MembersFieldName>)*"
```

## Collections of Users
Group membership commands involve specifying collections of users;
for `<UserTypeEntity>`, see: [Collections of Users](Collections-of-Users)

### Select users based on suspension state
When adding, deleting or synchronizing group members, to select only suspended or non-suspended users, use the following`<UserTypeEntity>`:
```
        (all users_ns|users_susp)|
        (domains_ns|domains_susp <DomainNameList>)|
        (group_ns|group_susp <GroupItem>)|
        (groups_ns|groups_susp <GroupList>)|
        (group_users_ns|group_users_susp <GroupList>
                [members] [managers] [owners]
                [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end)|
        (ou_ns|ou_susp <OrgUnitItem>)|
        (ou_and_children_ns|ou_and_children_susp <OrgUnitItem>)|
        (ous_ns|ous_susp <OrgUnitList>)|
        (ous_and_children_ns|ous_and_children_susp <OrgUnitList>)
```

When adding, deleting or synchronizing group members, the `notsuspended|suspended` option can be used to select
users in a particular suspension state. This option can be used with the following `<UserTypeEntity>`:
```
        (all users)|
        (domains <DomainNameList>)|
        (group <GroupItem>)|
        (groups <GroupList>)|
        (group_users <GroupList>
                [members] [managers] [owners]
                [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end)|
        (ou <OrgUnitItem>)|
        (ou_and_children <OrgUnitItem>)|
        (ous <OrgUnitList>)|
        (ous_and_children <OrgUnitList>)
```

### Select users based on archived state
When adding, deleting or synchronizing group members, the `notarchived|archived` option can be used to select
users in a particular archived state. This option can be used with the following `<UserTypeEntity>`:
```
        (all users|users_ns|users_susp|users_ns_susp)|
        (domains|domains_ns|domains_susp <DomainNameList>)|
        (group|group_ns|group_susp <GroupItem>)|
        (groups|groups_ns|groups_susp <GroupList>)|
        (group_users|group_users_ns|group_users_susp <GroupList>
                [members] [managers] [owners]
                [primarydomain] [domains <DomainNameList>] [recursive|includederivedmembership] end)|
        (ou|ou_ns|ou_susp <OrgUnitItem>)|
        (ou_and_children|ou_and_children_ns|ou_and_children_susp <OrgUnitItem>)|
        (ous|ous_ns|ous_susp <OrgUnitList>)|
        (ous_and_children|ous_and_children_ns|ous_and_children_susp <OrgUnitList>)|
        (query <QueryUser>)|
        (queries <QueryUserList>)
```

## Add members to a group
```
gam update group|groups <GroupEntity> create|add [<GroupRole>]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [[delivery] <DeliverySetting>]
        [preview] [actioncsv]
        <UserItem>|<UserTypeEntity>
```
To add a group as a member of another group, just specify its email address.
```
gam update group group1@domain.com add member group2@domain.com
```

When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are added
* `groupsonly` - Only the group members from the specified groups are added

For `notsuspended|suspended`, see: [Select users based on suspension state](#select-users-based-on-suspension-state)

For `notarchived|archived`, see: [Select users based on archived state](#select-users-based-on-archived-state)

You can set the `delivery` option for the new members:
* `allmail` - All messages, delivered as soon as they arrive
* `abridged|daily` - No more than one message a day
* `digest` - Up to 25 messages bundled into a single message
* `none|nomail` - No messages
* `disabled` - Remove subscription; this is what the documentation says, it's not clear what it means

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

Gam adds the members in batches and pauses between batches in order to avoid exceeding Google's quota limits. The size of the batch
is set in `gam.cfg/batch_size` and the pause in `gam.cfg/inter_watch_wait`. For add, values of 20 and 1 seem to give reasonable results.
For each batch, if the quota rate limit is exceeded, Gam increases inter_batch_wait by .25 seconds.

For example,
```
gam config batch_size 20 inter_batch_wait 1 update group testgroup@domain.com add members file users.lst
```
### `actioncsv` Example
Using `actioncsv` produces a CSV file showing the actions taken.
```
$ gam redirect csv AddUpdates.csv update group testgroup add members actioncsv users testuser2,testuser3
Group: testgroup@domain.com, Add 2 Members
  Group: testgroup@domain.com, Member: testuser2@domain.com, Added: Role: MEMBER (1/2)
  Group: testgroup@domain.com, Member: testuser3@domain.com, Add Failed: Member already exists. (2/2)
$ more AddUpdates.csv 
group,email,role,action,message
testgroup@domain.com,testuser2@domain.com,MEMBER,Added,Success
testgroup@domain.com,testuser3@domain.com,MEMBER,Add Failed,Member already exists.
```

## Delete members from a group
```
gam update group|groups <GroupEntity> delete|remove [<GroupRole>]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [preview] [actioncsv]
        <UserItem>|<UserTypeEntity>
```
`<GroupRole>` is ignored, deletions take place regardless of role.

To remove a group as a member of another group, just specify its email address.
```
gam update group group1@domain.com remove group2@domain.com
```

When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are deleted
* `groupsonly` - Only the group members from the specified groups are deleted

For `notsuspended|suspended`, see: [Select users based on suspension state](#select-users-based-on-suspension-state)

For `notarchived|archived`, see: [Select users based on archived state](#select-users-based-on-archived-state)

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

Gam deletes the members in batches and pauses between batches in order to avoid exceeding Google's quota limits. The size of the batch
is set in `gam.cfg/batch_size` and the pause in `gam.cfg/inter_watch_wait`. For delete, values of 20 and 2 seem to give reasonable results.
For each batch, if the quota rate limit is exceeded, Gam increases inter_batch_wait by .25 seconds.

For example,
```
gam config batch_size 20 inter_batch_wait 2 update group testgroup@domain.com delete members file users.lst
```
### `actioncsv` Example
Using `actioncsv` produces a CSV file showing the actions taken.
```
$ gam redirect csv DeleteUpdates.csv update group testgroup delete members actioncsv users testuser2,testuser4
Group: testgroup@domain.com, Remove 2 Members
  Group: testgroup@domain.com, Member: testuser2@domain.com, Removed: Role: MEMBER (1/2)
  Group: testgroup@domain.com, Member: testuser4@domain.com, Remove Failed: Does not exist (2/2)
$ more DeleteUpdates.csv 
group,email,role,action,message
testgroup@domain.com,testuser2@domain.com,MEMBER,Removed,Success
testgroup@domain.com,testuser4@domain.com,MEMBER,Remove Failed,Does not exist
```

## Synchronize members in a group
A synchronize operation gets the current membership for a group and does adds and deletes as necessary to make it match `<UserTypeEntity>`.
This is done by specific role except for a special case where role is ignored.
```
gam update group|groups <GroupEntity> sync [<GroupRole>|ignorerole]
        [usersonly|groupsonly] [addonly|removeonly]
        [notsuspended|suspended] [notarchived|archived]
        [remove_domain_nostatus_members]
        [[delivery] <DeliverySetting>]
        [preview] [actioncsv]
        (additionalmembers [<GroupRole>] <EmailAddressEntity>)*
        <UserItem>|<UserTypeEntity>
```
If `ignorerole` is specified, GAM removes members regardless of role and adds new members with role MEMBER.
This is a special purpose option, use with caution and ensure that `<UserTypeEntity>` specifies the full desired membership list of all roles.

If neither `<GroupRole>` nor `ignorerole` is specified, `member` is assumed.

When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are added/deleted
* `groupsonly` - Only the group members from the specified groups are added/deleted

For `notsuspended|suspended`, see: [Select users based on suspension state](#select-users-based-on-suspension-state)

For `notarchived|archived`, see: [Select users based on archived state](#select-users-based-on-archived-state)

The `notsuspended|suspended` and `notarchived|archived` not only control what users are selected from `<UserTypeEntity>`
but they also control what users are selected from `<GroupEntity>`.

The `remove_domain_nostatus_members` option is used to remove members from the group that are in your domain but have no status.
These members were added to the group before the user or group that they represent was created.
Your domain is defined as the value from `domain` in `gam.cfg` if it is defined, or, if not, the domain of your Google Workspace Admin in oauth2.txt.

You can set the `delivery` option for the new members:
* `allmail` - All messages, delivered as soon as they arrive
* `abridged|daily` - No more than one message a day
* `digest` - Up to 25 messages bundled into a single message
* `none|nomail` - No messages
* `disabled` - Remove subscription; this is what the documentation says, it's not clear what it means

Default:
* members in `<UserTypeEntity>` that are not in the current membership will be added
* members in the current membership that are not in `<UserTypeEntity>` will deleted

When the `addonly` option is specified:
* members in `<UserTypeEntity>` that are not in the current membership will be added
* members in the current membership that are not in `<UserTypeEntity>` will not be deleted

When the `removeonly` option is specified:
* members in `<UserTypeEntity>` that are not in the current membership will not be added
* members in the current membership that are not in `<UserTypeEntity>` will be deleted

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

The option `additionalmembers [<GroupRole>] <EmailAddressEntity>` can be used to specify members in addition to those specified with `<UserTypeEntity>`.
If a <GroupRole> is specified, it must match the same role as the one used for the group sync.

For example,
```
gam update group teachers@domain.com sync member additionalmembers counselor@domain.com ou /Teachers
```

Gam adds/deletes the members in batches and pauses between batches in order to avoid exceeding Google's quota limits. The size of the batch
is set in `gam.cfg/batch_size` and the pause in `gam.cfg/inter_watch_wait`. For sync, values of 20 and 1 seem to give reasonable results for
the adds but the inter_batch_wait is probably too low for the deletes; for each batch, if the quota rate limit is exceeded, Gam increases inter_batch_wait by .25 seconds.

For example,
```
gam config batch_size 20 inter_batch_wait 1 update group testgroup@domain.com sync members file users.lst
```
### Examples using CSV file and Google sheets:
* https://github.com/GAM-team/GAM/wiki/Collections-of-Users#examples-using-csv-files-and-google-sheets-to-update-the-membership-of-a-group

### Example
Assume that at your school there is a group for each grade level and the members come from an OU; here is a sample CSV file GradeOU.csv
```
Grade,OU
seniors@domain.org,/Students/ClassOf2023
juniors@domain.org,/Students/ClassOf2024
...
```
This allows you to do: `gam csv GradeOU.csv gam update group "~Grade" sync members ou "~OU"`
But suppose that at each grade level there are additional group members that are groups of faculty/staff; e.g., senioradvisors@domain.org.
In this scenario, you can't do the `update group sync` command as the members that are groups will be deleted; the `usersonly` option allows
the `update group sync` command to work: `gam csv GradeOU.csv gam update group "~Grade" sync members usersonly ou "~OU"`
The users from the OU are matched against the user members of the group and adds/deletes are done as necessary to synchronize them;
the group members of the group are unaffected.

### `actioncsv` Example
Using `actioncsv` produces a CSV file showing the actions taken.
```
$ gam redirect csv SyncUpdates.csv update group testgroup sync members actioncsv users testuser1,testuser3,testuser4
Getting all Members for testgroup@domain.com, may take some time on a large Group...
Got 3 Members for testgroup@domain.com...
Group: testgroup@domain.com, Remove 1 Member
  Group: testgroup@domain.com, Member: testuser2@domain.com, Removed: Role: MEMBER
Group: testgroup@domain.com, Add 1 Member
  Group: testgroup@domain.com, Member: testuser4@domain.com, Added: Role: MEMBER
$ more SyncUpdates.csv 
group,email,role,action,message
testgroup@domain.com,testuser2@domain.com,MEMBER,Removed,Success
testgroup@domain.com,testuser4@domain.com,MEMBER,Added,Success
```
## Delete members from a group by role or status
```
gam update group|groups <GroupEntity> clear [member] [manager] [owner]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [emailclearpattern|emailretainpattern <REMatchPattern>]
        [remove_domain_nostatus_members]
        [preview] [actioncsv]
```
If none of `member`, `manager`, or `owner` are specified, `member` is assumed.

By default, when clearing members from a group, all members, whether users or groups, are included.
* `usersonly` - Clear only the user members
* `groupsonly` - Clear only the group members

By default, when clearing members from a group, all members, whether suspended/archived or not, are included.
* `notsuspended` - Clear only non-suspended members
* `suspended` - Clear only suspended members
* `notarchived` - Clear only non-archived members
* `archived` - Clear only archived users
* `notsuspended notarchived` - Do not clear suspended and archived members
* `suspended archived` - Clear suspended and archived members
* `notsuspended archived` - Do not clear archived members
* `suspended notarchived` - Do not clear suspended members

Members that have met the above qualifications to be cleared can be further qualifed by their email address.
* `emailclearpattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be cleared; others will be retained
* `emailretainpattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be retained; others will be cleared

The `remove_domain_nostatus_members` option is used to clear members from the group that are in your domain but have no status.
These members were added to the group before the user or group that they represent was created.
Your domain is defined as the value from `domain` in `gam.cfg` if it is defined, or, if not, the domain of your Google Workspace Admin in oauth2.txt.

If `preview` is specified, the deletes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

Gam deletes the members in batches and pauses between batches in order to avoid exceeding Google's quota limits. The size of the batch
is set in `gam.cfg/batch_size` and the pause in `gam.cfg/inter_watch_wait`. For delete, values of 20 and 2 seem to give reasonable results.
For each batch, if the quota rate limit is exceeded, Gam increases inter_batch_wait by .25 seconds.

For example,
```
gam config batch_size 20 inter_batch_wait 2 update group testgroup@domain.com clear members
```
## Update member roles and delivery options
```
gam update group|groups <GroupEntity> update [<GroupRole>]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [[delivery] <DeliverySetting>]
        [createifnotfound]
        [preview] [actioncsv]
        <UserItem>|<UserTypeEntity>
```
There are two items that can be updated: role and delivery. If neither option is specified,
the users are updated to members; this is the behavior from previous versions. Otherwise,
only the specified items are updated.

When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are added
* `groupsonly` - Only the group members from the specified groups are added

By default, when updating members from organization units, all users, whether suspended or not, are included.
* `notsuspended` - Do not include suspended users
* `suspended` - Only include suspended users

By default, when updating members from groups, all users, whether suspended/archived or not, are included.
* `notsuspended` - Do not include suspended users
* `suspended` - Only include suspended users
* `notarchived` - Do not include archived users
* `archived` - Only include archived users
* `notsuspended notarchived` - Do not include suspended and archived users
* `suspended archived` - Include only suspended or archived users
* `notsuspended archived` - Only include archived users
* `suspended notarchived` - Only include suspended users

You can set the `delivery` option for the updated members:
* `allmail` - All messages, delivered as soon as they arrive
* `abridged|daily` - No more than one message a day
* `digest` - Up to 25 messages bundled into a single message
* `none|nomail` - No messages
* `disabled` - Remove subscription; this is what the documentation says, it's not clear what it means

If, when attempting to update the role of a group member, the group member is not found, the `createifnotfound` option causes Gam to add the member with the specified role.

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

## Bulk membership changes
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
You can also do `create|add`, `delete` and `update` in this manner.

If you want to update a specific role, you can do one of the following.
```
gam redirect stdout ./MemberUpdates.txt redirect stderr stdout update group csvkmd ./GroupMembers.csv keyfield group matchfield role MEMBER datafield email sync member csvdata email
gam redirect stdout ./ManagerUpdates.txt redirect stderr stdout update group csvkmd ./GroupMembers.csv keyfield group matchfield role MANAGER datafield email sync manager csvdata email
gam redirect stdout ./OwnerUpdates.txt redirect stderr stdout update group csvkmd ./GroupMembers.csv keyfield group matchfield role OWNER datafield email sync owner csvdata email
```

## Display user group member options

Display user's group membership information. Delivery information is displayed; an additional API call per user is required.
```
gam <UserTypeEntity> info member|group-members <GroupEntity>
gam info member|group-members <UserItem>|<UserTypeEntity> <GroupEntity>
```

## Display group membership in CSV format
By default, delivery information is not displayed.
```
gam print group-members [todrive <ToDriveAttribute>*]
        [([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryGroupList>)]))|
         (group|group_ns|group_susp <GroupItem>)|
         (select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [admincreatedmatch <Boolean>]
        [roles <GroupRoleList>] [members] [managers] [owners]
        [internal] [internaldomains <DomainNameList>] [external]
        [membernames] [showdeliverysettings]
        <MembersFieldName>* [fields <MembersFieldNameList>]
        [notsuspended|suspended] [notarchived|archived]
        [types <GroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [userfields <UserFieldNameList>]
        [allschemas|(schemas|custom|customschemas <SchemaNameList>)]
        [(recursive [noduplicates])|includederivedmembership] [nogroupemail]
        [peoplelookup|(peoplelookupuser <EmailAddress>)]
        [unknownname <String>] [cachememberinfo [Boolean]]
        [formatjson [quotechar <Character>]]
```
By default, the group membership of all groups in the account are displayed, these options allow selection of subsets of groups:
* `domain|domains <DomainNameEntity>` - Limit display to groups in the domains specified by `<DomainNameEntity>`
  * You can predefine this list with the `print_agu_domains` variable in `gam.cfg`.
* `member <EmailItem>` - Limit display to groups that contain `<EmailItem>` as a member; mutually exclusive with `query <QueryGroup>`
* `showownedby <EmailItem>` - Limit display to groups that contain `<EmailItem>` as an owner; mutually exclusive with `query <QueryGroup>`
* `(query <QueryGroup>)|(queries <QueryGroupList>)` - Limit groups to those that match a query; each query is run against each domain
* `group <GroupItem>` - Limit display to the single group `<GroupItem>`
* `group_ns <GroupItem>` - Limit display to the single group `<GroupItem>`, display non-suspended members
* `group_susp <GroupItem>` - Limit display to the single group `<GroupItem>`, display suspended members
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`
* `showownedby <UserItem>` - Limit display to groups owned by `<UserItem>`

When using `query <QueryGroup>` with the `name:{PREFIX}*` query, `PREFIX` must contain at least three characters.

You can identify groups with the `All users in the organization` member with:
* `query "memberKey=<CustomerID>"`
* `member id:<CustomerID>`

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`
* `admincreatedmatch True` - Limit display to groups created by administrators
* `admincreatedmatch False` - Limit display to groups created by users

By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `roles <GroupRoleList>` - Display specified roles
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners

By default, all types of members (customer, group, user) in the group are displayed; this option modifies that behavior:
* `types <GroupMemberTypeList>` - Display specified types

By default, members that are groups are displayed as a single entry of type GROUP; this option recursively expands group members to display their user members.
* `recursive` - Recursively expand group members

When `recursive` is specified, the default is to only display type user members; this option modifies those behaviors:
* `types <GroupMemberTypeList>` - Display specified types

By default, when displaying members from a group, all members, whether suspended/archived or not, are included.
* `notsuspended` - Display only non-suspended members
* `suspended` - Display only suspended members
* `notarchived` - Do not include archived members
* `archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived members
* `suspended archived` - Include only suspended or archived members
* `notsuspended archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended members, this is not common but allows creating groups that allow easy identification of suspended users

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, the ID, role, email address, type and status of each member are displayed along with the group email address;
these options specify which fields to display:
* `membernames` - Display members full name; an additional API call per member is required
* `showdeliverysettings` - Display delivery settings; an additional API call per member is required
* `<MembersFieldName>*` - Individual field names
* `fields <MembersFieldNameList>` - A comma separated list of field names
    * `delivery|deliverysettings` - Specify this field to get delivery information; an additional API call per member is required

For members that are users, you can specify additional information to display; an additional API call per member is required
* `userfields <UserFieldNameList>` - Display specific user fields
* `allschemas|(schemas|custom|customschemas <SchemaNameList>)` - Display all or specific custom schema values

The additional API calls can be reduced with the `cachememberinfo` option; a single API call is made for each user/group
and the data is cached to eliminate to need to repeat the API call; this consumes more memory but dramatically reduces the number of API calls.

If member names are requested, names are not available for users not in the domain; you can request that GAM use the People API to retrieve
names for these users. Names are not retrieved in all cases and success is dependent on what user is used to perform the retrievals.
* `peoplelookup` - Use the administrator named in oauth2.txt to perform the retrievals
* `peoplelookupuser <EmailAddress>` - Use `<EmailAddress>` to perform the retrievals

By default, when `membernames` is specified, GAM displays `Unknown` for members whose names can not be determined.
Use `unknownname <String>` to specify an alternative value.

By default, the group email address is always shown, you can suppress it with the `nogroupemail` option.

The `recursive` option adds two columns, level and subgroup, to the output:
* `level` - At what level of the expansion does the user appear; level 0 is the top level
* `subgroup` - The group that contained the user

Displaying membership of multiple groups or recursive expansion may result in multiple instances of the same user being displayed; these multiple instances can be reduced to one entry.
* `noduplicates` - Reduce multiple instances of the same user to the first instance

The `includederivedmembership` option is an alternative to `recursive`; it causes the API to expand type GROUP and type CUSTOMER
members to display their constituent members while still displaying the original member.
The API produces inconsistent results, use with caution.

The options `recursive noduplicates` and `includederivedmembership types user noduplicates` return the same list of users.
The `includederivedmembership` option makes less API calls but doesn't show level and subgroup information.
Expanding a member of type CUSTOMER may produce a large volume of data as it will display all users in your domain.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display group membership in hierarchical format
```
gam show group-members
        [([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryGroupList>)]))|
         (group|group_ns|group_susp <GroupItem>)|
         (select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [admincreatedmatch <Boolean>]
        [roles <GroupRoleList>] [members] [managers] [owners] [depth <Number>]
        [internal] [internaldomains <DomainNameList>] [external]
        [notsuspended|suspended] [notarchived|archived]
        [types <GroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [includederivedmembership]
```
By default, the group membership of all groups in the account are displayed, these options allow selection of subsets of groups:
* `domain|domains <DomainNameEntity>` - Limit display to groups in the domains specified by `<DomainNameEntity>`
  * You can predefine this list with the `print_agu_domains` variable in `gam.cfg`.
* `member <EmailItem>` - Limit display to groups that contain `<EmailItem>` as a member; mutually exclusive with `query <QueryGroup>`
* `showownedby <EmailItem>` - Limit display to groups that contain `<EmailItem>` as an owner; mutually exclusive with `query <QueryGroup>`
* `(query <QueryGroup>)|(queries <QueryGroupList>)` - Limit groups to those that match a query; each query is run against each domain
* `group <GroupItem>` - Limit display to the single group `<GroupItem>`
* `group_ns <GroupItem>` - Limit display to the single group `<GroupItem>`, display non-suspended members
* `group_susp <GroupItem>` - Limit display to the single group `<GroupItem>`, display suspended members
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`
* `showownedby <UserItem>` - Limit display to groups owned by `<UserItem>`

When using `query <QueryGroup>` with the `name:{PREFIX}*` query, `PREFIX` must contain at least three characters.

You can identify groups with the `All users in the organization` member with:
* `query "memberKey=<CustomerID>"`
* `member id:<CustomerID>`

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`
* `admincreatedmatch True` - Limit display to groups created by administrators
* `admincreatedmatch False` - Limit display to groups created by users

By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `roles <GroupRoleList>` - Display specified roles
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners

By default, when displaying members from a group, all members, whether suspended/archived or not, are included.
* `notsuspended` - Display only non-suspended members
* `suspended` - Display only suspended members
* `notarchived` - Do not include archived members
* `archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived members
* `suspended archived` - Include only suspended or archived members
* `notsuspended archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended members, this is not common but allows creating groups that allow easy identification of suspended users

By default, all types of members (customer, group, user) in the group are displayed; this option modifies that behavior:
* `types <GroupMemberTypeList>` - Display specified types

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, members of type GROUP are recursively expanded to show their constituent members. (Members of
type CUSTOMER are not expanded.) The `depth <Number>` argument controls the depth to which nested groups are displayed.
* `depth -1` - all groups in the selected group and below are displayed; this is the default.
* `depth 0` - the groups within a selected group are displayed, no descendants are displayed.
* `depth N` - the groups within the selected group and those groups N levels below the selected group are displayed.

The `includederivedmembership` option causes the API to expand type GROUP and type CUSTOMER
members to display their constituent members while still displaying the original member.

The options `types user` and `includederivedmembership types user` return the same list of users.
The `includederivedmembership` option makes less API calls but doesn't show hierarchy.
Expanding a member of type CUSTOMER may produce a large volume of data as it will display all users in your domain.

### Display group structure
To see a group's structure of nested groups use the `type group` option.
```
$ gam show group-members group testgroup5 types group
Group: testgroup5@domain.com
  MEMBER, GROUP, testgroup1@domain.com, ACTIVE
    MEMBER, GROUP, testgroup2@domain.com, ACTIVE
  MEMBER, GROUP, testgroup3@domain.com, ACTIVE
    MEMBER, GROUP, testgroup2@domain.com, ACTIVE
    MEMBER, GROUP, testgroup4@domain.com, ACTIVE
```
To show the structure of all groups you can do the following; it will be time consuming for a large number of groups.
```
gam redirect stdout ./groups.txt show group-members types group
```

### Examples
#### Print a CSV of all members of a group regardless of role, all fields
```
gam print group-members <GroupEntity>
```
#### Print a CSV containing all managers emails
```
gam print group-members <GroupEntity> role manager fields email
```
#### Print a CSV output of all members and their emails only
```
gam print group-members <GroupEntity> role member fields email
```
#### Display group owners in your domain, but excluding groups where the email starts with a 4 digit code
```
gam print group-members domain <Your Domain> emailmatchpattern not '^1234.*' roles owners
```


These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`
* `admincreatedmatch True` - Limit display to groups created by administrators
* `admincreatedmatch False` - Limit display to groups created by users

By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `roles <GroupRoleList>` - Display specified roles
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners

By default, all types of members (customer, group, user) in the group are displayed; this option modifies that behavior:
* `types <GroupMemberTypeList>` - Display specified types

By default, members that are groups are displayed as a single entry of type GROUP; this option recursively expands group members to display their user members.
* `recursive` - Recursively expand group members

When `recursive` is specified, the default is to only display type user members; this option modifies those behaviors:
* `types <GroupMemberTypeList>` - Display specified types

By default, when displaying members from a group, all members, whether suspended/archived or not, are included.
* `notsuspended` - Display only non-suspended members
* `suspended` - Display only suspended members
* `notarchived` - Do not include archived members
* `archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived members
* `suspended archived` - Include only suspended or archived members
* `notsuspended archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended members, this is not common but allows creating groups that allow easy identification of suspended users

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, the ID, role, email address, type and status of each member are displayed along with the group email address;
these options specify which fields to display:
* `membernames` - Display members full name; an additional API call per member is required
* `showdeliverysettings` - Display delivery settings; an additional API call per member is required
* `<MembersFieldName>*` - Individual field names
* `fields <MembersFieldNameList>` - A comma separated list of field names
    * `delivery|deliverysettings` - Specify this field to get delivery information; an additional API call per member is required

For members that are users, you can specify additional information to display; an additional API call per member is required
* `userfields <UserFieldNameList>` - Display specific user fields
* `allschemas|(schemas|custom|customschemas <SchemaNameList>)` - Display all or specific custom schema values

The additional API calls can be reduced with the `cachememberinfo` option; a single API call is made for each user/group
and the data is cached to eliminate to need to repeat the API call; this consumes more memory but dramatically reduces the number of API calls.

If member names are requested, names are not available for users not in the domain; you can request that GAM use the People API to retrieve
names for these users. Names are not retrieved in all cases and success is dependent on what user is used to perform the retrievals.
* `peoplelookup` - Use the administrator named in oauth2.txt to perform the retrievals
* `peoplelookupuser <EmailAddress>` - Use `<EmailAddress>` to perform the retrievals

By default, when `membernames` is specified, GAM displays `Unknown` for members whose names can not be determined.
Use `unknownname <String>` to specify an alternative value.

By default, the group email address is always shown, you can suppress it with the `nogroupemail` option.

The `recursive` option adds two columns, level and subgroup, to the output:
* `level` - At what level of the expansion does the user appear; level 0 is the top level
* `subgroup` - The group that contained the user

Displaying membership of multiple groups or recursive expansion may result in multiple instances of the same user being displayed; these multiple instances can be reduced to one entry.
* `noduplicates` - Reduce multiple instances of the same user to the first instance

The `includederivedmembership` option is an alternative to `recursive`; it causes the API to expand type GROUP and type CUSTOMER
members to display their constituent members while still displaying the original member.
The API produces inconsistent results, use with caution.

The options `recursive noduplicates` and `includederivedmembership types user noduplicates` return the same list of users.
The `includederivedmembership` option makes less API calls but doesn't show level and subgroup information.
Expanding a member of type CUSTOMER may produce a large volume of data as it will display all users in your domain.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display group membership in hierarchical format
```
gam show group-members
        [([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryGroupList>)]))|
         (group|group_ns|group_susp <GroupItem>)|
         (select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [admincreatedmatch <Boolean>]
        [roles <GroupRoleList>] [members] [managers] [owners] [depth <Number>]
        [internal] [internaldomains <DomainNameList>] [external]
        [notsuspended|suspended] [notarchived|archived]
        [types <GroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [includederivedmembership]
```
By default, the group membership of all groups in the account are displayed, these options allow selection of subsets of groups:
* `domain|domains <DomainNameEntity>` - Limit display to groups in the domains specified by `<DomainNameEntity>`
  * You can predefine this list with the `print_agu_domains` variable in `gam.cfg`.
* `member <EmailItem>` - Limit display to groups that contain `<EmailItem>` as a member; mutually exclusive with `query <QueryGroup>`
* `showownedby <EmailItem>` - Limit display to groups that contain `<EmailItem>` as an owner; mutually exclusive with `query <QueryGroup>`
* `(query <QueryGroup>)|(queries <QueryGroupList>)` - Limit groups to those that match a query; each query is run against each domain
* `group <GroupItem>` - Limit display to the single group `<GroupItem>`
* `group_ns <GroupItem>` - Limit display to the single group `<GroupItem>`, display non-suspended members
* `group_susp <GroupItem>` - Limit display to the single group `<GroupItem>`, display suspended members
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`
* `showownedby <UserItem>` - Limit display to groups owned by `<UserItem>`

When using `query <QueryGroup>` with the `name:{PREFIX}*` query, `PREFIX` must contain at least three characters.

You can identify groups with the `All users in the organization` member with:
* `query "memberKey=<CustomerID>"`
* `member id:<CustomerID>`

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`
* `admincreatedmatch True` - Limit display to groups created by administrators
* `admincreatedmatch False` - Limit display to groups created by users

By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `roles <GroupRoleList>` - Display specified roles
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners

By default, when displaying members from a group, all members, whether suspended/archived or not, are included.
* `notsuspended` - Display only non-suspended members
* `suspended` - Display only suspended members
* `notarchived` - Do not include archived members
* `archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived members
* `suspended archived` - Include only suspended or archived members
* `notsuspended archived` - Only include archived members, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended members, this is not common but allows creating groups that allow easy identification of suspended users

By default, all types of members (customer, group, user) in the group are displayed; this option modifies that behavior:
* `types <GroupMemberTypeList>` - Display specified types

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, members of type GROUP are recursively expanded to show their constituent members. (Members of
type CUSTOMER are not expanded.) The `depth <Number>` argument controls the depth to which nested groups are displayed.
* `depth -1` - all groups in the selected group and below are displayed; this is the default.
* `depth 0` - the groups within a selected group are displayed, no descendants are displayed.
* `depth N` - the groups within the selected group and those groups N levels below the selected group are displayed.

The `includederivedmembership` option causes the API to expand type GROUP and type CUSTOMER
members to display their constituent members while still displaying the original member.

The options `types user` and `includederivedmembership types user` return the same list of users.
The `includederivedmembership` option makes less API calls but doesn't show hierarchy.
Expanding a member of type CUSTOMER may produce a large volume of data as it will display all users in your domain.

### Display group structure
To see a group's structure of nested groups use the `type group` option.
```
$ gam show group-members group testgroup5 types group
Group: testgroup5@domain.com
  MEMBER, GROUP, testgroup1@domain.com, ACTIVE
    MEMBER, GROUP, testgroup2@domain.com, ACTIVE
  MEMBER, GROUP, testgroup3@domain.com, ACTIVE
    MEMBER, GROUP, testgroup2@domain.com, ACTIVE
    MEMBER, GROUP, testgroup4@domain.com, ACTIVE
```
To show the structure of all groups you can do the following; it will be time consuming for a large number of groups.
```
gam redirect stdout ./groups.txt show group-members types group
```

### Examples
#### Print a CSV of all members of a group regardless of role, all fields
```
gam print group-members <GroupEntity>
```
#### Print a CSV containing all managers emails
```
gam print group-members <GroupEntity> role manager fields email
```
#### Print a CSV output of all members and their emails only
```
gam print group-members <GroupEntity> role member fields email
```
#### Display group owners in your domain, but excluding groups where the email starts with a 4 digit code
```
gam print group-members domain <Your Domain> emailmatchpattern not '^1234.*' roles owners
```
