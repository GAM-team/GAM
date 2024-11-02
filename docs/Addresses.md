# Addresses
- [API documentation](#api-documentation)
- [Display addresses](#display-addresses)

## API documentation
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/domains
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/groups
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.calendars
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/users

## Display addresses
Produces a three column CSV file (headers Type, Email, Target) that displays all group and user primary
email addresses and aliases; resource calendar addresses and domain names.

The types are:
```
DomainPrimary, DomainSecondary, DomainAlias
Group, GroupAlias, GroupNEAlias
Resource
SuspendedUser, SuspendedUserAlias, SuspendedUserNEAlias
User, UserAlias, UserNEAlias
```
'NE' is an abbreviation for NonEditable.
```
gam print addresses [todrive <ToDriveAttribute>*]
        [domain <DomainName>]
```
By default, groups and users in all domains in the account are selected; this options allows selection of subsets of groups and users:
* `domain <DomainName>` - Limit groups and users to those in `<DomainName>`

