- [Setup a Chat Bot](#setup-a-chat-bot)
- [Listing Rooms and Chats Your Bot Has Been Added To](#listing-rooms-and-chats-your-bot-has-been-added-to)
- [Listing Members of a Room or Chat](#listing-members-of-a-room-or-chat)
- [Creating a Chat Message](#creating-a-chat-message)
- [Updating a Chat Message](#updating-a-chat-message)
- [Deleting a Chat Message](#deleting-a-chat-message)

## Setup a Chat Bot
Since GAM 6.03, GAM is capable of acting as a Chat Bot and sending messages to Chat Rooms or direct messages to users. You first need to configure your Chat Bot.

1. Run the command ```gam create chatmessage space q9lgEgAAAAE text "Hello Google Chat"``` to attempt to create your first chat message. It will fail and point you to a URL to configure your Chat Bot.
2. Enter a name and description of your choosing. For the avatar URL you can use `https://dummyimage.com/384x256/4d4d4d/0011ff.png&text=+GAM` or a public URL to an image of your own choosing.
3. In the Functionality section, check off both "Bot works in direct messages" and "Bot works in rooms and direct messages with multiple users"
4. For Connection Settings, choose "Cloud Pub/Sub" and enter "no-topic" for the topic name. GAM doesn't yet listen to pub/sub so this option is not used.
5. Configure permissions for who your bot can chat. The recommendation is everyone in your domain.
6. Save changes.
7. Now you are ready to start chatting.

----

## Listing Rooms and Chats Your Bot Has Been Added To

### Syntax

```
gam print chatspaces [todrive]
```

Prints the spaces a Chat Bot is able to send messages to. A space can be a direct message to a user, a chat group or a chat room. At first you'll have no spaces listed. Try [finding your bot and chatting it](https://support.google.com/chat/answer/7655820) and then your space will be listed with the above.

----

## Listing Members of a Room or Chat

### Syntax

```
gam print chatmembers space <space> [todrive]
```

prints the members of a given Chat space.

----

## Creating a Chat Message

### Syntax

```
gam create chatmessage [text <message text>] [textfile <file>] space <space> [thread <thread id>]
```

Creates a chat message in the given space. You must specify either text and the text of your message or textfile and the path to a file where the text can be read. Messages are limited to 4,096 characters and will be trimmed to that length. Chat supports [simple formatting](https://developers.google.com/chat/reference/message-formats/basic#using_formatted_text_in_messages) allowing you to bold, underline, italics and strikethrough your text.

### Example
This example creates a new chat message in the given room.
```
gam create chatmessage text "Hello Chat" space spaces/iEMj8AAAAAE
```
This example creates a formatted message and posts it to an existing thread
```
gam create chatmessage text "*Bold* _Italics_ ~Strikethrough~" thread spaces/AAAADi-pvqc/threads/FMNw-iE9jN4 space spaces/AAAADi-pvqc
```
This example reads the MotD.txt file and posts it's contents to Chat.
```
gam create chatmessage textfile MotD.txt spaces spaces/AAAADi-pvqc
```
----

## Updating a Chat Message
### Syntax
```
gam update chatmessage name <name> [text <chat text>] [textfile <file>]
```
Updates and rewrites an existing Chat message. Message will show as edited and no notification will be sent to members.

### Example
This example updates an existing chat message with new text.
```
gam update chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU text "HELLO CHAT?"
```
----

## Deleting a Chat Message
### Syntax
```
gam delete chatmessage name <name>
```
Deletes the given Chat message. Members will no longer see the message.

### Example
```
gam delete chatmessage name spaces/AAAADi-pvqc/messages/PKJrx90ooIU.PKJrx90ooIU
```
----