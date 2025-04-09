# Users - Contacts - Delegates
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Create contact delegates](#create-contact-delegates)
- [Delete contact delegates](#delete-contact-delegates)
- [Display contact delegates](#display-contact-delegates)

## API documentation
* [Contact Delegation API](https://developers.google.com/admin-sdk/contact-delegation/reference/rest/v1/admin.contacts.v1.users.delegates)

## Notes
Contact delegation must be enabled, see the following:

* [Contact Delegation Notes](https://support.google.com/contacts/answer/2590392)
* [Directory Sharing Notes](https://support.google.com/a/answer/60218?sjid=15009482130973386336-NA)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>
<UserList> ::= "<UserItem>(,<UserItem>)*"
<UserEntity> ::=
        <UserList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Users
```
## Create contact delegates
```
gam <UserTypeEntity> create|add contactdelegate <UserEntity>
```
## Delete contact delegates
```
gam <UserTypeEntity> delete|del contactdelegate <UserEntity>
```
## Display contact delegates
```
gam <UserTypeEntity> show contactdelegates [shownames] [csv]
gam <UserTypeEntity> print contactdelegates [todrive <ToDriveAttribute>*] [shownames]
```
By default, delegate names are not displayed; use the `shownames` option to display the delegates name.
This involves an extra API call per delegate email address.

By default, `show delegates` displays indented keys and values; use the `csv` option to have just the values
shown as a comma separated list.
