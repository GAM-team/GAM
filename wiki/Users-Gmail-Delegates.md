# Users - Gmail - Delegates
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Aliases](#aliases)
- [Create Gmail delegates](#create-gmail-delegates)
- [Delete Gmail delegates](#delete-gmail-delegates)
- [Update Gmail delegates](#update-gmail-delegates)
- [Display Gmail delegates](#display-gmail-delegates)
- [Delete all delegates for a user](#delete-all-delegates-for-a-user)

## Notes

To use Gmail delegation, the delegator and delagatee must be in org units where
mail delegation is enabled. In the admin console, go to Apps/Google Workspace/Gmail/User Settings.

## API documentation
* [Gmail API - Delegates](https://developers.google.com/gmail/api/v1/reference/users.settings.delegates)
* [Delegation Notes](https://support.google.com/a/answer/7223765)
* [Delegation Notes](https://support.google.com/a/answer/11946994)

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
## Aliases

It is an error to use a user's alias as a delegate; if you try, an error will be generated.
The `convertalias` option causes GAM to make an extra API call per user in `<UserEntity>`
to convert aliases to primary email addresses. If you know that all of the email addresses
in `<UserEntity>` are primary, you can omit `convertalias` and avoid the extra API calls.

## Create Gmail delegates
These two commands are equivalent.
```
gam <UserTypeEntity> add delegate|delegates [convertalias] <UserEntity>
gam <UserTypeEntity> delegate|delegates to [convertalias] <UserEntity>
```
### Example

To give Bob access to Fred's mailbox as a delegate:

```
gam user fred@domain.com add delegate bob@domain.com
```

## Delete Gmail delegates
```
gam <UserTypeEntity> delete|del delegate|delegates [convertalias] <UserEntity>
```
## Update Gmail delegates
Update delegates to be able to access a user's contacts.
```
gam <UserTypeEntity> update delegate|delegates [convertalias] [<UserEntity>]
```
If `<UserEntity>` is omitted, all of a user's accepted delegates are updated.

## Display Gmail delegates
```
gam <UserTypeEntity> show delegates|delegate [shownames] [csv]
gam <UserTypeEntity> print delegates|delegate [todrive <ToDriveAttribute>*] [shownames]
```
By default, delegate names are not displayed; use the `shownames` option to display the delegates name.
This involves an extra API call per delegate email address.

By default, `show delegates` displays indented keys and values; use the `csv` option to have just the values
shown as a comma separated list.

## Delete all delegates for a user
```
$ gam redirect csv ./Delegates.csv user testsimple print delegates
Getting all Delegates for testsimple@domain.com
$ gam redirect stdout - multiprocess csv Delegates.csv gam user "~User" delete delegate "~delegateAddress"
2023-11-10T06:56:04.118-08:00,0/3,Using 3 processes...
2023-11-10T06:56:04.123-08:00,0,Processing item 3/3
User: testsimple@domain.com, Delete 1 Delegate
  User: testsimple@domain.com, Delegate: testuser1@domain.com, Deleted
User: testsimple@domain.com, Delete 1 Delegate
  User: testsimple@domain.com, Delegate: testuser2@domain.com, Deleted
User: testsimple@domain.com, Delete 1 Delegate
  User: testsimple@domain.com, Delegate: testgroup@domain.com, Deleted
2023-11-10T06:56:07.253-08:00,0/3,Processing complete
```
