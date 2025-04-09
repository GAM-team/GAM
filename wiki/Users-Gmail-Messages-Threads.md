# Users - Gmail - Messages/Threads
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [Subject and label queries](#subject-and-label-queries)
- [Draft messages](#draft-messages)
- [Import messages](#import-messages)
- [Insert messages](#insert-messages)
- [Archive messages](#archive-messages)
- [Export messages/threads](#export-messagesthreads)
- [Forward messages/threads](#forward-messagesthreads)
- [Manage messages/threads](#manage-messagesthreads)
- [Delete messages by Message-Id](#delete-messages-by-message-id)
- [Display messages/threads](#display-messagesthreads)
  - [Display all messages](#display-all-messages)
  - [Display a specific set of messages](#display-a-specific-set-of-messages)
  - [Display a selected set of messages](#display-a-selected-set-of-messages)
  - [Choose information to display](#choose-information-to-display)
    - [Display message content](#display-message-content)
    - [Display message counts](#display-message-counts)
    - [Display label counts](#display-label-counts)
  - [Print only options](#print-only-options)
  - [Show only options](#show-only-options)
  - [Download attachments](#download-attachments)
  - [Upload attachments](#upload-attachments)
  - [Display messages sent by delegates for delegator](#display-messages-sent-by-delegates-for-delegator)
- [User attribute `replace <Tag> <UserReplacement>` processing](Tag-Replace)

## Notes
* [Restrict email messages to authorized addresses or domains only](https://support.google.com/a/answer/2640542)
* [Block emails between specific user groups](https://support.google.com/a/answer/9175444)

## API documentation
* [Gmail API - Messages](https://developers.google.com/gmail/api/v1/reference/users.messages)
* [Gmail API - Threads](https://developers.google.com/gmail/api/v1/reference/users.threads)
* [Gmail API - Drafts](https://developers.google.com/gmail/api/v1/reference/users.drafts)
* [Gmail API - Import](https://developers.google.com/gmail/api/v1/reference/users.messages/import)
* [Gmail API - Insert](https://developers.google.com/gmail/api/v1/reference/users.messages/insert)
* [Groups Migration API - Archive](https://developers.google.com/admin-sdk/groups-migration/v1/reference/archive/insert)

## Query documentation
* [Search Messages](https://support.google.com/mail/answer/7190)

The document above shows the following  queries in the left column;
they don't work, use the query in the right column.

| Fails | Works |
|-------|-------|
| has:yellow-star | l:^ss_sy |
| has:blue-star | l:^ss_sb |
| has:red-star | l:^ss_sr |
| has:orange-star | l:^ss_so |
| has:green-star | l:^ss_sg |
| has:purple-star | l:^ss_sp |
| has:red-bang | l:^ss_cr |
| has:yellow-bang | l:^ss_cy |
| has:blue-info | l:^ss_cb |
| has:orange-guillemet | l:^ss_co |
| has:green-check | l:^ss_cg |
| has:purple-question | l:^ss_cp |

This table and other suggestions came from:
* https://www.planetahuevo.es/uso-de-gmail-avanzado-saca-partido-a-tu-gmail/

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<LabelName> ::= <String>
<QueryGmail> ::= <String> See: https://support.google.com/mail/answer/7190
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

<SMTPDateHeader> ::=
        date|
        delivery-date|
        expires|
        expiry-date|
        latest-delivery-time|
        reply-by|
        resent-date
<SMTPHeader> ::=
        accept-language|
        alternate-recipient|
        autoforwarded|
        autosubmitted|
        bcc|
        cc|
        comments|
        content-alternative|
        content-base|
        content-description|
        content-disposition|
        content-duration|
        content-id|
        content-identifier|
        content-language|
        content-location|
        content-md5|
        content-return|
        content-transfer-encoding|
        content-type|
        content-features|
        conversion|
        conversion-with-loss|
        dl-expansion-history|
        deferred-delivery|
        delivered-to|
        discarded-x400-ipms-extensions|
        discarded-x400-mts-extensions|
        disclose-recipients|
        disposition-notification-options|
        disposition-notification-to|
        encoding|
        encrypted|
        from|
        generate-delivery-report|
        importance|
        in-reply-to|
        incomplete-copy|
        keywords|
        language|
        list-archive|
        list-help|
        list-id|
        list-owner|
        list-post|
        list-subscribe|
        list-unsubscribe|
        mime-version|
        message-context|
        message-id|
        message-type|
        obsoletes|
        original-encoded-information-types|
        original-message-id|
        originator-return-address|
        pics-label|
        prevent-nondelivery-report|
        priority|
        received|
        references|
        reply-to|
        resent-bcc|
        resent-cc|
        resent-from|
        resent-message-id|
        resent-reply-to|
        resent-sender|
        resent-to|
        return-path|
        sender|
        sensitivity|
        subject|
        supersedes|
        to|
        x400-content-identifier|
        x400-content-return|
        x400-content-type|
        x400-mts-identifier|
        x400-originator|
        x400-received|
        x400-recipients|
        x400-trace
<SMTPHeaderList> ::= "<SMTPDateHeader|SMTPHeader>(,<SMTPDateHeader|SMTPHeader>)*"

<MessageID> ::= <String>
<MessageIDList> ::= "<MessageID>(,<MessageID>)*"
<MessageIDEntity> ::=
        <MessageIDList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<ThreadID> ::= <String>
<ThreadIDList> ::= "<ThreadID>(,<ThreadID>)*"
<ThreadIDEntity> ::= <ThreadIDList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>

<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>

<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)

<MessageContent> ::=
        (message|textmessage|htmlmessage <String>)|
        (file|textfile|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)|
        (emlfile <FileName> [charset <Charset>]))

<DriveFolderID> ::= <String>
<DriveFolderName> ::= <String>
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>

<DriveFileParentAttribute> ::=
        (parentid <DriveFolderID>)|
        (parentname <DriveFolderName>)|
        (anyownerparentname <DriveFolderName>)|
        (teamdriveparentid <DriveFolderID>)|
        (teamdriveparent <SharedDriveName>)|
        (teamdriveparentid <SharedDriveID> teamdriveparentname <DriveFolderName>)|
        (teamdriveparent <SharedDriveName> teamdriveparentname <DriveFolderName>)
```
## Message queries with dates
```
query <QueryGmail> [querytime<String> <Date>]*
```
* `query "xxx"` - ` xxx` is appended to the current query; you can repeat the query argument to build up a longer query.

Use the `querytime<String> <Date>` option to allow dates, usually relative, to be substituted into the `query <QueryGmail>` option.
The `querytime<String> <Date>` value replaces the string `#querytime<String>#` in any queries.
The characters following `querytime` can be any combination of lowercase letters and numbers. This is most useful in scripts
where you can specify a relative date without having to change the script.

For example, query for messages from moree than 5 years ago:
```
querytime5years -5y query "before:#querytime5years#"
```

## Subject and label queries
Using a query to select messages by subject or label requires some attention in order to achieve the desired effect.
* https://support.google.com/mail/answer/7190

To select messages with all of the words (`word1`, `word2` and `word3`) in the subject, regardless of location or order, use:
* `query "subject:word1 word2 word3"`

To select messages with exactly (`word1 word2 word3`) in the subject, use:
* `query "subject:\"word1 word2 word3\""`

To select messages with a label containing `&()"|{}/`, you have to replace these characters with `-` in the query.
You can also replace ` ` with `-` but it doesn't seem to be required.

* `query "label:Foo -Bar-"` - Select messages with label `Foo (Bar)`

You can have GAM do the substitutions for you with the `matchlabel <LabelName>` option.
* `matchlabel "Foo (Bar)"` is converted to `query "label:Foo -Bar-"`

## Draft messages
Add a draft message to a user's mailbox.
```
gam <UserTypeEntity> draft message
        <MessageContent>
        (replace <Tag> <UserReplacement>)*
        (replaceregex <RESearchPattern> <RESubstitution> <Tag> <UserReplacement>)*
        (<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
        (attach <FileName> [charset <Charset>])*
        (embedimage <FileName> <String>)*
```
`<MessageContent>` is the message, there are five ways to specify it:
* `message|textmessage|htmlmessage <String>` - Use `<String>` as the message
* `file|htmlfile <FileName> [charset <Charset>]` - Read the message from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the message from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the message from the Google Cloud Storage file `<StorageBucketObjectName>`
* `emlfile <FileName> [charset <Charset>]` - Read the message from the EML message file `<FileName>`. SMTP headers specified in the command will replace those in the message file. The default `charset` is `ascii`.

The `<SMTPDateHeader> <Time>` argument  requires `<Time>` values which will be converted to RFC2822 dates. If you have these headers with values that
are not in `<Time>` format, use the argument `header <SMTPDateHeader> <String>`.

If you have an SMTP header that is not found in `<SMTPDateHeader>` or `<SMTPHeader>`, use `header <String> <String>`.

The `<SMTPHeader>` value `content-type` is not valid for these commands; it will be derived from other arguments.

You can embed images in HTML email messages.

Your HTML message will contain lines like this:
```
<img src="cid:image1"/>
<img src="cid:image2"/>
```

Your command line will have: `embedimage file1.jpg image1 embedimage file2.jpg image2`

## Import messages
Import a message into a user's mailbox, with standard email delivery scanning and classification similar to receiving via SMTP.
```
gam <UserTypeEntity> import message
        <MessageContent>
        (replace <Tag> <UserReplacement>)*
        (replaceregex <RESearchPattern> <RESubstitution> <Tag> <UserReplacement>)*
        (<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
        (addlabel <LabelName>)* [labels <LabelNameList>]
        (attach <FileName> [charset <Charset>])*
        (embedimage <FileName> <String>)*
        [deleted [<Boolean>]] [checkspam [<Boolean>]] [processforcalendar [<Boolean>]]
```

`<MessageContent>` is the message, there are five ways to specify it:
* `message|textmessage|htmlmessage <String>` - Use `<String>` as the message
* `file|htmlfile <FileName> [charset <Charset>]` - Read the message from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the message from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the message from the Google Cloud Storage file `<StorageBucketObjectName>`
* `emlfile <FileName> [charset <Charset>]` - Read the message from the EML message file `<FileName>`. SMTP headers specified in the command will replace those in the message. The default `chatser` is `ascii`.

When `emlfile` is not specified:
* If `to` is not specified, it is set to the user email addresses in `<UserTypeEntity>`.
* If `from` is not specified, it is set to the admin user identified in oauth2.txt.

The `<SMTPDateHeader> <Time>` argument  requires `<Time>` values which will be converted to RFC2822 dates. If you have these headers with values that
are not in `<Time>` format, use the argument `header <SMTPDateHeader> <String>`.

If you have an SMTP header that is not found in `<SMTPDateHeader>` or `<SMTPHeader>`, use `header <String> <String>`.

The `<SMTPHeader>` value `content-type` is not valid for these commands; it will be derived from other arguments.

If no `addlabel <LabelName>` is specified, the message will be placed in the Inbox.

You can embed images in HTML email messages.

Your HTML message will contain lines like this:
```
<img src="cid:image1"/>
<img src="cid:image2"/>
```

Your command line will have: `embedimage file1.jpg image1` embedimage file2.jpg image2`

`deleted` defaults to False, when True: Mark the email as permanently deleted (not TRASH) and only visible in Google Vault to a Vault administrator.

`checkspam` defaults to False: Ignore the Gmail spam classifier decision and never mark this email as SPAM in the mailbox.

`processforcalendar` defaults to False, when True: Process calendar invites in the email and add any extracted meetings to the Google Calendar for this user.

## Insert messages
Insert a message into a user's mailbox similar to IMAP APPEND, bypassing most scanning and classification.
```
gam <UserTypeEntity> insert message
        <MessageContent>
        (replace <Tag> <UserReplacement>)*
        (replaceregex <RESearchPattern> <RESubstitution> <Tag> <UserReplacement>)*
        (<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
        (addlabel <LabelName>)* [labels <LabelNameList>]
        (attach <FileName> [charset <Charset>])*
        (embedimage <FileName> <String>)*
        [deleted [<Boolean>]]
```

`<MessageContent>` is the message, there are five ways to specify it:
* `message|textmessage|htmlmessage <String>` - Use `<String>` as the message
* `file|htmlfile <FileName> [charset <Charset>]` - Read the message from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the message from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the message from the Google Cloud Storage file `<StorageBucketObjectName>`
* `emlfile <FileName> [charset <Charset>]` - Read the message from the EML message file `<FileName>`. SMTP headers specified in the command will replace those in the message file. The default `chatser` is `ascii`.

When `emlfile` is not specified:
* If `to` is not specified, it is set to the user email addresses in `<UserTypeEntity>`.
* If `from` is not specified, it is set to the admin user identified in oauth2.txt.

The `<SMTPDateHeader> <Time>` argument  requires `<Time>` values which will be converted to RFC2822 dates. If you have these headers with values that
are not in `<Time>` format, use the argument `header <SMTPDateHeader> <String>`.

If you have an SMTP header that is not found in `<SMTPDateHeader>` or `<SMTPHeader>`, use `header <String> <String>`.

The `<SMTPHeader>` value `content-type` is not valid for these commands; it will be derived from other arguments.

If no `addlabel <LabelName>` is specified, the message will be placed in the Inbox.

You can embed images in HTML email messages.

Your HTML message will contain lines like this:
```
<img src="cid:image1"/>
<img src="cid:image2"/>
```

Your command line will have: `embedimage file1.jpg image1` embedimage file2.jpg image2`

`deleted` defaults to False, when True: Mark the email as permanently deleted (not TRASH) and only visible in Google Vault to a Vault administrator.

## Archive messages
```
gam <UserTypeEntity> archive messages <GroupItem>
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_archive <Number>])|(ids <MessageIDEntity>)
        [csv [todrive <ToDriveAttribute>*]]
```

Messages are archived to the group specified by `<GroupItem>`.

### Archive  a specific set of messages
* `ids <MessageIDEntity>` - A list of message ids

### Archive a selected set of messages
* `((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+` - Criteria to select messages
* `max_to_archive` - Limit the number of messages that will be archived; use a value of 0 for no limit
* `doit` - No messages are archived unless you specify `doit`. By not specifying `doit`, you can preview the messages selected to verify that the results match your expectations.

When `matchlabel <LabelName>` is specified, the following characters are replaced with a `-` in the generated query.
```
 &()"|{}/
```

By default, Gam fetches all matching messages from Google and then processes only `max_to_archive` of them.
To speed up fetching, specify `quick` and only `max_to_archive` of the matching messages will be fetched.
You must still specify `doit` to perform the operation.

By default, the command results are displayed as indented keys and values. Use the `csv` option
to display the command results in CSV form.
```
$ gam user user@domain.com archive messages ids 18e9fc6581b9acab,18e9fc58c5491f4c    
User: user@domain.com, Archive 2 Messages
  User: user@domain.com, Message: 18e9fc6581b9acab, Archived (1/2)
  User: user@domain.com, Message: 18e9fc58c5491f4c, Archived (2/2)
$ gam user user@domain.com archive messages ids 18e9fc6581b9acab,18e9fc58c5491f4c csv
User: user@domain.com, Archive 2 Messages
User,id,action,error
user@domain.com,18e9fc6581b9acab,Archived,
user@domain.com,18e9fc58c5491f4c,Archived,
```

See below for message selection.

## Export messages/threads
Export messages in EML format.
```
gam <UserTypeEntity> export message|messages
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [max_to_export <Number>])|(ids <MessageIDEntity>)
        [targetfolder <FilePath>] [targetname <FileName>] [overwrite [<Boolean>]]
gam <UserTypeEntity> export thread|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+ [quick|notquick] [max_to_export <Number>])|(ids <ThreadIDEntity>)
        [targetfolder <FilePath>] [targetname <FileName>] [overwrite [<Boolean>]]
```

By default, when exporting a message, it is downloaded to the directory specified in `gam.cfg/drive_dir`.
* `targetfolder <FilePath>` - Specify an alternate location for the downloaded file.

By default, when exporting a message, the local name is `Msg-<MessageID>`.
* `targetname <FileName>` - Specify an alternate name for the downloaded file; `#id#` will be replaced by `<MessageID>`.

The strings `#email#`, `#user#` and `#username#` will be replaced by the the user's full email address or just the name portion
in `targetfolder <FilePath>` and `targetname <FileName>`.

By default, when exporting a message, an existing local file will not be overwritten; a numeric prefix is added to the filename.
* `overwrite` - Overwite an existing file
* `overwrite true` - Overwite an existing file
* `overwrite false` - Do not overwite an existing file; add a numeric prefix and create a new file

See below for message selection.

## Forward messages/threads
```
gam <UserTypeEntity> forward message|messages recipient|to <RecipientEntity>
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_forward <Number>])|(ids <MessageIDEntity>)
         [subject <String>] [addorigfieldstosubject]
gam <UserTypeEntity> forward thread|threads recipient|to <RecipientEntity>
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_forward <Number>])|(ids <ThreadIDEntity>)
         [subject <String>] [addorigfieldstosubject]
```

By default, the message subject has `Fwd: ` prepended; use `subject <String>` to specify a new subject.

All `Cc` addresses are removed from the forwarded message.

If `addorigfieldstosubject` is specified, GAM appends the original `from`, `to` and `date` fields to the message subject.
```
Fwd: Ross to TestUser (Original From: Ross Scroggs <ross.scroggs@gmail.com> To: testuser@domain.com Date: Thu, 23 Nov 2023 07:01:59 -0800)
```

See below for message selection.

## Manage messages/threads
```
gam <UserTypeEntity> delete messages|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_delete <Number>])|(ids <MessageIDEntity>)
        [csv [todrive <ToDriveAttribute>*]]
gam <UserTypeEntity> modify messages|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_modify <Number>])|(ids <MessageIDEntity>)
        ((addlabel <LabelName>)|(removelabel <LabelName>))+
        [csv [todrive <ToDriveAttribute>*]]
gam <UserTypeEntity> spam messages|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_spam <Number>])|(ids <MessageIDEntity>)
        [csv [todrive <ToDriveAttribute>*]]
gam <UserTypeEntity> trash messages|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_trash <Number>])|(ids <MessageIDEntity>)
        [csv [todrive <ToDriveAttribute>*]]
gam <UserTypeEntity> untrash messages|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+
         [quick|notquick] [doit] [max_to_untrash <Number>])|(ids <MessageIDEntity>)
        [csv [todrive <ToDriveAttribute>*]]
```

By default, the command results are displayed as indented keys and values. Use the `csv` option
to display the command results in CSV form.
```
$ gam user user@domain.com delete messages ids 18e9fc6581b9acab,18e9fc58c5491f4c    
User: user@domain.com, Delete 2 Messages
  User: user@domain.com, Message: 18e9fc6581b9acab, Deleted (1/2)
  User: user@domain.com, Message: 18e9fc58c5491f4c, Deleted (2/2)
$ gam user user@domain.com delete messages ids 18e9fc6581b9acab,18e9fc58c5491f4c csv
User: user@domain.com, Delete 2 Messages
User,id,action,error
user@domain.com,18e9fc6581b9acab,Deleted,
user@domain.com,18e9fc58c5491f4c,Deleted,
```

### Manage a specific set of messages
* `ids <MessageIDEntity>` - A list of message ids

### Manage a selected set of messages
* `((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+` - Criteria to select messages
* `max_to_xxx` - Limit the number of messages that will be processed; use a value of 0 for no limit
* `doit` - No messages are processed unless you specify `doit`. By not specifying `doit`, you can preview the messages selected to verify that the results match your expectations.

When `matchlabel <LabelName>` is specified, the following characters are replaced with a `-` in the generated query.
```
 &()"|{}/
```

By default, Gam fetches all matching messages from Google and then processes only `max_to_process` of them.
To speed up fetching, specify `quick` and only `max_to_process` of the matching messages will be fetched.
You must still specify `doit` to perform the operation.

## Delete messages by Message-Id
Sometimes multiple users in your domain receive an inappropriate message that you'd like to delete.
From any user that received the message (or the one that sent it), you have to obtain the Message-Id. That looks like this:
```
Message-Id: <B1A91373-49E1-4235-8290-3E991E998A76@domain.com>
```

If you know Bob Smith sent the message or is someone you know received it and the subject is "New org chart next year", you can quickly find it like this:

```
gam user bob.smith@yourdomain.com print messages query "\"New org chart next year\"" headers subject,to,message-id
```

This will print a list of messages that match; by looking at the addressees, you can select which message ID(s) are relevant.

To delete the message for all users:
```
gam config auto_batch_min 1 all users delete message query "rfc822msgid:<B1A91373-49E1-4235-8290-3E991E998A76@domain.com>" doit
```

If your domain has many users, this process might still take a while. You can target a subset of users, for instance by Org unit or group. Refer to [Collections of Users](https://github.com/GAM-team/GAM/wiki/Collections-of-Users) for all available options. For example, to target all users in the Org unit Sales:

```
gam config auto_batch_min 1 ou_and_children Sales delete message query "rfc822msgid:<B1A91373-49E1-4235-8290-3E991E998A76@domain.com>" doit
```

Or all users in the EastOffice group, including subgroups:

```
gam config auto_batch_min 1 groups_inde EastOffice delete message query "rfc822msgid:<B1A91373-49E1-4235-8290-3E991E998A76@domain.com>" doit
```

## Display messages/threads
```
gam <UserTypeEntity> show messages|threads
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
         [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <MessageIDEntity>)
        [labelmatchpattern <REMatchPattern>] [sendermatchpattern <REMatchPattern>]
        [countsonly|positivecountsonly] [useronly]
        [headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
        [showlabels] [delimiter <Character>] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
        [maxmessagesperthread <Number>]
        [showattachments [attachmentnamepattern <REMatchPattern>>] [noshowtextplain]]
        [saveattachments [attachmentnamepattern <REMatchPattern>>]]
            [targetfolder <FilePath>] [overwrite [<Boolean>]]
gam <UserTypeEntity> print messages|threads [todrive <ToDriveAttribute>*]
        (((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
         [quick|notquick] [max_to_print <Number>] [includespamtrash])|(ids <MessageIDEntity>)
        [labelmatchpattern <REMatchPattern>] [sendermatchpattern <REMatchPattern>]
        [countsonly|positivecountsonly] [useronly]
        [headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
        [showlabels] [delimiter <Character>] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
        [maxmessagesperthread <Number>]
        [showattachments [attachmentnamepattern <REMatchPattern>>]]
        [convertcrnl]
```
## Display all messages
By default, Gam displays all messages.
* `max_to_xxx` - Limit the number of messages that will be displayed
* `includespamtrash` - Include messages in the Spam and Trash folders

By default, all messages in a thread are displayed with `print|show threads`.
Use `maxmessagesperthread <Number>` to limit the number of messages displayed for a thread.
For example, this can be used if you only want to see the first message of each thread.
```
gam user user@domain.com print|show threads maxmessagesperthread 1
```

## Display a specific set of messages
* `ids <MessageIDEntity>` - A list of message ids

## Display a selected set of messages
* `((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])+` - Criteria to select messages
* `max_to_xxx` - Limit the number of messages that will be displayed
* `includespamtrash` - Include messages in the Spam and Trash folders
* `labelmatchpattern <REMatchPattern>` - Only display messages with some label that matches `<REMatchPattern>`
  * `labelmatchpattern xyz` - Label must start with xyz
  * `labelmatchpattern .*xyz.*` - Label must contain xyz
  * `labelmatchpattern .*xyz` - Label must end with xyz
  * `labelmatchpattern ^xyz$` - Label must extctly match xyz
* `sendermatchpattern <REMatchPattern>` - Only display messages if the sender matches the `<REMatchPattern>`

When `matchlabel <LabelName>` is specified, the following characters are replaced with a `-` in the generated query.
```
 &()"|{}/
```

By default, Gam fetches only `max_to_process` matching messages from Google and then displays them.
To see how many messages actually match, specify `notquick` and all matching messages will be fetched; only `max_to_process` of them will be displayed.

### Difference between `From` and `Sender` headers
The `From` header specifies the author of the message, that is,
the mailbox of the person or system responsible for the writing of the message.
The `Sender` header specifies the mailbox of the agent responsible
for the actual transmission of the message.  For example, if a secretary were to send
a message for another person, the mailbox of the secretary would appear in the
`Sender` header and the mailbox of the actual author would appear in the `From` header.

The Gmail API supports querying the `From` header, but not the `Sender` header;
thus, you must use `sendermatchpattern <REMatchPattern>` to query this header.

## Choose information to display
By default, the fields `User, threadId, id` and these SMTP headers are displayed: `Date, Subject, From, Reply-To, To, Delivered-To, Content-Type, Message-ID`.
Use these options to customize the display.

By default, the `<SMTPDateHeader>` values are displayed in RFC2822 format; the `dateheaderformat iso|rfc2822|<String>` option allows reformatting it:
* `iso` - Format is `%Y-%m-%dT%H:%M:%S%:z`
* `rfc2822` - Format is `%a, %d %b %Y %H:%M:%S %z`
* `<String>` - Format according to: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
If the `Date` header value can't be parsed as RFC2822, it is left unchanged.

The `dateheaderconverttimezone [<Boolean>]>` option converts `<SMTPDateHeader>` values to the `gam.cfg timezone`.

### Display message content
* `headers all` - Display all SMTP headers
* `headers <SMTPHeaderList>` - Display only the SMTP headers listed
* `showbody` - Display the message body
* `showhtml` - When used in conjunction with `showbody`, display the message body if it is of type `text/html`
* `showdate` - Display the message `internalDate`
* `showlabels` - Display the message labels and count
  * `useronly` - Do not display system labels
  * `delimiter <Character>` - Separate the list of labels with `<Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.
* `showsize` - Display the message size
* `showsnippet` - Display the message snippet

### Display message counts
* `countsonly` - Display the count of the number of messages
* `showsize` - Display the cumulative message size

### Display label counts
* `showlabels` - Display the message labels
* `countsonly` - Display all message label counts
* `positivecountsonly` - Display message label counts that are greater than 0
* `showsize` - Display the cumulative message size for each label
* `useronly` - Do not display system labels

## Print only options
These options are valid with `print`.
* `convertcrnl` - In the message body, convert carriage returns to `\r` and newlines to `\n`; the default value is `csv_output_convert_cr_nl` from `gam.cfg`.

By default, message attachment information is not displayed.
* `showattachments` - Display attachment filename, MIME type and size
* `attachmentnamepattern <REMatchPattern>>` - Limit the attachments shown to those whose names match `<REMatchPattern>`

## Show only options
These options are valid with `show`.

By default, message attachment information is not displayed.
* `showattachments` - Display message attachment content for MIME type text/plain, display filename, MIME type and size for other MIME types
  * `noshowtextplain` - Do not display message attachment content for MIME type text/plain, just display its filename, MIME type and size
* `attachmentnamepattern <REMatchPattern>>` - Limit the attachments shown to those whose names match `<REMatchPattern>`

## Download attachments
These options are valid with `show`.

By default, message attachments are not downloaded.
* `saveattachments` - Download message attachments
* `attachmentnamepattern <REMatchPattern>>` - Limit the attachments downloaded to those whose names match `<REMatchPattern>`

By default, message attachments are downloaded to the directory specified in `gam.cfg/drive_dir`.
* `targetfolder <FilePath>` - Specify an alternate location for the downloaded attachments

The strings `#email#`, `#user#` and `#username#` will be replaced by the the user's full emailaddress or just the name portion
in `targetfolder <FilePath>`.

By default, when downloading attachments, an existing local file will not be overwritten; a numeric prefix is added to the filename.
* `overwrite` - Overwite an existing file
* `overwrite true` - Overwite an existing file
* `overwrite false` - Do not overwite an existing file; add a numeric prefix and create a new file

## Upload attachments
These options are valid with `show`.

By default, message attachments are not uploaded to Google Drive.
* `uploadattachments` - Upload message attachments
* `attachmentnamepattern <REMatchPattern>>` - Limit the attachments uploaded to those whose names match `<REMatchPattern>`

By default, message attachments are uploaded to the root of the user's My Drive.
* `<DriveFileParentAttributeh>` - Specify an alternate location for the uploaded attachments

## Display messages sent by delegates for delegator
Display messages sent by a particular delegate for a delegator; the message is
from the delegator but sent by the delegate.
```
$ gam user delegator show messages query "in:sent" sendermatchpattern delegate1@domain.com headers from,to,sender
Getting all Messages for delegator@domain.com
Got 24 Messages...
User: delegator@domain.com, Show maximum of 24 Messages of 24 Total Messages
  Message: 17a63d9f459cb9be (2/24)
    From: Test Simple <delegator@domain.com>
    To: ross.scroggs@gmail.com
    Sender: delegate1@domain.com

$ gam user delegator show messages query "in:sent" sendermatchpattern delegate2@domain.com headers from,to,sender
Getting all Messages for delegator@domain.com
Got 24 Messages...
User: delegator@domain.com, Show maximum of 24 Messages of 24 Total Messages
  Message: 17a63dc2cb14ed1e (1/24)
    From: Test Simple <delegator@domain.com>
    To: ross.scroggs@gmail.com
    Sender: delegate2@domain.com

$ gam user delegator show messages query "in:sent" sendermatchpattern "delegate.*@domain.com" headers from,to,sender
Getting all Messages for delegator@domain.com
Got 24 Messages...
User: delegator@domain.com, Show maximum of 24 Messages of 24 Total Messages
  Message: 17a63dc2cb14ed1e (1/24)
    From: Test Simple <delegator@domain.com>
    To: ross.scroggs@gmail.com
    Sender: delegate2@domain.com
  Message: 17a63d9f459cb9be (2/24)
    From: Test Simple <delegator@domain.com>
    To: ross.scroggs@gmail.com
    Sender: delegate1@domain.com
```

Display number of messages sent by delegates for a delegator; only delegates
that sent messages will be displayed.
```
$ gam csv ./SentByDelegates.csv user delegator print messages query "in:sent" sendermatchpattern ".+" countsonly 
Getting all Messages for delegator@domain.com
Got 24 Messages...
$ more SentByDelegates.csv
User,Sender,messages
delegator@domain.com,delegate1@domain.com,1
delegator@domain.com,delegate2@domain.com,1
```
