# Permission Matches
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [File Selection](#file-selection)
- [Permission Selection](#permission-selection)
- [Define a Match](#define-a-match)
- [File Selection Examples](#file-selection-examples)
- [Permission Selection Examples](#permission-selection-examples)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<DomainNameList> ::= "<DomainName>(,<DomainName>)*"

<DriveFileACLRole> ::=
        commenter|
        contentmanager|fileorganizer|
        contributor|editor|writer|
        manager|organizer|owner|
        reader|viewer
<DriveFileACLRoleList> ::= "<DriveFileACLRole>(,<DriveFileACLRole>)*"

<DriveFileACLType> ::= anyone|domain|group|user
<DriveFileACLTypeList> ::= "<DriveFileACLType>(,<DriveFileACLType>)*"

<EmailAddress> ::= <String>@<DomainName>
<EmailAddressList> ::= "<EmailAddress>(,<EmailAddress>)*"

<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<PermissionMatch> ::=
        pm|permissionmatch [not]
            [type|nottype <DriveFileACLType>] [role|notrole <DriveFileACLRole>]
            [typelist|nottypelist <DriveFileACLTypeList>] [rolelist|notrolelist <DriveFileACLRoleList>]
            [allowfilediscovery|withlink <Boolean>]
            [emailaddress <REMatchPattern>] [emailaddressList <EmailAddressList>]
            [permissionidlist <PermissionIDList>
            [name|displayname <String>]
            [domain|notdomain <REMatchPattern>] [domainlist|notdomainlist <DomainNameList>]
            [expirationstart <Time>] [expirationend <Time>]
            [deleted <Boolean>] [inherited <Boolean>] [permtype member|file]
        em|endmatch
<PermissionMatchMode> ::=
        pmm|permissionmatchmode or|and
<PermissionMatchAction> ::=
        pma|permissionmatchaction process|skip
```
## File Selection
In the `print/show filecounts/filelists/filetree` commands you can limit the files counted/displayed by specifying permissions
that the file must/must not have. Permission matching is expensive on Shared Drives as retrieving the permissions requires a separate API call per file.

You can define multiple `<PermissionMatches>`; each match specifies a set of required fields/values. A permission
matches if all of its fields/values match the required fields/values; you can negate the match with `not`.

### Permission Match Mode
When you specify multiple `<PermissionMatches>`, `<PermissionMatchMode>` controls whether there is a permissions match
when any or all or the `<PermissionMatches>` match.
* `pmm or` - If any `<PermissionMatch>` matches, then there is a permissions match. This is the default.
* `pmm and` - If all `<PermissionMatches>` match, then there is a permissions match.

### Permission Match Action
`<PermissionMatchAction>` controls processing when there is a permissions match.
* `pma process` - If there is a  permissions match, count/display the file. This is the default.
* `pma skip` - If there is a permissions match, do not count/display the file.

## Permission Selection
In the `print/show drivefileacls` and `create/delete permissions` commands you can limit the permissions displayed/processed.

* `pma process` - If a permission matches, display/process the permission. This is the default.
* `pma skip` - If a permission matches, do not display/process the permission.

## Define a Match
* `pm|permissionmatch` - Start of permission match definition.
* `not` - Negate the match.
* `type <DriveFileACLType>` - The type of the grantee must match.
* `nottype <DriveFileACLType>` - The type of the grantee must not match.
* `typelist <DriveFileACLTypeList>` - The type of the grantee must match any value in the list.
* `nottypelist <DriveFileACLTypeList>` - The type of the grantee must not match any value in the list.
* `role <DriveFileACLRole>` - The role granted by this permission must match.
* `notrole <DriveFileACLRole>` - The role granted by this permission must not match.
* `rolelist <DriveFileACLRoleList>` - The role granted by this permission must match any value in the list..
* `notrolelist <DriveFileACLRoleList>` - The role granted by this permission must not match any value in the list..
* `allowfilediscovery|withlink <Boolean>` - Whether a link is required or whether the file can be discovered through search.
* `emailaddress <REMatchPattern>` - For types user and group, the required email address.
* `emailaddresslist <EmailAddressList>` - For types user and group, a list of required email addresses; any one of which must match.
* `permissionidlist <PermissionIDListList>` - A list of required permission IDs; any one of which must match.
* `name|displayname <REMatchPattern>` - For types domain, user and group, the displayable name.
* `domain <REMatchPattern>` - For type domain, the required domain name. For types user and group, the required domain name in the email address.
* `notdomain <REMatchPattern>` - For type domain, any domain name that doesn't match. For types user and group, any domain name that doesn't match in the email address.
* `domainlist <DomainNameList>` - For type domain, the required domain name. For types user and group, the required domain name in the email address.
* `notdomainlist <DomainNameList>` - For type domain, any domain name that doesn't match. For types user and group, any domain name that doesn't match in the email address.
* `expirationstart <Time>` - For types user and group, will the permission expire on or after <Time>.
* `expirationend <Time>` - For types user and group, will the permission expire before or on <Time>.
* `deleted <Boolean>` - For types user and groups, has the user or group been deleted.
* `inherited <Boolean>` - For Shared Drive files/folders, is the permission inherited
* `permtype member|file` - For Shared Drive files/folders, is the permission derived from membership or explicitly granted.
* `em|endmatch` - End of permission match definition

## File Selection Examples

These are the permission match definitions that would be appended to a command like:
```
gam user user@domain.com print filelist ...
```

Process all files with permissions type anyone:
```
pm type anyone em
```

Process all files except those with permissions type anyone:
```
pm type anyone em
pma skip
```
Process all files owned by someout outside of your domain
```
pm type user role owner notdomain mydomain.com em
```
Process all files shared to users outside of your domains
```
pm type user notrole owner notdomainlist mydomain1.com,mydomain2.com em
```
Process all files with write access for group@domain.com or user@domain.com:
```
pm role writer type group emailaddress group@domain.com em
pm role writer type user emailaddress user@domain.com em
```
Process all files with write access for group@domain.com and user@domain.com:
```
pm role writer type group emailaddress group@domain.com em
pm role writer type user emailaddress user@domain.com em
pmm and
```
Process all files where neither user1@domain.com or user2@domain.com have access:
```
pm type user emailaddress user1@domain.com em
pm type user emailaddress user2@domain.com em
pma skip
```
or you can use regular expressions
```
pm type user emailaddress "user[1|2]@domain.com" em
pma skip
```
Process all files shared with group group@domain.com and not shared with user user@domain.com:
```
pm type group emailaddress group@domain.com em pm not type user user@domain.com em pmm and
```

Process all files shared with domain.com either directly or via a user or group.
```
pm domain domain.com em pm emailaddress ".*@domain.com" em
```

Display all non-inherited permissions on a Shared Drive.
```
pm inherited false em
```
## Permission Selection Examples
These are the permission match definitions that would be appended to a command like:
```
gam user user@domain.com print drivefileacls  ...
```

Display all permissions shared with domain.com either directly or via a user or group.
```
pm domain domain.com em pm emailaddress ".*@domain.com" em
```

Display target audience permissions.
```
pm type domain domain ".+.audience.googledomains.com" em
```
