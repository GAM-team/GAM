# Cloud Identity Groups - Membership
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Notes](#Notes)
- [Collections of Users](#collections-of-users)
- [Add members to a group](#add-members-to-a-group)
- [Delete members from a group](#delete-members-from-a-group)
- [Synchronize members in a group](#synchronize-members-in-a-group)
- [Delete members from a group by role](#delete-members-from-a-group-by-role)
- [Update member roles and expiration time](#update-member-roles-and-expiration-time)
- [Bulk membership changes](#bulk-membership-changes)
- [Display user group member options](#display-user-group-member-options)
- [Display group membership in CSV format](#display-group-membership-in-csv-format)
- [Display group membership in hierarchical format](#display-group-membership-in-hierarchical-format)

## API documentation
* [Cloud Identity Groups Overview](https://cloud.google.com/identity/docs/groups)
* [Cloud Identity Groups API - Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups)
* [Cloud Identity Groups API - Membership](https://cloud.google.com/identity/docs/reference/rest/v1/groups.memberships)
* [Cloud Identity Groups](https://gsuiteupdates.googleblog.com/2020/08/new-api-cloud-identity-groups-google.html)
* [Security Groups](https://gsuiteupdates.googleblog.com/2020/09/security-groups-beta.html)

## Query documentation
* [Cloud Identity Groups API - Search Dynamic Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery)
* [Member Restrictions](https://cloud.google.com/identity/docs/reference/rest/v1/SecuritySettings#MemberRestriction)

## Notes

In the Admin Directory API a group has the following characteristics:
* `id` - The unique ID of a group
* `email` - The group's email address
* `name` - The group's display name

In the Cloud Indentity Groups API a group has the following characteristics:
* `name` - The unique ID of a group
* `groupKey.id` - The group's email address
* `displayName` - The group's display name

The Admin Directory API group characteristic names will be used.

Dynamic Groups require Cloud Identity Premium accounts.

* https://cloud.google.com/identity/docs/how-to/create-dynamic-groups

The `cimember <UserItem>` option of `gam print|show cigroup-members` requires a Google Workspace Enterprise Standard, Enterprise Plus, and Enterprise for Education;
and Cloud Identity Premium accounts. Unfortunately, even if you have the required account, the API call that supports the query doesn't work.

* https://cloud.google.com/identity/docs/reference/rest/v1/groups.memberships/searchTransitiveGroups

## Definitions
```
<DeviceId> ::= <String>
<CBCMBrowser> ::= id:cbcm-browser.<DeviceId>
<ChromeOSDevice> ::= id:chrome-os-device.<DeviceId>
<BrowserDeviceList> ::= "(<CBCMBrowser>|<ChromeOSDevice>)(,(<CBCMBrowser>|<ChromeOSDevice>))*"
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|groups/<String>
<GroupList> ::= "<GroupItem>(,<GroupItem>)*"
<GroupEntity> ::=
        <GroupList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<GroupRole> ::= owner|manager|member
<GroupRoleList> ::= "<GroupRole>(,<GroupRole>)*"
<CIGroupMemberType> ::= cbcmbrowser|chromeosdevice|customer|group|other|serviceaccount|user
<CIGroupMemberTypeList> ::= "<CIGroupMemberType>(,<CIGroupMemberType>)*"

<CIGroupMembersFieldName> ::=
        createtime
        email|useremail|
        expiretime|
        memberkey|
        name|
        preferredmemberkey|
        role|
        type|
        updatetime
<CIGroupMembersFieldNameList> ::= "<CIGroupMembersFieldName>(,<CIGroupMembersFieldName>)*"

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>
```

## Collections of Users
Group membership commands involve specifying collections of users or lists of browsers/devices;
for `<UserTypeEntity>`, see: [Collections of Users](Collections-of-Users)

## Add members to a group
```
gam update cigroups <GroupEntity> create|add [<GroupRole>]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [expire|expires <Time>] [preview] [actioncsv]
        <UserTypeEntity>|<BrowserDeviceList>
```
When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are added
* `groupsonly` - Only the group members from the specified groups are added

By default, when adding members from organization units, all users, whether suspended or not, are included.
* `notsuspended` - Do not include suspended users, this is common
* `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users

By default, when adding members from groups, all users, whether suspended/archived or not, are included.
* `notsuspended` - Do not include suspended users, this is common
* `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users
* `notarchived` - Do not include archived users
* `archived` - Only include archived users, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived users
* `suspended archived` - Include only suspended or archived users
* `notsuspended archived` - Only include archived users, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

### `actioncsv` Example
Using `actioncsv` produces a CSV file showing the actions taken.
```
$ gam redirect csv AddUpdates.csv update cigroup testgroup add members actioncsv users testuser2,testuser3
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
gam update cigroups <GroupEntity> delete|remove [<GroupRole>]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [preview] [actioncsv]
        <UserTypeEntity>|<BrowserDeviceList>
```
`<GroupRole>` is ignored, deletions take place regardless of role.

When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are deleted
* `groupsonly` - Only the group members from the specified groups are deleted

By default, when deleting members from organization units, all users, whether suspended or not, are included.
* `notsuspended` - Do not include suspended users, this is common
* `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users

By default, when deleting members from groups, all users, whether suspended/archived or not, are included.
* `notsuspended` - Do not include suspended users, this is common
* `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users
* `notarchived` - Do not include archived users
* `archived` - Only include archived users, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived users
* `suspended archived` - Include only suspended or archived users
* `notsuspended archived` - Only include archived users, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

### `actioncsv` Example
Using `actioncsv` produces a CSV file showing the actions taken.
```
$ gam redirect csv DeleteUpdates.csv update cigroup testgroup delete members actioncsv users testuser2,testuser4
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
gam update cigroups <GroupEntity> sync [<GroupRole>|ignorerole]
        [usersonly|groupsonly] [addonly|removeonly]
        [notsuspended|suspended] [notarchived|archived]
        [expire|expires <Time>] [preview] [actioncsv]
        <UserTypeEntity>
```
If `ignorerole` is specified, GAM removes members regardless of role and adds new members with role MEMBER.
This is a special purpose option, use with caution and ensure that `<UserTypeEntity>` specifies the full desired membership list of all roles.

If neither `<GroupRole>` nor `ignorerole` is specified, `member` is assumed.

When `<UserTypeEntity>` specifies a group or groups:
* `usersonly` - Only the user members from the specified groups are added/deleted
* `groupsonly` - Only the group members from the specified groups are added/deleted

By default, when synchronizing members from organization units, all users, whether suspended or not, are included.
* `notsuspended` - Do not include suspended users, this is common
* `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users

By default, when synchronizing members from groups, all users, whether suspended/archived or not, are included.
* `notsuspended` - Do not include suspended users, this is common
* `suspended` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users
* `notarchived` - Do not include archived users
* `archived` - Only include archived users, this is not common but allows creating groups that allow easy identification of archived users
* `notsuspended notarchived` - Do not include suspended and archived users
* `suspended archived` - Include only suspended or archived users
* `notsuspended archived` - Only include archived users, this is not common but allows creating groups that allow easy identification of archived users
* `suspended notarchived` - Only include suspended users, this is not common but allows creating groups that allow easy identification of suspended users

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

### Examples using CSV file and Google sheets:
* https://github.com/GAM-team/GAM/wiki/Collections-of-Users#examples-using-csv-files-and-google-sheets-to-update-the-membership-of-a-group

### Example
Assume that at your school there is a group for each grade level and the members come from an OU; here is a sample CSV file GradeOU.csv
```
Grade,OU
seniors@domain.org,/Students/ClassOf2018
juniors@domain.org,/Students/ClassOf2019
...
```
This allows you to do: `gam csv GradeOU.csv gam update cigroup "~Grade" sync members ou "~OU"`
But suppose that at each grade level there are additional group members that are groups of faculty/staff; e.g., senioradvisors@domain.org.
In this scenario, you can't do the `update cigroup sync` command as the members that are groups will be deleted; the `usersonly` option allows
the `update cigroup sync` command to work: `gam csv GradeOU.csv gam update cigroup "~Grade" sync members usersonly ou "~OU"`
The users from the OU are matched against the user members of the group and adds/deletes are done as necessary to synchronize them;
the group members of the group are unaffected.

### `actioncsv` Example
Using `actioncsv` produces a CSV file showing the actions taken.
```
$ gam redirect csv SyncUpdates.csv update cigroup testgroup sync members actioncsv users testuser1,testuser3,testuser4
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
## Delete members from a group by role
```
gam update cigroups <GroupEntity> clear [member] [manager] [owner]
        [usersonly|groupsonly]
        [emailclearpattern|emailretainpattern <REMatchPattern>]
        [preview] [actioncsv]
```
If none of `member`, `manager`, or `owner` are specified, `member` is assumed.

By default, when clearing members from a group, all members, whether users or groups, are included.
* `usersonly` - Clear only the user members
* `groupsonly` - Clear only the group members

Members that have met the above qualifications to be cleared can be further qualifed by their email address.
* `emailclearpattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be cleared; others will be retained
* `emailretainpattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be retained; others will be cleared

If `preview` is specified, the deletes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

## Update member roles and expiration time
```
gam update cigroups <GroupEntity> update [<GroupRole>]
        [usersonly|groupsonly]
        [notsuspended|suspended] [notarchived|archived]
        [expire|expires <Time>] [preview] [actioncsv]
        <UserTypeEntity>
```
There are two items that can be updated: role and expiration time. If neither option is specified,
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

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `group,email,role,action,message` is generated
that shows the actions performed when updating the group.

## Bulk membership changes
Suppose you have a CSV file (GroupMembers.csv) with headers: group,role,email

Each row contains a group email address, member role (OWNER, MEMBER, MANAGER) and a member email address.

The following command will synchronize the membership for all groups and roles.
```
gam redirect stdout ./MemberUpdates.txt redirect stderr stdout update cigroup csvkmd GroupMembers.csv keyfield group subkeyfield role datafield email sync csvdata email
```
You can also do `create|add`, `delete` and `update` in this manner.

If you want to update a specific role, you can do one of the following.
```
gam redirect stdout ./MemberUpdates.txt redirect stderr stdout update cigroup csvkmd ./GroupMembers.csv keyfield group matchfield role MEMBER datafield email sync member csvdata email
gam redirect stdout ./ManagerUpdates.txt redirect stderr stdout update cigroup csvkmd ./GroupMembers.csv keyfield group matchfield role MANAGER datafield email sync manager csvdata email
gam redirect stdout ./OwnerUpdates.txt redirect stderr stdout update cigroup csvkmd ./GroupMembers.csv keyfield group matchfield role OWNER datafield email sync owner csvdata email
```

## Display user group member options

Display user's group membership information.
```
gam <UserTypeEntity> info cimember <GroupEntity>
gam info cimember <UserTypeEntity> <GroupEntity>
```

## Display group membership in CSV format
```
gam print cigroup-members [todrive <ToDriveAttribute>*]
        [(cimember|showownedby <UserItem>)|(cigroup <GroupItem>)|(select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [roles <GroupRoleList>] [members] [managers] [owners]
        [types <CIGroupMemberTypeList>]
        <CIGroupMembersFieldName>* [fields <CIGroupMembersFieldNameList>]
        [minimal|basic|full]
        [(recursive [noduplicates]) | |includederivedmembership] [nogroupeemail]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
```
By default, the group membership of all groups in the account are displayed, these options allow selection of subsets of groups:
* `cimember <UserItem>` - Limit display to groups that contain `<UserItem>` as a member
* `showownedby <UserItem>` - Limit display to groups owned by `<UserItem>`
* `cigroup <GroupItem>` - Limit display to the single group `<GroupItem>`
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`

By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `roles <GroupRoleList>` - Display specified roles
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners

By default, all types of members (cbcmbrowser, chromeosdevice, customer, group, serviceaccount, user) in the group are displayed; this option modifies that behavior:
* `types <CIGroupMemberTypeList>` - Display specified types

By default, members that are groups are displayed as a single entry of type GROUP; this option recursively expands group members to display their user members.
* `recursive` - Recursively expand group members

When `recursive` is specified, the default is to only display type user members; this option modifies those behaviors:
* `types <GroupMemberTypeList>` - Display specified types

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, the ID, role, email address, type, createTime, updateTime and expireTime of each member is displayed along with the group email address;
these options specify which fields to display:
* `<CIGroupMembersFieldName>*` - Individual field names
* `fields <CIGroupMembersFieldNameList>` - A comma separated list of field names

You can control the fields displayed:
* `minimal` - Fields displayed: group, id, role, email
* `basic` - Fields displayed: group, type, id, role, email, expireTime
* `full` - Fields displayed: group, type, id, role, email, createTime, updateTime, expireTime; this is the default

By default, the group email address is always shown, you can suppress it with the `nogroupemail` option.

The `recursive` option adds two columns, level and subgroup, to the output:
* `level` - At what level of the expansion does the user appear; level 0 is the top level
* `subgroup` - The group that contained the user

Displaying membership of multiple groups or recursive expansion may result in multiple instances of the same user being displayed; these multiple instances can be reduced to one entry.
* `noduplicates` - Reduce multiple instances of the same user to the first instance

The `includederivedmembership` option is an alternative to `recursive`; it causes the API to expand type GROUP
members to display their constituent members. The role displayed for a user is the highest role it
has in any constituent group, it is not necessarily its role in the top group.

The options `recursive noduplicates` and `includederivedmembership types user` return the same list of users.
The `includederivedmembership` option makes less API calls but doesn't show level and subgroup information.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display group membership in hierarchical format
```
gam show cigroup-members
        [(cimember|showownedby <UserItem>)|(cigroup <GroupItem>)|(select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [roles <GroupRoleList>] [members] [managers] [owners]
        [types <CIGroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [minimal|basic|full]
        [(depth <Number>) | includederivedmembership]
```
By default, the group membership of all groups in the account are displayed, these options allow selection of subsets of groups:
* `cimember <UserItem>` - Limit display to groups that contain `<UserItem>` as a member
* `showownedby <UserItem>` - Limit display to groups owned by `<UserItem>`
* `cigroup <GroupItem>` - Limit display to the single group `<GroupItem>`
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`

By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `roles <GroupRoleList>` - Display specified roles
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners

By default, all types of members (cbcmbrowser, chromeosdevice, customer, group, serviceaccount, user) in the group are displayed; this option modifies that behavior:
* `types <CIGroupMemberTypeList>` - Display specified types

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, members of type GROUP are recursively expanded to show their constituent members. (Members of
type CUSTOMER are not expanded.) The `depth <Number>` argument controls the depth to which nested groups are displayed.
* `depth -1` - all groups in the selected group and below are displayed; this is the default.
* `depth 0` - the groups within a selected group are displayed, no descendants are displayed.
* `depth N` - the groups within the selected group and those groups N levels below the selected group are displayed.

The `includederivedmembership` option causes the API to expand type GROUP
members to display their constituent members. The role displayed for a user is the highest role it
has in any constituent group, it is not necessarily its role in the top group.

The options `types user` and `includederivedmembership types user` return the same list of users.
The `includederivedmembership` option makes less API calls but doesn't show hierarchy.

You can control the fields displayed:
* `minimal` - Fields displayed: role, email
* `basic` - Fields displayed: type, role, email, expireTime
* `full` - Fields displayed: type, role, email, createTime, updateTime, expireTime; this is the default

### Display group structure
To see a group's structure of nested groups use the `type group` option.
```
$ gam show cigroup-members group testgroup5 types group
Group: testgroup5@domain.com
  MEMBER, GROUP, testgroup1@domain.com, ACTIVE
    MEMBER, GROUP, testgroup2@domain.com, ACTIVE
  MEMBER, GROUP, testgroup3@domain.com, ACTIVE
    MEMBER, GROUP, testgroup2@domain.com, ACTIVE
    MEMBER, GROUP, testgroup4@domain.com, ACTIVE
```
To show the structure of all groups you can do the following; it will be time consuming for a large number of groups.
```
gam redirect stdout ./groups.txt show cigroup-members types group
```
