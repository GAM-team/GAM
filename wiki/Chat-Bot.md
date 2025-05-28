# Chat Bot
- [Introduction](#introduction)
- [Set up a Chat Bot](#set-up-a-chat-bot)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Display Rooms and Chats to which your Bot belongs](#display-rooms-and-chats-to-which-your-bot-belongs)
- [Display Members of a Room or Chat](#display-members-of-a-room-or-chat)
- [Create a Chat Message](#create-a-chat-message)
- [Update a Chat Message](#update-a-chat-message)
- [Delete a Chat Message](#delete-a-chat-message)
- [Display a Chat Message](#display-a-chat-message)

## Introduction
To use these commands you must update your service account authorization.
```
gam user user@domain.com update serviceaccount

[*]  4)  Chat API - Memberships (supports readonly)
[*]  5)  Chat API - Memberships Admin (supports readonly)
[*]  6)  Chat API - Messages (supports readonly)
[*]  7)  Chat API - Spaces (supports readonly)
[*]  8)  Chat API - Spaces Admin (supports readonly)
[*]  9)  Chat API - Spaces Delete
[*] 10)  Chat API - Spaces Delete Admin
```

Added `use_chat_admin_access` Boolean variable to `gam.cfg`. 
```
* When False, GAM uses user access when making all Chat API calls. For calls that support admin access,
    this can be overridden with the asadmin command line option.
* When True, GAM uses admin access for Chat API calls that support admin access; other calls will use user access.
* Default: False
```

Google requires that you have a Chat Bot configured in order to use the Chat API; set up a Chat Bot as described in the next section.

## Set up a Chat Bot
GAM is capable of acting as a Chat Bot and sending messages to Chat Rooms or direct messages to users.

Even if you're not going to use GAM as a Chat Bot, you have to configure a Chat Bot as it is required by the Chat API in [Users - Chat](Users-Chat).

* Run the command `gam setup chat`; it will point you to a URL to configure your Chat Bot.
* Enter an App name and Description of your choosing.
* For the Avatar URL you can use `https://dummyimage.com/384x256/4d4d4d/0011ff.png&text=+GAM` or a public URL to an image of your own choosing.
* In Functionality, uncheck both "Receive 1:1 messages" and "Join spaces and group conversations"
* In Connection settings, choose "Cloud Pub/Sub" and enter `projects/<ProjectID>/topics/no-topic` for the Topic Name. Replace `<ProjectID>` with your GAM project ID. GAM doesn't yet listen to pub/sub so this option is not used.
* In Visibility, uncheck "Make this Chat app available to specific people and groups in Domain Workspace".
* Click Save.

## API documentation
* https://developers.google.com/chat/concepts
* https://developers.google.com/chat/reference/rest
* https://support.google.com/chat/answer/7655820

## Definitions
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
         (textfile <FileName> [charset <Charset>])|
         (gdoc <UserGoogleDoc>)|
         (gcsdoc <StorageBucketObjectName>))

<ChatMember> ::= spaces/<String>/members/<String>
<ChatMessage> ::= spaces/<String>/messages/<String>
<ChatSpace> ::= spaces/<String> | space <String> | space spaces/<String>
<ChatThread> ::= spaces/<String>/threads/<String>
<ChatMessageID> ::= client-<String>
        <String> must contain only lowercase letters, numbers, and hyphens up to 56 characters in length.
```
```
<ChatSpaceFieldName> ::=
        accesssettings|
        admininstalled|
        createtime|
        displayname|
        externaluserallowed|
        importmode|
        lastactivetime|
        membershipcount|
        name|
        singleuserbotdm|
        spacedetails|
        spacehistorystate|
        spacethreadingstate|threaded|
        spacetype|type|
        spaceuri
<ChatSpaceFieldNameList> ::= "<ChatSpaceFieldName>(,<ChatSpaceFieldName>)*"

<ChatMemberFieldName> ::=
        createtime|
        deletetime|
        groupmember|
        member|
        name|
        role|
        state|
<ChatMemberFieldNameList> ::= "<ChatMemberFieldName>(,<ChatMemberFieldName>)*"

<ChatMessageFieldName> ::=
        accessorywidgets|
        actionresponse|
        annotations|
        argumenttext|
        attachedgifs|
        attachment|
        cards|
        cardsv2|
        clientassignedmessageid|
        createtime|
        deletetime|
        deletionmetadata|
        emojireactionsummaries|
        fallbacktext|
        formattedtext|
        lastupdatetime|
        matchedurl|
        name|
        privatemessageviewer|
        quotedmessagemetadata|
        sender|
        slashcommand|
        space|
        text|
        thread|
        threadreply
<ChatMessageFieldNameList> ::= "<ChatMessageFieldName>(,<ChatMessageFieldName>)*"
```

## Display Rooms and Chats to which your Bot belongs
Display the spaces to which your Chat Bot can send messages.
A space can be a direct message to a user, a chat group or a chat room.
At first you'll have no spaces listed. Try [finding your bot and chatting it](https://support.google.com/chat/answer/7655820) and then your space will be listed.

### Display information about a specific chat space
```
gam info chatspace space <ChatSpace>
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about all chat spaces
```
gam show chatspaces
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chatspaces [todrive <ToDriveAttribute>*]
        [fields <ChatSpaceFieldNameList>]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.
`
By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

----

## Display Members of a Room or Chat
### Display information about a specific chat member
```
gam info chatmember member <ChatMember>
        [fields <ChatMemberFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about all chat members in a chat space
```
gam show chatmembers space <ChatSpace>
        [showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
        [fields <ChatMemberFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chatmembers [todrive <ToDriveAttribute>*] space <ChatSpace>
        [showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
        [fields <ChatMemberFieldNameList>]
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

Use `filter <String>` to filter memberships by a member's role and membertype.
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

## Create a Chat Message
Create a chat message in a space. Messages are limited to 4,096 characters and will be trimmed to that length.

Chat supports [simple formatting](https://developers.google.com/chat/reference/message-formats/basic#using_formatted_text_in_messages) allowing you to bold, underline, italics and strikethrough your text.
```
gam create chatmessage space <ChatSpace>
        <ChatContent>
        [messageId <ChatMessageID>]
        [(thread <ChatThread>)|(threadkey <String>) [replyoption fail|fallbacktonew]]
        [returnidonly]
```
Specify the text of the message: `<ChatContent>`
* `text <String>` - The message is `<String>`
* `textfile <FileName> [charset <Charset>]` - The message is read from a local file
* `gdoc <UserGoogleDoc>` - The message is read from a Google Doc.
* `gcsdoc <StorageBucketObjectName>` - The message is read from a Google Cloud Storage file.

By default, a new message thread is created; use `thread <ChatThread>` or `threadkey <String>` to create the message as a reply to an existing thread.
Use `replyoption` to specify what happens if the specified thread does not exist:
* `fail` - If the thread soes not exiat, a `Not Found` error is generated
* `fallbacktonew` - If the thread does not exist, start a new thread

The first time you reply to a thread you must use `thread <ChatThread>`; if you also specify `threadkey <String>`
then you can use just `threadkey <String>` in subsequent replies.

If you specify `thread` or `threadkey` but not `replyoption`, the default is `fail'.

By default, details about the chat message are displayed.
* `returnidonly` - Display the chat message name only

### Examples
This example creates a new chat message in the given room.
```
gam create chatmessage space spaces/iEMj8AAAAAE text "Hello Chat"
```
This example creates a formatted message and posts it to an existing thread
```
gam create chatmessage space spaces/AAAADi-pvqc thread spaces/AAAADi-pvqc/threads/FMNw-iE9jN4 text "*Bold* _Italics_ ~Strikethrough~"
```
This example reads the MotD.txt file and posts its contents to Chat.
```
gam create chatmessage spaces spaces/AAAADi-pvqc textfile MotD.txt
```
This example reads the Google Doc MotD and posts its contents to Chat.
```
gam create chatmessage spaces spaces/AAAADi-pvqc gdoc announcements@domain.com name "MotD"
```

----

## Update a Chat Message
Updates and rewrites an existing Chat message. Message will show as edited and no notification will be sent to members.
```
gam update chatmessage name <ChatMessage>
        <ChatContent>
```
Specify the source of the message:
* `text <String>` - The message is `<String>`
* `textfile <FileName> [charset <Charset>]` - The message is read from a local file
* `gdoc <UserGoogleDoc>` - The message is read from a Google Doc.
* `gcsdoc <StorageBucketObjectName>` - The message is read from a Google Cloud Storage file.

### Example
This example updates an existing chat message with new text.
```
gam update chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU text "HELLO CHAT?"
```

----

## Delete a Chat Message
Deletes the given Chat message. Members will no longer see the message.

```
gam delete chatmessage name <ChatMessage>
```

### Example
```
gam delete chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU
```

----

## Display a Chat Message
Display the given Chat message.

```
gam info chatmessage name <ChatMessage>
        [fields <ChatMessageFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Example
```
gam info chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU
```

----
