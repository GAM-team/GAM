# Users - Chat
- [Introduction](#introduction)
- [Set up a Chat Bot](#set-up-a-chat-bot)
- [API documentation](#api-documentation)
- [Query Documentation](#query-documentation)
- [Definitions](#definitions)
- [Chat Space Permissions](#chat-space-permissions)
- [Manage Chat Spaces](#manage-chat-spaces)
- [Display Chat Spaces](#display-chat-spaces)
- [Manage Chat Members](#manage-chat-members)
- [Display Chat Members](#display-chat-members)
- [Manage Chat Messages](#manage-chat-messages)
- [Display Chat Messages](#display-chat-messages)
- [Display Chat Events](#display-chat-events)
- [Bulk Operations](#bulk-operations)

## Introduction
These features were added in version 6.60.00.

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

* Run the command `gam setup chat`; it will point you to a URL to configure your Chat Bot; this is required to use the Chat API.
* Enter an App name and Description of your choosing.
* For the Avatar URL you can use `https://dummyimage.com/384x256/4d4d4d/0011ff.png&text=+GAM` or a public URL to an image of your own choosing.
* In Functionality, uncheck both "Receive 1:1 messages" and "Join spaces and group conversations"
* In Connection settings, choose "Cloud Pub/Sub" and enter "no-topic" for the topic name. GAM doesn't yet listen to pub/sub so this option is not used.
* In Visibility, uncheck "Make this Chat app available to specific people and groups in Domain Workspace".
* Click Save.

## API documentation
* [Overview](https://developers.google.com/workspace/chat/overview)
* [Chat API](https://developers.google.com/workspace/chat/api/reference/rest)
* [Chat API - Members](https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.members/list)
* [Chat API - Messages](https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.messages/list)
* [Chat API - Events](https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.spaceEvents/list)
* [Apps in Google Chat](https://support.google.com/chat/answer/7655820)
* [Manage Spaces in Admin Console](https://support.google.com/a/answer/13369245)
* [Predefined permission settings](https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces#Space.FIELDS.predefined_permission_settings)

## Query documentation
* [Search Spaces](https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search)

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
         (textfile <FileName> [charset <Charset>])|
         (gdoc <UserGoogleDoc>)|
         (gcsdoc <StorageBucketObjectName>))

<ChatEvent> ::= spaces/<String>/spaceEvents/<String>
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
        permissionsettings|
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

## Chat Space Permissions
### Announcement
| Keyword | Description | Allowed | Default |
|---------|-------------|---------|---------|
| manageapps | Manage apps | managers-immutable | managers |
| managemembersandgroups | Manage members and groups | managers/members | managers |
| managewebhooks | Manage web hooks | managers-immutable | managers |
| modifyspacedetails | Modify space details | managers/members | managers |
| postmessages | Post messages | managers-immutable | managers |
| replymessages | Reply messages | members/managers | members |
| togglehistory | Turn history on and off | managers/members | managers |
| useatmentionall | Use @all | managers-immutable | managers |

### Collaboration
| Keyword | Description | Allowed | Default |
|---------|-------------|---------|---------|
| manageapps | Manage apps | members-immutable | members |
| managemembersandgroups | Manage members and groups | managers/members | members |
| managewebhooks | Manage web hooks | managers/members | members |
| modifyspacedetails | Modify space details | managers/members | members |
| postmessages | Post messages | members-immutable | members |
| replymessages | Reply messages | members-immutable | members |
| togglehistory | Turn history on and off | managers/members | members |
| useatmentionall | Use @all | managers/members | members |

## Manage Chat Spaces
### Create a chat space
```
gam <UserTypeEntity> create chatspace
        [type <ChatSpaceType>] [announcement|collaboration]
        [restricted|(audience <String>)]
        [externalusersallowed <Boolean>]
        [members <UserTypeEntity>]
        [displayname <String>]
        [description <String>] [guidelines <String>]
        [history <Boolean>]
        [<ChatContent>]
        [formatjson|returnidonly]
```
For `type space`, the following apply:
* `members <UserTypeEntity>` - Optional, can not specify more that 20 users
* `displayname <String>` - Required
* `description <String>` - Optional
* `guidelines <String>` - Optional
* `history <Boolean>` - Optional
* `announcement|collaboration` - Initial permission settings; default is `collaboration`; this is in Developer Preview

For `type groupchat`, the following apply:
* `members <UserTypeEntity>` - Required, must specify between 2 and 20 users
* `displayname <String>` - Ignored
* `description <String>` - Optional
* `guidelines <String>` - Optional
* `history <Boolean>` - Optional

For `type directmessage`, the following apply:
* `members <UserTypeEntity>` - Required, must specify 1 user
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

### Update a user's chat space
```
gam <UserTypeEntity> update chatspace <ChatSpace>
        [restricted|(audience <String>)]|
        ([displayname <String>]
         [type space]
         [description <String>] [guidelines|rules <String>]
         [history <Boolean>])
        [managemembersandgroups managers|members]
        [modifyspacedetails managers|members]
        [togglehistory managers|members]
        [useatmentionall managers|members]
        [manageapps managers|members]
        [managewebhooks managers|members]
        [replymessages managers|members]
        [formatjson]
```
A groupchat space can be upgraded to a space by specifying `type space` and `displayname <String>`.

The `restricted|audience` options can not be combined with options `displayname,type,description,guidelines,history`.

You can manage permissions for chat spaces with the following options that are available with Developer Preview.
        [managemembersandgroups managers|members]
        [modifyspacedetails managers|members]
        [togglehistory managers|members]
        [useatmentionall managers|members]
        [manageapps managers|members]
        [managewebhooks managers|members]
        [postmessages managers|members]
        [replymessages managers|members]


By default, Gam displays the information about the created chatspace as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Update a chat space, asadmin
```
gam <UserItem> update chatspace asadmin <ChatSpace>
        [restricted|(audience <String>)]|
        ([displayname <String>]
         [type space]
         [description <String>] [guidelines|rules <String>]
         [history <Boolean>])
        [formatjson]
```
A groupchat space can be upgraded to a space by specifying `type space` and `displayname <String>`.

The `restricted|audience` options can not be combined with options `displayname,type,description,guidelines,history`.

By default, Gam displays the information about the created chatspace as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Delete a user's chat space
```
gam <UserTypeEntity> delete chatspace <ChatSpace>
```

### Delete a chat space, asadmin
```
gam <UserItem> delete chatspace asadmin <ChatSpace>
```

## Display Chat Spaces
### Display information about a specific chat space for a user
```
gam <UserTypeEntity> info chatspace <ChatSpace>
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about a direct message chat space between two users
```
gam <UserTypeEntity> info chatspacedm <UserItem>
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about all chat spaces for a user
```
gam <UserTypeEntity> show chatspaces
        [types <ChatSpaceTypeList>]
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, chat spaces of all types are displayed.
* `types <ChatSpaceTypeList>` - Display specific types of spaces.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatspaces [todrive <ToDriveAttribute>*]
        [types <ChatSpaceTypeList>]
        [fields <ChatSpaceFieldNameList>]
        [formatjson [quotechar <Character>]]
```
By default, chat spaces of all types are displayed.
* `types <ChatSpaceTypeList>` - Display specific types of spaces.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Display information about all user's chat spaces
```
# Local file
gam config auto_batch_min 1 redirect csv ./AllChatSpaces.csv multiprocess redirect stdout - multiprocess redirect stderr stdout all users print chatspaces
# Google sheet
gam config auto_batch_min 1 redirect csv - todrive <ToDriveAttribute>* multiprocess redirect stdout - multiprocess redirect stderr stdout all users print chatspaces
```
Add these options as desired:
```
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

### Display information about a specific chat space, asadmin
```
gam <UserItem> info chatspace asadmin <ChatSpace>
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about all chat spaces, asadmin
For query and orderby information, see: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search

Only spaces of `<ChatSpaceType>` `space` are displayed; spaces of `<ChatSpaceType>` `groupchat` and `directmessage` are not displayed.
```
gam <UserItem> show chatspaces asadmin
        [query <String>] [querytime<String> <Time>]
        [orderby <ChatSpaceAdminOrderByFieldName> [ascending|descending]]
        [fields <ChatSpaceFieldNameList>]
        [formatjson]
```
By default, all chat spaces of type SPACE are displayed.
* `query <String> [querytime<String> <Time>]` - Display selected chat spaces
  * See: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserItem> print chatspaces asadmin [todrive <ToDriveAttribute>*]
        [query <String>] [querytime<String> <Time>]
        [orderby <ChatSpaceAdminOrderByFieldName> [ascending|descending]]
        [fields <ChatSpaceFieldNameList>]
        [formatjson [quotechar <Character>]]
```
By default, all chat spaces of type SPACE are displayed.
* `query <String> [querytime<String> <Time>]` - Display selected chat spaces
  * See: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage Chat Members
### Add members to a user's chat space
```
gam <UserTypeEntity> create chatmember <ChatSpace>
        [type human|bot] [role member|manager]
        (user <UserItem>)* (members <UserTypeEntity>)*
        (group <GroupItem>)* (groups <GroupEntity>)*
        [formatjson|returnidonly]
```
By default, Gam displays the information about the chatmember as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display the chatmember name only

### Delete members from a user's chat space
Delete members by specifying a chat space and user/group email addresses.
```
gam <UserTypeEntity> delete chatmember <ChatSpace>
        ((user <UserItem>)|(members <UserTypeEntity>)|
         (group <GroupItem>)|(groups <GroupEntity>))+
```

Delete members from a user's chat space by specifying chatmember names.
```
gam <UserTypeEntity> remove chatmember members <ChatMemberList>
```

### Add members to a chat space, asadmin
Creating memberships for users outside the administrator's Google Workspace organization isn't supported using asadmin.
```
gam <UserItem> create chatmember asadmin <ChatSpace>
        [type human|bot] [role member|manager]
        (user <UserItem>)* (members <UserTypeEntity>)*
        (group <GroupItem>)* (groups <GroupEntity>)*
        [formatjson|returnidonly]
```
By default, Gam displays the information about the chatmember as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display the chatmember name only

### Delete members from a chat space, asadmin
Delete members by specifying a chat space and user/group email addresses.
```
gam <UserItem> delete chatmember asadmin <ChatSpace>
        ((user <UserItem>)|(members <UserTypeEntity>)|
         (group <GroupItem>)|(groups <GroupEntity>))+
```

Delete members from a chat space by specifying chatmember names, asadmin
```
gam <UserItem> remove chatmember members asadmin <ChatMemberList>
```

### Update a members role in a user's chat space
Update members by specifying a chat space, user/group email addresses and role.
```
gam <UserTypeEntity> update chatmember <ChatSpace>
        role member|manager
        ((user <UserItem>)|(members <UserTypeEntity>))+
```
Update members by specifying chatmember names and role.
```
gam <UserTypeEntity> modify chatmember
        role member|manager
        members <ChatMemberList>
```

### Update a members role in a chat space, asadmin
Update members by specifying a chat space, user/group email addresses and role.
```
gam <UserItem> update chatmember asadmin <ChatSpace>
        role member|manager
        ((user <UserItem>)|(members <UserTypeEntity>))+
```
Update members by specifying chatmember names and role.
```
gam <UserItem> modify chatmember asadmin
        role member|manager
        members <ChatMemberList>
```

## Display Chat Members
### Display information about a user's specific chat members
```
gam <UserTypeEntity> info chatmember members <ChatMemberList>
        [fields <ChatMemberFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about members in a user's chat spaces
```
gam <UserTypeEntity> show chatmembers
        <ChatSpace>* [types <ChatSpaceTypeList>]
        [showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
        [fields <ChatMemberFieldNameList>]
        [formatjson]
```

By default, members for all of a user's chat spaces of all types are displayed.
* `<ChatSpace>` - Display members for a specific chat space
* `types <ChatSpaceTypeList>` - Display members for specific types of spaces.

By default, all JOINED user members in a chat space are displayed.
* `showinvited` - Display `INVITED` members.
* `showgroups` - Display group members,
* `filter <String>` - Filter memberships by a member's `role `and `member.type`.
  * To filter by role, set role to ROLE_MEMBER or ROLE_MANAGER.
  * To filter by type, set member.type to HUMAN or BOT.
  * To filter by both role and type, use the AND operator.
  * To filter by either role or type, use the OR operator.

For example, the following filters are valid:
```
role = "ROLE_MANAGER" OR role = "ROLE_MEMBER"
member.type = "HUMAN" AND role = "ROLE_MANAGER"
```
The following filters are invalid:
```
member.type = "HUMAN" AND member.type = "BOT"
role = "ROLE_MANAGER" AND role = "ROLE_MEMBER"
```

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatmembers [todrive <ToDriveAttribute>*]
        <ChatSpace>* [types <ChatSpaceTypeList>]
        [showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
        [fields <ChatMemberFieldNameList>]
        [formatjson [quotechar <Character>]]
```

By default, members for all of a user's chat spaces of all types are displayed.
* `<ChatSpace>` - Display members for a specific chat space
* `types <ChatSpaceTypeList>` - Display members for specific types of spaces.

By default, all JOINED user members in a chat space are displayed.
* `showinvited` - Display `INVITED` members.
* `showgroups` - Display group members,
* `filter <String>` - Filter memberships by a member's `role `and `member.type`.
  * To filter by role, set role to ROLE_MEMBER or ROLE_MANAGER.
  * To filter by type, set member.type to HUMAN or BOT.
  * To filter by both role and type, use the AND operator.
  * To filter by either role or type, use the OR operator.

For example, the following filters are valid:
```
role = "ROLE_MANAGER" OR role = "ROLE_MEMBER"
member.type = "HUMAN" AND role = "ROLE_MANAGER"
```
The following filters are invalid:
```
member.type = "HUMAN" AND member.type = "BOT"
role = "ROLE_MANAGER" AND role = "ROLE_MEMBER"
```

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Display information about specific chat members, asadmin
```
gam <UserItem> info chatmember asadmin members <ChatMemberList>
        [fields <ChatMemberFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about members all chat spaces, asadmin
For query and orderby information, see: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search
```
gam <UserItem> show chatmembers asadmin
        <ChatSpace>*  [query <String>] [querytime<String> <Time>]
        [showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
        [fields <ChatMemberFieldNameList>]
        [formatjson]
```

By default, members for all chat spaces of type SPACE are displayed.
* `<ChatSpace>` - Display members for a specific chat space
* `query <String> [querytime<String> <Time>]` - Display members for selected chat spaces
  * See: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search

By default, all JOINED user members in a chat space are displayed.
* `showinvited` - Display `INVITED` members.
* `showgroups` - Display group members,
* `filter <String>` - Filter memberships by a member's `role `and `member.type`.
  * To filter by role, set role to ROLE_MEMBER or ROLE_MANAGER.
  * To filter by type, set member.type to HUMAN or BOT.
  * To filter by both role and type, use the AND operator.
  * To filter by either role or type, use the OR operator.

For example, the following filters are valid:
```
role = "ROLE_MANAGER" OR role = "ROLE_MEMBER"
member.type = "HUMAN" AND role = "ROLE_MANAGER"
```
The following filters are invalid:
```
member.type = "HUMAN" AND member.type = "BOT"
role = "ROLE_MANAGER" AND role = "ROLE_MEMBER"
```

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserItem> print chatmembers asadmin  [todrive <ToDriveAttribute>*]
        <ChatSpace>*  [query <String>] [querytime<String> <Time>]
        [showinvited [<Boolean>]] [showgroups [<Boolean>]] [filter <String>]
        [fields <ChatMemberFieldNameList>]
        [formatjson [quotechar <Character>]]
```

By default, members for all chat spaces of type SPACE are displayed.
* `<ChatSpace>` - Display members for a specific chat space
* `query <String> [querytime<String> <Time>]` - Display members for selected chat spaces
  * See: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces/search

By default, all JOINED user members in a chat space are displayed.
* `showinvited` - Display `INVITED` members.
* `showgroups` - Display group members,
* `filter <String>` - Filter memberships by a member's `role `and `member.type`.
  * To filter by role, set role to ROLE_MEMBER or ROLE_MANAGER.
  * To filter by type, set member.type to HUMAN or BOT.
  * To filter by both role and type, use the AND operator.
  * To filter by either role or type, use the OR operator.

For example, the following filters are valid:
```
role = "ROLE_MANAGER" OR role = "ROLE_MEMBER"
member.type = "HUMAN" AND role = "ROLE_MANAGER"
```
The following filters are invalid:
```
member.type = "HUMAN" AND member.type = "BOT"
role = "ROLE_MANAGER" AND role = "ROLE_MEMBER"
```

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Delete a user from their `space` and `groupchat` spaces
There is no way to delete a user from a directmessage space.

Replace user@domain.com and admin@domain.com with actual values.
```
gam redirect csv ./UserChatSpaces.csv user user@domain.com print chatspaces types space,groupchat
gam redirect stdout ./DeleteUserChatMemberships.txt multiprocess redirect stderr stdout csv ./UserChatSpaces.csv gam user admin@domain.com delete chatmember asadmin "~name" user "~User"
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
* `textfile <FileName> [charset <Charset>]` - The message is read from a local file
* `gdoc <UserGoogleDoc>` - The message is read from a Google Doc.
* `gcsdoc <StorageBucketObjectName>` - The message is read from a Google Cloud Storage file.

By default, a new message thread is created; use `thread <ChatThread>` or `threadkey <String>` to create the message as a reply to an existing thread.
Use `replyoption` to specify what happens if the specified thread does not exist:
* `fail` - If the thread soes not exiat, a `Not Found` error is generated
* `fallbacktonew` - If the thread does not exist, start a new thread

The first time you reply to a thread you must use `thread <ChatThread>`; if you also specify `threadkey <String>`
then you can use just `threadkey <String>` in subsequent replies.

If you specify `thread` or `threadkey` but not `replyoption`, the default is `fail`.

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
* `textfile <FileName> [charset <Charset>]` - The message is read from a local file
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
        [fields <ChatMessageFieldNameList>]
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
gam <UserTypeEntity> show chatmessages
        <ChatSpace>+
        [showdeleted [<Boolean>]] [filter <String>]
        [fields <ChatMessageFieldNameList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatmessages [todrive <ToDriveAttribute>*]
        <ChatSpace>+
        [showdeleted [<Boolean>]] [filter <String>]
        [fields <ChatMessageFieldNameList>]
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

## Display Chat Events
Display a specific Chat event.

```
gam <UserTypeEntity> info chatevent name <ChatEvent>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Example
```
gam user user@domain.com info chatevent name spaces/AAAAsUhqjkg/spaceEvents/MTcxMTY4ODM2NDE3OTQzOV81X3VwZGF0ZWQ
```

### Display information about all chat events in a chat space
```
gam <UserTypeEntity> show chatevents
        <ChatSpace>+
        filter <String>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print chatevents [todrive <ToDriveAttribute>*]
        <ChatSpace>+
        filter <String>
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

Use `filter <String>` to filter events by when they occurred and by the type of event.

To filter events by the date they happened, specify the start_time and end_time with a timestamp in RFC-3339 format and double quotation marks.

You must specify at least one event type (event_types) using the has : operator. To filter by multiple event types, use the OR operator.
For a list of supported event types, see: https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.spaceEvents#SpaceEvent.FIELDS.event_type

For example, the following queries are valid on Linux/MacOS:
```
filter 'start_time="2024-03-15T11:30:00-04:00" AND event_types:"google.workspace.chat.message.v1.created"'
filter 'start_time="2024-03-15T11:30:00+00:00" AND end_time="2024-03-3100:00:00+00:00"event_types:"google.workspace.chat.message.v1.created"'
```

For example, the following queries are valid on Windows Command Prompt:
```
filter "start_time=\"2024-03-15T11:30:00-04:00\" AND event_types:\"google.workspace.chat.message.v1.created\""
filter "start_time=\"2024-03-15T11:30:00+00:00\" AND end_time=\"2024-03-3100:00:00+00:00\" AND event_types:\"google.workspace.chat.message.v1.created\""
```

For example, the following queries are valid on Windows PowerShell:
```
filter 'start_time=\"2024-03-15T11:30:00-04:00\" AND event_types:\"google.workspace.chat.message.v1.created\"'
filter 'start_time=\"2024-03-15T11:30:00+00:00\" AND end_time=\"2024-03-3100:00:00+00:00\" AND event_types:\"google.workspace.chat.message.v1.created\"'
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
