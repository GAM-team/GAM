# Users - Group Membership
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Add users to groups](#add-users-to-groups)
- [Delete users from groups](#delete-users-from-groups)
- [Delete external user from groups](#delete-external-user-from-groups)
- [Update users group roles and delivery settings](#update-users-group-roles-and-delivery-settings)
- [Synchronize users group membership](#synchronize-users-group-membership)
- [Check users group membership](#check-users-group-membership)
- [Display users group membership](#display-users-group-membership)
  - [Display group names as an indented list](#display-group-names-as-an-indented-list)
  - [Display group names in CSV format](#display-group-names-in-csv-format)
  - [Display group details as an indented list](#display-group-details-as-an-indented-list)
  - [Display group details in CSV format](#display-group-details-in-csv-format)
  - [Display group counts as an indented list](#display-group-counts-as-an-indented-list)
  - [Display group counts in CSV format](#display-group-counts-in-csv-format)
  - [Display total group counts as an indented list](#display-total-group-counts-as-an-indented-list)
  - [Display total group counts in CSV format](#display-total-group-counts-in-csv-format)
  - [Display group addresses in CSV format](#display-group-addresses-in-csv-format)
  - [Display groups and their parents](#display-groups-and-their-parents)
- [Add a target user to the same groups as a source user](#add-a-target-user-to-the-same-groups-as-a-source-user)

## API documentation
* [Directory API - Members](https://developers.google.com/admin-sdk/directory/reference/rest/v1/members)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DeliverySetting> ::=
        allmail|
        abridged|daily|
        digest|
        disabled|
        none|nomail
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<GroupList> ::= "<GroupItem>(,<GroupItem>)*"
<GroupEntity> ::=
        <GroupList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<GroupRole> ::= owner|manager|member
<GroupRoleList> ::= "<GroupRole>(,<GroupRole>)*"

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>
```
## Add users to groups
Add each user in `<UserTypeEntity>` to all of the groups specified by `([<GroupRole>] <GroupEntity>)+`.
If `<GroupRole>` is not specified, `member` is assumed.
```
gam <UserTypeEntity> add group|groups
        ([<GroupRole>] [[delivery] <DeliverySetting>] <GroupEntity>)+
```

### Basic Example
Add a user to several groups with different roles.
```
$ gam user testuser1@domain.com add groups owner testgroup1@domain.com manager testgroup2@domain.com member testgroup3@domain.com,testgroup4@domain.com
User: testuser1@domain.com, Add to 4 Groups
  Group: testgroup1@domain.com, Owner: testuser1@domain.com, Added (1/4)
  Group: testgroup2@domain.com, Manager: testuser1@domain.com, Added (2/4)
  Group: testgroup3@domain.com, Member: testuser1@domain.com, Added (3/4)
  Group: testgroup4@domain.com, Member: testuser1@domain.com, Added (4/4)

```

### Advanced Example
Use a CSV file to specify users, groups and roles.
```
# Desired state
$ more UserGroupRole.csv
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE

# Current state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery

# Add users to groups
$ gam redirect stdout - multiprocess csv UserGroupRole.csv gam user "~User" add group "~Role" "~Delivery" "~Group"
Using 5 processes...
User: testuser1@domain.com, Add to 1 Group
  Group: testgroup1@domain.com, Owner: testuser1@domain.com, Added
User: testuser1@domain.com, Add to 1 Group
  Group: testgroup4@domain.com, Member: testuser1@domain.com, Added
User: testuser2@domain.com, Add to 1 Group
  Group: testgroup1@domain.com, Member: testuser2@domain.com, Added
User: testuser1@domain.com, Add to 1 Group
  Group: testgroup3@domain.com, Member: testuser1@domain.com, Added
User: testuser1@domain.com, Add to 1 Group
  Group: testgroup2@domain.com, Manager: testuser1@domain.com, Added
User: testuser3@domain.com, Add to 1 Group
  Group: testgroup1@domain.com, Member: testuser3@domain.com, Added
User: testuser2@domain.com, Add to 1 Group
  Group: testgroup2@domain.com, Manager: testuser2@domain.com, Added
User: testuser3@domain.com, Add to 1 Group
  Group: testgroup2@domain.com, Owner: testuser3@domain.com, Added

# Final state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE
```

## Delete users from groups
```
gam <UserTypeEntity> delete group|groups
        [(domain <DomainName>)|(customerid <CustomerID>)|
         (emailmatchpattern [not] <REMatchPattern>)|<GroupEntity>]
```
By default, users will be deleted from all groups of which they are a member, these options allow selection of subsets of groups:
* `domain <DomainName>` - Delete from all groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, delete from all groups in a resold workspace of which they are a member
* `emailmatchpattern [not] <REMatchPattern>` - Delete from all groups of which they are a member based on (not) matching the group email address
* `<GroupEntity>` - Delete from a specific list of groups

### Basic Examples
Delete a user from all groups to which it belongs.
```
$ gam user testuser1@domain.com delete groups
User: testuser1@domain.com, Delete from 4 Groups
  Group: testgroup1@domain.com, Member: testuser1@domain.com, Deleted (1/4)
  Group: testgroup2@domain.com, Member: testuser1@domain.com, Deleted (2/4)
  Group: testgroup3@domain.com, Member: testuser1@domain.com, Deleted (3/4)
  Group: testgroup4@domain.com, Member: testuser1@domain.com, Deleted (4/4)
```

Delete users from all groups to which they belong. Assume a CSV file NoGroupsUsers.csv with a column labelled primaryEmail
that lists the users.
```
gam csv NoGroupsUsers.csv gam user "~primaryEmail" delete groups
```

### Advanced Example
Use a CSV file to specify users and groups.
```
# Current state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE

# Delete users from groups
$ gam csvkmd users UserGroupRole.csv keyfield User delete groups
User: testuser1@domain.com, Delete from 4 Groups (1/3)
  Group: testgroup1@domain.com, Member: testuser1@domain.com, Deleted (1/4)
  Group: testgroup2@domain.com, Member: testuser1@domain.com, Deleted (2/4)
  Group: testgroup3@domain.com, Member: testuser1@domain.com, Deleted (3/4)
  Group: testgroup4@domain.com, Member: testuser1@domain.com, Deleted (4/4)
User: testuser2@domain.com, Delete from 2 Groups (2/3)
  Group: testgroup1@domain.com, Member: testuser2@domain.com, Deleted (1/2)
  Group: testgroup2@domain.com, Member: testuser2@domain.com, Deleted (2/2)
User: testuser3@domain.com, Delete from 2 Groups (3/3)
  Group: testgroup1@domain.com, Member: testuser3@domain.com, Deleted (1/2)
  Group: testgroup2@domain.com, Member: testuser3@domain.com, Deleted (2/2)

# Final state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
```
## Delete external user from groups
There is a user from outside of your domain that you would like to delete from all groups.
```
$ gam user user@external.com delete groups
User: user@external.com, Delete from 0 Groups
```

There is a Goggle issue that causes this to fail for a few external addresses.
To solve this problem, you need the unique ID for the external address;
the following steps show how to do this.

Create a test group.
```
$ gam create group testexternal description "Test External Email Addresses"
Group: testexternal@domain.com, Created
```

Add the external address to that group.
```
$ gam update group testexternal add member user@external.com
Group: testexternal@domain.com, Add 1 Member
  Group: testexternal@domain.com, Member: user@external.com, Added: Role: MEMBER
```

Print the group members of the group to get the unique ID of the external address.
```
$ gam print group-members group testexternal
Getting all Members, Managers, Owners for testexternal@domain.com
group,type,role,id,status,email
testexternal@domain.com,USER,MEMBER,123406166545652215678,,user@external.com
```

Delete the external address from all groups.
```
$ gam user uid:123406166545652215678 delete groups
User: 123406166545652215678, Delete from 2 Groups
  Group: testexternal@domain.com, Member: 123406166545652215678, Deleted (1/2)
  Group: testgroup@domain.com, Member: 123406166545652215678, Deleted (2/2)
```

## Update users group roles and delivery settings
For each user in `<UserTypeEntity>` update their current group role and delivery settings.
```
gam <UserTypeEntity> update group|groups
        [(domain <DomainName>)|(customerid <CustomerID>)]) [<GroupRole>] [[delivery] <DeliverySetting>]
        ([<GroupRole>] [[delivery] <DeliverySetting>] [<GroupEntity>])*
```
By default, update user roles and delivery settings for all groups of which they are a member, these options allow selection of subsets of groups:
* `domain <DomainName>` - Update user role and delivery settings for all groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, update user role and delivery settings for all groups in a resold workspace of which they are a member
* `<GroupEntity>` - Update user role and delivery settings for a specific list of groups; you can specify different roles and delivery settings for different group lists

### Example
```
# Current state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE

# Desired changes
$ more UserGroupRoleNew.csv
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup2@domain.com,OWNER,ACTIVE,DIGEST
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,DIGEST

# Update roles/delivery settings
$ gam redirect stdout - multiprocess csv UserGroupRoleNew.csv gam user "~User" update group "~Role" "~Delivery" "~Group"
Using 3 processes...
User: testuser2@domain.com, Update to 1 Group
  Group: testgroup2@domain.com, Manager: testuser2@domain.com, Updated
User: testuser3@domain.com, Update to 1 Group
  Group: testgroup2@domain.com, Owner: testuser3@domain.com, Updated
User: testuser1@domain.com, Update to 1 Group
  Group: testgroup2@domain.com, Owner: testuser1@domain.com, Updated

# Final state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,DIGEST
```
## Synchronize users group membership
For each user in `<UserTypeEntity>` get their current group membership and do adds and deletes as necessary to match `([<GroupRole>] <GroupEntity>)+`.
If `<GroupRole>` is not specified, `member` is assumed.
```
gam <UserTypeEntity> sync group|groups
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [<GroupRole>] [[delivery] <DeliverySetting>] <GroupEntity>)*
```
By default, users will be synchronized with all groups of which they are a member, these options allow selection of subsets of groups:
* `domain <DomainName>` - Synchronize with all groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, synchronize with all groups in a resold workspace of which they are a member

### Basic Example
```
# Current state
$ gam user testuser1@domain.com print groups
User,Group,Role
testuser1@domain.com,testgroup2@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup5@domain.com,MEMBER,ACTIVE,ALL_MAIL

# Update membership
$ gam user testuser1@domain.com sync groups owner testgroup1@domain.com manager testgroup2@domain.com member testgroup3@domain.com,testgroup4@domain.com
User: testuser1@domain.com, Remove from 1 Group
  Group: testgroup5@domain.com, Member: testuser1@domain.com, Removed
User: testuser1@domain.com, Add to 1 Group
  Group: testgroup1@domain.com, Owner: testuser1@domain.com, Added
User: testuser1@domain.com, Update in 1 Group
  Group: testgroup2@domain.com, Manager: testuser1@domain.com, Updated

# Final state
$ gam user testuser1@domain.com print groups
User,Group,Role
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
```
### Advanced Example
```
# Current state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup5@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL

# Desired state
$ more UserGroupRole.csv
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE

# Update membership
$ gam csvkmd users UserGroupRole.csv keyfield User subkeyfield Role datafield Group sync groups csvdata Group
User: testuser1@domain.com, Remove from 1 Group (1/3)
  Group: testgroup5@domain.com, Member: testuser1@domain.com, Removed
User: testuser2@domain.com, Update to 1 Group (2/3)
  Group: testgroup2@domain.com, Manager: testuser2@domain.com, Updated
User: testuser3@domain.com, Add to 1 Group (3/3)
  Group: testgroup2@domain.com, Owner: testuser3@domain.com, Added

# Intermediate state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,ALL_MAIL

# Update roles/delivery settings
$ gam redirect stdout - multiprocess csv UserGroupRole.csv gam user "~User" update group "~Role" "~Delivery" "~Group"
Using 5 processes...
User: testuser2@domain.com, Update to 1 Group
  Group: testgroup1@domain.com, Member: testuser2@domain.com, Updated
User: testuser1@domain.com, Update to 1 Group
  Group: testgroup4@domain.com, Member: testuser1@domain.com, Updated
User: testuser1@domain.com, Update to 1 Group
  Group: testgroup3@domain.com, Member: testuser1@domain.com, Updated
User: testuser1@domain.com, Update to 1 Group
  Group: testgroup2@domain.com, Manager: testuser1@domain.com, Updated
User: testuser1@domain.com, Update to 1 Group
  Group: testgroup1@domain.com, Owner: testuser1@domain.com, Updated
User: testuser3@domain.com, Update to 1 Group
  Group: testgroup1@domain.com, Member: testuser3@domain.com, Updated
User: testuser2@domain.com, Update to 1 Group
  Group: testgroup2@domain.com, Manager: testuser2@domain.com, Updated
User: testuser3@domain.com, Update to 1 Group
  Group: testgroup2@domain.com, Owner: testuser3@domain.com, Updated

# Final state
$ gam csvkmd users UserGroupRole.csv keyfield User print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser2@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup1@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE

```
## Check users group membership
For each user in `<UserTypeEntity>` check if they are members of the groups in `<GroupEntity>` with a role
in `role <GroupsRoleList>`; if not specified, any role is acceptable.
```
gam <UserTypeEntity> check group|groups
        [roles <GroupRoleList>] [includederivedmembership] [csv] <GroupEntity>
```
By default, only direct membership is checked; include the `includederivedmembership` to check
if a user is a member of a group or one of its sub-groups.

By default, the output is indented keys and values written to stdout;
use the `csv` option to write the output to a CSV file.

A return code of 0 indicates that a user is a member of all of the groups with an acceptable role;
a return code of 29 indicates that the user is not a member of all of the groups.

## Display users group membership
It takes one API call to get the list of groups to which a user belongs.

### Display group names as an indented list
There is one row per group to which a user belongs.
```
gam <UserTypeEntity> show groups
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>] nodetails
```

### Display group names in CSV format
There is one row per user/group combination.
```
gam <UserTypeEntity> print groups [todrive <ToDriveAttribute>*]
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>] nodetails
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member
* `roles <GroupRoleList>` - Limit display to those groups for which the user has a specific role

### Display group details as an indented list
There is one row per group to which a user belongs showing role, status and delivery information.

There is one API call per user/group to get the user's role and delivery settings.
```
gam <UserTypeEntity> show groups
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>]
```

### Display group details in CSV format
There is one row per user/group combination displaying role, status and delivery information.

There is one API call per user/group to get the user's role and delivery settings.
```
gam <UserTypeEntity> print groups [todrive <ToDriveAttribute>*]
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>]
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member
* `roles <GroupRoleList>` - Limit display to those groups for which the user has a specific role

### Display group counts as an indented list
There is one row per user displaying the number of groups, by role, to which a user belongs.

There is one API call per user/group to get the user's role.
```
gam <UserTypeEntity> show groups
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>] countsonly
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member
* `roles <GroupRoleList>` - Limit display to those groups for which the user has a specific role

### Display group counts in CSV format
There is one row per user displaying the number of groups, by role, to which a user belongs.

There is one API call per user/group to get the user's role.
```
gam <UserTypeEntity> print groups [todrive <ToDriveAttribute>*]
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>] countsonly
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member
* `roles <GroupRoleList>` - Limit display to those groups for which the user has a specific role

### Display total group counts as an indented list
There is one row per user displaying the number of groups to which a user belongs.

There is one API call per user to get the total group count.
```
gam <UserTypeEntity> show groups
        [(domain <DomainName>)|(customerid <CustomerID>)]
        totalonly
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member


### Display total group counts in CSV format
There is one row per user displaying the total number of groups to which a user belongs.

There is one API call per user to get the total group count.
```
gam <UserTypeEntity> print groups [todrive <ToDriveAttribute>*]
        [(domain <DomainName>)|(customerid <CustomerID>)]
        totalonly
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member

### Display group addresses in CSV format
There is one row per user showing the number and list of groups to which a user directly belongs.
```
gam <UserTypeEntity> print groupslist [todrive <ToDriveAttribute>*]
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [delimiter <Character>] [quotechar <Character>]
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member

By default, the entries in lists of groups are separated by the `csv_output_field_delimiter' from `gam.cfg`.
* `delimiter <Character>` - Separate list items with `<Character>`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

#### Examples
```
$ gam user testuser1@domain.com show groups
User: testuser1@domain.com, Show 4 Groups
  Group: testgroup1@domain.com, Role: OWNER, Status: ACTIVE, Delivery: DIGEST (1/4)
  Group: testgroup2@domain.com, Role: MANAGER, Status: ACTIVE, Delivery: DAILY (2/4)
  Group: testgroup3@domain.com, Role: MEMBER, Status: ACTIVE, Delivery: ALL_MAIL (3/4)
  Group: testgroup4@domain.com, Role: MEMBER, Status: ACTIVE, Delivery: ALL_MAIL (4/4)

$ gam user testuser1@domain.com print groups
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser1@domain.com,testgroup2@domain.com,MANAGER,ACTIVE,DAILY
testuser1@domain.com,testgroup3@domain.com,MEMBER,ACTIVE,ALL_MAIL
testuser1@domain.com,testgroup4@domain.com,MEMBER,ACTIVE,ALL_MAIL

$ gam csvkmd users UserGroupRole.csv keyfield User show groups role owner
User: testuser1@domain.com, Show maximum of 4 Groups (1/3)
  Group: testgroup1@domain.com, Role: OWNER, Status: ACTIVE, Delivery: DIGEST (1/4)
User: testuser2@domain.com, Show maximum of 2 Groups (2/3)
User: testuser3@domain.com, Show maximum of 2 Groups (3/3)
  Group: testgroup2@domain.com, Role: OWNER, Status: ACTIVE, Delivery: NONE (2/2)

$ gam csvkmd users UserGroupRole.csv keyfield User print groups role owner
User,Group,Role,Status,Delivery
testuser1@domain.com,testgroup1@domain.com,OWNER,ACTIVE,DIGEST
testuser3@domain.com,testgroup2@domain.com,OWNER,ACTIVE,NONE

$ gam users testuser1,testuser2 show groups domain domain.net
User: testuser1@domain.com, Show maximum of 2 Groups (1/2)
  Group: testgroup@domain.net, Role: MEMBER (1/2)
  Group: testnet@domain.net, Role: MEMBER (2/2)
User: testuser2@domain.com, Show maximum of 0 Groups (2/2)

$ gam users testuser1,testuser2 print groups domain domain.net
User,Group,Role
testuser1@domain.com,testgroup@domain.net,MEMBER
testuser1@domain.com,testnet@domain.net,MEMBER

$ gam users testuser1,testuser2 print groupslist
Getting all Groups for testuser1@domain.com (1/2)
Getting all Groups for testuser2@domain.com (2/2)
User,Groups,GroupsList
testuser1@domain.com,6,classroom_teachers@domain.com testfromgroup@domain.com testgroup1@domain.com testgroup2@domain.com testgroup4@domain.com testgroup@domain.com
testuser2@domain.com,0,

$ gam config csv_output_row_filter "Groups:count=0" users testuser1,testuser2 print groupslist
Getting all Groups for testuser1@domain.com (1/2)
Getting all Groups for testuser2@domain.com (2/2)
User,Groups,GroupsList
testuser2@domain.com,0,
```
### Display groups and their parents
Display a user's groups and their parents as an indented list.
```
gam <UserTypeEntity> show grouptree
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>]
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member

By default, all of a users's groups are displayed without role information. Displaying role
information requires an additional API call per user/group combination.
* `roles <GroupRoleList>` - Display groups with role information where the user has one of the specified roles

Display a user's groups and their parents in CSV format.
```
gam <UserTypeEntity> print grouptree [todrive <ToDriveAttribute>*]
        [(domain <DomainName>)|(customerid <CustomerID>)]
        [roles <GroupRoleList>]
        [showparentsaslist [<Boolean>]] [delimiter <Character>]
```
By default, all groups to which a member belongs are displayed, these options allow selection of subsets of groups:
* `domain <DomainName>` - Limit display to groups in the domain `<DomainName>` of which they are a member
* `customerid <CustomerID>` - For resellers, display all groups in a resold workspace of which they are a member

By default, all of a users's groups are displayed without role information. Displaying role
information requires an additional API call per user/group combination.
* `roles <GroupRoleList>` - Display groups with role information where the user has one of the specified roles

By default, the group parent emails and names are displayed in multiple indexed columns.
Use options `showparentsaslist [<Boolean>]` and `delimiter <Character>` to display
the group parent emails and names in two columns as delimited lists .

#### Examples
```
$ gam user testuser1@domain.com show grouptree
User: testuser1@domain.com, Show maximum of 4 Group Trees
  testgroup1@domain.com: Test Group1 (1/4)
    testgroup@domain.com: Test Group Org
  testgroup2@domain.com: Test - Group 2 (2/4)
    testgroup1@domain.com: Test Group1
      testgroup@domain.com: Test Group Org
    testgroup@domain.net: Test Group Net
  testgroup3@domain.com: Test - Group 3 (3/4)
  testgroup@domain.com: Test Group Org (4/4)

$ gam user testuser1@domain.com show grouptree roles member,manager,owner
User: testuser1@domain.com, Show 4 Group Trees
  testgroup1@domain.com: Test Group1, Role: MEMBER (1/4)
    testgroup@domain.com: Test Group Org
  testgroup2@domain.com: Test - Group 2, Role: MEMBER (2/4)
    testgroup1@domain.com: Test Group1
      testgroup@domain.com: Test Group Org
    testgroup@domain.net: Test Group Net
  testgroup3@domain.com: Test - Group 3, Role: MANAGER (3/4)
  testgroup@domain.com: Test Group Org, Role: MEMBER (4/4)

$ gam user testuser1@domain.com show grouptree roles manager 
User: testuser1@domain.com, Show maximum of 4 Group Trees
  testgroup3@domain.com: Test - Group 3, Role: MANAGER (3/4)

$ gam user testuser1@domain.com print grouptree
User,Group,Name,parents,parents.0.email,parents.0.name,parents.1.email,parents.1.name
testuser1@domain.com,testgroup1@domain.com,Test Group1,1,testgroup@domain.com,Test Group Org,,
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,2,testgroup1@domain.com,Test Group1,testgroup@domain.com,Test Group Org
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,1,testgroup@domain.net,Test Group Net,,
testuser1@domain.com,testgroup3@domain.com,Test - Group 3,0,,,,
testuser1@domain.com,testgroup@domain.com,Test Group Org,0,,,,

$ gam user testuser1@domain.com print grouptree showparentsaslist delimiter "|"
User,Group,Name,ParentsCount,Parents,ParentsName
testuser1@domain.com,testgroup1@domain.com,Test Group1,1,testgroup@domain.com,Test Group Org
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,2,testgroup1@domain.com|testgroup@domain.com,Test Group1|Test Group Org
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,1,testgroup@domain.net,Test Group Net
testuser1@domain.com,testgroup3@domain.com,Test - Group 3,0,,
testuser1@domain.com,testgroup@domain.com,Test Group Org,0,,

$ gam user testuser1@domain.com print grouptree roles member,manager,owner
User,Group,Name,Role,parents,parents.0.email,parents.0.name,parents.1.email,parents.1.name
testuser1@domain.com,testgroup1@domain.com,Test Group1,MEMBER,1,testgroup@domain.com,Test Group Org,,
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,MEMBER,2,testgroup1@domain.com,Test Group1,testgroup@domain.com,Test Group Org
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,MEMBER,1,testgroup@domain.net,Test Group Net,,
testuser1@domain.com,testgroup3@domain.com,Test - Group 3,MANAGER,0,,,,
testuser1@domain.com,testgroup@domain.com,Test Group Org,MEMBER,0,,,,

$ gam user testuser1@domain.com print grouptree roles member,manager,owner showparentsaslist delimiter "|"
User,Group,Name,Role,ParentsCount,Parents,ParentsName
testuser1@domain.com,testgroup1@domain.com,Test Group1,MEMBER,1,testgroup@domain.com,Test Group Org
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,MEMBER,2,testgroup1@domain.com|testgroup@domain.com,Test Group1|Test Group Org
testuser1@domain.com,testgroup2@domain.com,Test - Group 2,MEMBER,1,testgroup@domain.net,Test Group Net
testuser1@domain.com,testgroup3@domain.com,Test - Group 3,MANAGER,0,,
testuser1@domain.com,testgroup@domain.com,Test Group Org,MEMBER,0,,

$ gam user testuser1@domain.com print grouptree roles manager 
User,Group,Name,Role,parents
testuser1@domain.com,testgroup3@domain.com,Test - Group 3,MANAGER,0

$ gam config csv_output_header_drop_filter "name,parents.*name" user testuser1@domain.com print grouptree
User,Group,parents,parents.0.email,parents.1.email
testuser1@domain.com,testgroup1@domain.com,1,testgroup@domain.com,
testuser1@domain.com,testgroup2@domain.com,2,testgroup1@domain.com,testgroup@domain.com
testuser1@domain.com,testgroup2@domain.com,1,testgroup@domain.net,
testuser1@domain.com,testgroup3@domain.com,0,,
testuser1@domain.com,testgroup@domain.com,0,,
```

## Add a target user to the same groups as a source user
Get the source user group information.
```
gam redirect csv ./SourceGroups.csv user sourceuser@domain.com print groups
```

Add the target user to the these groups with the same role and delivery settings.
```
gam csv ./SourceGroups.csv gam user targetuser@domain.com add group "~Role" delivery "~Delivery" "~Group"
```
