# Users - Gmail - Delegates
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Aliases](#aliases)
- [Delegation Notification](#delegation-notification)
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

<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>

<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)

<NotifyMessageContent> ::=
        (message|textmessage|htmlmessage <String>)|
        (file|textfile|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
```
## Aliases

It is an error to use a user's alias as a delegate; if you try, an error will be generated.
The `convertalias` option causes GAM to make an extra API call per user in `<UserEntity>`
to convert aliases to primary email addresses. If you know that all of the email addresses
in `<UserEntity>` are primary, you can omit `convertalias` and avoid the extra API calls.

## Delegation Notification
When creating a delegate, you can send a message to the delegate.
```
[notify [<Boolean>]
    [subject <String>]
    [from <EmailAaddress>] [mailbox <EmailAddress>]
    [replyto <EmailAddress>]
    [<NotifyMessageContent>] [html [<Boolean>]]
]
```
* `notify [<Boolean>]` - Should notification be sent

In the subject and message, these strings will be replaced with the specified values:
* `#user#` - user's email address
* `#delegate#` - delegate's email address

If subject is not specified, the following value will be used:
* `#user# mail delegation to #delegate#`

`<NotifyMessageContent>` is the message, there are four ways to specify it:
* `message|textmessage|htmlmessage <String>` - Use `<String>` as the message
* `file|htmlfile <FileName> [charset <Charset>]` - Read the message from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the message from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the message from the Google Cloud Storage file `<StorageBucketObjectName>`

If `<NotifyMessageContent>`is not specified, the following value will be used:
* `#user# has granted you #delegate# access to read, delete and send mail on their behalf.`

Unless specified in `<NotifyMessageContent>`, messages are sent as plain text,
use `html` or `html true` to indicate that the message is HTML.

Use `\n` in `message <String>` to indicate a line break; no other special characters are recognized.

By default, the email is sent from the admin user identified in oauth2.txt, `gam oauth info` will show the value.
Use `from <EmailAddress>` to specify an alternate from address.
Use `mailbox <EmailAddress>` if `from <EmailAddress>` specifies a group; GAM has to login as a user to be able to send a message. 
Gam gets no indication as to the status of the message delivery; the from user will get a non-delivery receipt if the message could not be sent to the delegate.

## Create Gmail delegates
These two commands are equivalent.
```
gam <UserTypeEntity> add delegate|delegates [convertalias] <UserEntity>
        [[notify <EmailAddressList>]
            [subject <String>]
            [from <EmailAaddress>] [mailbox <EmailAddress>]
            [replyto <EmailAaddress>]
            [<NotifyMessageContent>]
        ]
gam <UserTypeEntity> delegate|delegates to [convertalias] <UserEntity>
        [[notify <EmailAddressList>]
            [subject <String>]
            [from <EmailAaddress>] [mailbox <EmailAddress>]
            [replyto <EmailAaddress>]
            [<NotifyMessageContent>]
        ]
```
### Example

To give Bob access to Fred's mailbox as a delegate:

```
gam user fred@domain.com add delegate bob@domain.com
gam user fred@domain.com delegate to bob@domain.com
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
