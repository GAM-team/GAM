# Users - Chat
- [API documentation](#api-documentation)
- [Introduction](#introduction)
- [Set up a Chat Bot](#set-up-a-chat-bot)
- [Definitions](#definitions)
- [Manage Chat Spaces](#manage-chat-spaces)
- [Display Chat Spaces](#display-chat-spaces)
- [Manage Chat Members](#manage-chat-members)
- [Display Chat Members](#display-chat-members)
- [Manage Chat Messages](#manage-chat-messages)
- [Display Chat Messages](#display-chat-messages)
- [Bulk Operations](#bulk-operations)

## API documentation
* https://developers.google.com/chat/concepts
* https://developers.google.com/chat/reference/rest
* https://support.google.com/chat/answer/7655820

## Introduction
These features were added in version 6.60.00.

To use these commands you must update your service account authorization.
```
gam user user@domain.com update serviceaccount

[*]  3)  Chat API - Memberships (supports readonly)
[*]  4)  Chat API - Messages (supports readonly)
[*]  5)  Chat API - Spaces (supports readonly)
[*]  6)  Chat API - Spaces Delete

```
Google requires that you have a Chat Bot configured in order to use the Chat API; set up a Chat Bot as described in the next section.

## Set up a Chat Bot

* Run the command `gam setup chat`; it will point you to a URL to configure your Chat Bot; this is required to use the Chat API.
* Enter an App name and Description of your choosing.
* For the Avatar URL you can use `https://dummyimage.com/384x256/4d4d4d/0011ff.png&text=+GAM` or a public URL to an image of your own choosing.
* In Functionality, uncheck both "Receive 1:1 messages" and "Join spaces and group conversations"
* In Connection settings, choose "Cloud Pub/Sub" and enter "no-topic" for the topic name. GAM doesn't yet listen to pub/sub so this option is not used.
* In Visibility, uncheck "Make this Chat app available to specific people and groups in Domain Workspace".
* Click Save.

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
* [Drive File Selection](Drive-File-Selection) for symbols not listed here, such as `<DriveFileIDEntity>`
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

<ChatContent> ::=
        ((text <String>)|
         (textfile <FileName> [charset <CharSet>])|
         (gdoc <UserGoogleDoc>)|
         (gcsdoc <StorageBucketObjectName>))

<ChatMember> ::= spaces/<String>/members/<String>
<ChatMemberList> ::= "<ChatMember>(,<ChatMember>)*"
<ChatMessage> ::= spaces/<String>/messages/<String>
<ChatSpace> ::= spaces/<String> | space <String> | space spaces/<String>
<ChatThread> ::= spaces/<String>/threads/<String>
<ChatSpaceType> ::=
        space|
	groupchat|
	directmessage
<ChatSpaceTypeList> ::= "<ChatSpaceType>(,<ChatSpaceType>)*"
<ChatMessageID> ::= client-<String>
        <String> must contain only lowercase letters, numbers, and hyphens up to 56 characters in length.
```

## Manage Chat Spaces
### Create a chat space
```
gam <UserTypeEntity> create chatspace
        [type <ChatSpaceType>]
        [externalusersrallowed <Boolean>]
        [members <UserTypeEntity>]
        [displayname <String>]
        [description <String>] [guidelines <String>]
        [history <Boolean>]
        [<ChatContent>]
        [formatjson|returnidonly]
```
For `type space`, the following apply:
* `member <UserTypeEntity>` - Optional, can not specify more that 20 users
* `displayname <String>` - Required
* `description <String>` - Optional
* `guidelines <String>` - Optional
* `history <Boolean>` - Optional

For `type groupchat`, the following apply:
* `member <UserTypeEntity>` - Required, must specify between 2 and 20 users
* `displayname <String>` - Ignored
* `description <String>` - Optional
* `guidelines <String>` - Optional
* `history <Boolean>` - Optional

For `type directmessage`, the following apply:
* `member <UserTypeEntity>` - Required, must specify 1 user
* `displayname <String>` - Ignored
* `description <String>` - Ignored
* `guidelines <String>` - Ignored
* `history <Boolean>` - Optional

By default, Gam displays the information about the created chatspace as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display the chatspace name only

Use the `<ChatContent>` option to send an initial message to the created chatspace.

By default, details about the chatmessage are displayed.
* `returnidonly` - Display the chatmessage name only

### Update a chat space
```
gam <UserTypeEntity> update chatspace <ChatSpace>
        [type space]
        [displayname <String>]
        [description <String>] [guidelines <String>]
        [history <Boolean>]
        [formatjson]
```
A groupchat space can be upgraded to a space by specifying `type space` and `displayname <String>`.

By default, Gam displays the information about the created chatspace as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Delete a chat space
```
gam <UserTypeEntity> delete chatspace <ChatSpace>
```

## Display Chat Spaces
### Display information about a specific chat space for a user
```
gam <UserTypeEntity> info chatspace <ChatSpace>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about a direct message chat space between two users
```
gam <UserTypeEntity> info chatspacedm <UserItem>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about all chat spaces for a user
```
gam <UserTypeEntity> show chatspaces
        [types <ChatSpaceTypeList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatspaces [todrive <ToDriveAttribute>*]
        [types <ChatSpaceTypeList>]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage Chat Members
### Add members to a chat space
```
gam <UserTypeEntity> create chatmember <ChatSpace>
        [type human|bot]
        ((user <UserItem>)|(members <UserTypeEntity>))*
        [formatjson|returnidonly]
```
By default, Gam displays the information about the chatmember as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display the chatmember name only

### Delete members from a chat space
Delete members by specifying a chat space and user email addresses.
```
gam <UserTypeEntity> delete chatmember <ChatSpace>
        ((user <UserItem>)|(members <UserTypeEntity>))+
```

Delete members by specifying chatmember names.
```
gam <UserTypeEntity> remove chatmember members <ChatMemberList>
```

## Display Chat Members
### Display information about a specific chat members
```
gam <UserTypeEntity> info chatmember members <ChatMemberList>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about all chat members in a chat space
```
gam <UserTypeEntity> show chatmembers <ChatSpace>
        [showinvited [<Boolean>]] [filter <String>]
        [formatjson]
```

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatmembers [todrive <ToDriveAttribute>*] <ChatSpace>
        [showinvited [<Boolean>]] [filter <String>]
        [formatjson [quotechar <Character>]]
```

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

By default, only `JOINED` members are displayed; use `showinvited` to also display `INVITED` members.

Use `filter <String>` to filter memberships by a member's `role `and `member.type`.
* To filter by role, set role to ROLE_MEMBER or ROLE_MANAGER.
* To filter by type, set member.type to HUMAN or BOT.
* To filter by both role and type, use the AND operator.
* To filter by either role or type, use the OR operator.

For example, the following queries are valid:
```
role = "ROLE_MANAGER" OR role = "ROLE_MEMBER"
member.type = "HUMAN" AND role = "ROLE_MANAGER"
```
The following queries are invalid:
```
member.type = "HUMAN" AND member.type = "BOT"
role = "ROLE_MANAGER" AND role = "ROLE_MEMBER"
```

### Delete a user from their `space` and `groupchat` spaces
There is no way to delete a user from a directmessage space.
```
gam redirect csv ./UserChatSpaces.csv user user@domain.com print chatspaces types space,groupchat
gam redirect stdout ./DeleteUserChatMemberships.txt multiprocess redirect stderr stdout csv ./UserChatSpaces.csv gam user "~User" delete chatmember "~name" user "~User"
```

## Manage Chat Messages
### Create a chat message in a space

Messages are limited to 4,096 characters and will be trimmed to that length.

Chat supports [simple formatting](https://developers.google.com/chat/reference/message-formats/basic#using_formatted_text_in_messages) allowing you to bold, underline, italics and strikethrough your text.
```
gam <UserTypeEntity> create chatmessage <ChatSpace>
        <ChatContent>
        [messageId <ChatMessageID>]
        [(thread <ChatThread>)|(threadkey <String>) [replyoption fail|fallbacktonew]]
        [returnidonly]
```
Specify the text of the message: `<ChatContent>`
* `text <String>` - The message is `<String>`
* `textfile <FileName> [charset <CharSet>]` - The message is read from a local file
* `gdoc <UserGoogleDoc>` - The message is read from a Google Doc.
* `gcsdoc <StorageBucketObjectName>` - The message is read from a Google Cloud Storage file.

By default, a new message thread is created; use `thread <ChatThread>` or `threadkey <String>` to create the message as a reply to an existing thread.
Use `replyoption` to specify what happens if the specified thread does not exist:
* `fail` - If the thread soes not exiat, a `Not Found` error is generated
* `fallbacktonew` - If the thread does not exist, start a new thread

The first time you reply to a thread you must use `thread <ChatThread>`; if you also specify `threadkey <String>`
then you can use just `threadkey <String>` in subsequent replies.

If you specify `thread` or `threadkey` but not `replyoption`, the default is `fail'.

By default, details about the chatmessage are displayed.
* `returnidonly` - Display the chatmessage name only

### Examples
This example creates a new chat message in the given room.
```
gam user user@domain.com create chatmessage space spaces/iEMj8AAAAAE text "Hello Chat"
```
This example creates a formatted message and posts it to an existing thread
```
gam user user@domain.com create chatmessage space spaces/AAAADi-pvqc thread spaces/AAAADi-pvqc/threads/FMNw-iE9jN4 text "*Bold* _Italics_ ~Strikethrough~"
```
This example reads the MotD.txt file and posts its contents to Chat.
```
gam user user@domain.com create chatmessage spaces spaces/AAAADi-pvqc textfile MotD.txt
```
This example reads the Google Doc MotD and posts its contents to Chat.
```
gam user user@domain.com create chatmessage spaces spaces/AAAADi-pvqc gdoc announcements@domain.com name "MotD"
```

### Update a Chat Message
Updates and rewrites an existing Chat message. Message will show as edited and no notification will be sent to members.
```
gam <UserTypeEntity> update chatmessage name <ChatMessage>
        <ChatContent>
```
Specify the text of the message: `<ChatContent>`
* `text <String>` - The message is `<String>`
* `textfile <FileName> [charset <CharSet>]` - The message is read from a local file
* `gdoc <UserGoogleDoc>` - The message is read from a Google Doc.
* `gcsdoc <StorageBucketObjectName>` - The message is read from a Google Cloud Storage file.

### Example
This example updates an existing chat message with new text.
```
gam user user@domain.com update chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU text "HELLO CHAT?"
```

### Delete a Chat Message
Deletes the given Chat message. Members will no longer see the message.

```
gam <UserTypeEntity> delete chatmessage name <ChatMessage>
```

### Example
```
gam user user@domain.com delete chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU
```

## Display Chat Messages
Display a specific Chat message.

```
gam <UserTypeEntity> info chatmessage name <ChatMessage>
        [filter <String>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Example
```
gam user user@domain.com info chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU
```

### Display information about all chat messages in a chat space
```
gam <UserTypeEntity> show chatmessages <ChatSpace>
        [showdeleted [<Boolean>]] [filter <String>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatmessages [todrive <ToDriveAttribute>*] <ChatSpace>
        [showdeleted [<Boolean>]] [filter <String>]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

By default, deleted messages are not displayed; use `showdeleted` to also display deleted messages.

Use `filter <String>` to filter messages by `createTime` and `thread.name`.

To filter messages by the date they were created, specify the createTime with a timestamp in RFC-3339 format and double quotation marks. For example, "2023-04-21T11:30:00-04:00".
* Use the greater than operator `>` to list messages that were created after a timestamp.
* Use the less than operator `<` to list messages that were created before a timestamp.
* To filter messages within a time interval, use the AND operator between two timestamps.
* To filter by thread, specify the thread.name, formatted as spaces/{space}/threads/{thread}. You can only specify one thread.name per query.
* To filter by both thread and date, use the AND operator in your query.

For example, the following queries are valid on Linux/MacOS:
```
filter 'createTime > "2012-04-21T11:30:00-04:00"'
filter 'createTime > "2012-04-21T11:30:00-04:00" AND thread.name = spaces/AAAAAAAAAAA/threads/123'
filter 'createTime > "2012-04-21T11:30:00+00:00" AND createTime < "2013-01-01T00:00:00+00:00" AND thread.name = spaces/AAAAAAAAAAA/threads/123'
filter 'thread.name = spaces/AAAAAAAAAAA/threads/123'
```

For example, the following queries are valid on Windows Command Prompt:
```
filter "createTime > \"2012-04-21T11:30:00-04:00\""
filter "createTime > \"2012-04-21T11:30:00-04:00\" AND thread.name = spaces/AAAAAAAAAAA/threads/123"
filter "createTime > \"2012-04-21T11:30:00+00:00\" AND createTime < \"2013-01-01T00:00:00+00:00\" AND thread.name = spaces/AAAAAAAAAAA/threads/123"
filter "thread.name = spaces/AAAAAAAAAAA/threads/123"
```

For example, the following queries are valid on Windows PowerShell:
```
filter 'createTime > \"2012-04-21T11:30:00-04:00\"'
filter 'createTime > \"2012-04-21T11:30:00-04:00\" AND thread.name = spaces/AAAAAAAAAAA/threads/123"'
filter 'createTime > \"2012-04-21T11:30:00+00:00\" AND createTime < \"2013-01-01T00:00:00+00:00\" AND thread.name = spaces/AAAAAAAAAAA/threads/123'
filter 'thread.name = spaces/AAAAAAAAAAA/threads/123'
```

## Bulk Operations
### Display information about all chat spaces for a collection of users
```
gam config auto_batch_min 1 redirect csv ./ChatSpaces.csv multiprocess [todrive <ToDriveAttribute>*] redirect stdout - multiprocess redirect stderr <UserTypeEntity> print chatspaces
        [types <ChatSpaceTypeList>]
        [formatjson [quotechar <Character>]]
```

### Display information about all chat space members of the chat spaces for a collection of users
```
gam config auto_batch_min 1 redirect csv ./ChatSpaces.csv multiprocess [todrive <ToDriveAttribute>*] redirect stdout - multiprocess redirect stderr <UserTypeEntity> print chatspaces
        [types <ChatSpaceTypeList>]
gam redirect csv ./ChatSpaceMembers.csv multiprocess [todrive <ToDriveAttribute>*] redirect stdout - multiprocess redirect stderr stdout csv ./ChatSpaces.csv gam user "~User" print chatmembers "~name"
        [showinvited [<Boolean>]] [filter <String>]
```
