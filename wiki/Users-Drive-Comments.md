# Users - Drive - Comments
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Definitions](#definitions)
- [Display file comments](#display-file-comments)

## API documentation
* [Drive API - Comments](https://developers.google.com/drive/api/v3/reference/comments)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<CommentsAuthorSubfieldName> ::=
        author.displayname|
        author.emailaddress|
        author.me|
        author.permissionid|
        author.photolink

<CommentsRepliesSubfieldName> ::=
        reply.action|
        reply.author|
        reply.author.<CommentsAuthorSubfieldName>|
        reply.content|
        reply.createddate|createdtime|
        reply.deleted|
        reply.htmlcontent|
        reply.id|
        reply.modifieddate|modifiedtime

<CommentsFieldName> ::=
        action|
        author|
        content|
        <CommentsAuthorSubfieldName>|
        <CommentsRepliesSubfieldName>|
        createddate|createdtime|
        deleted|
        htmlcontent|
        id|
        modifieddate|modifiedtime|
        quotedfilecontent|
        reply|replies|
        resolved
<CommentsFieldNameList> ::= "<CommentsFieldName>(,<CommentsFieldName>)*"
```

## Display file comments
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> show filecomments <DriveFileEntity>
        [showdeleted] [start <Date>|<Time>]
        [fields <CommentsFieldNameList>] [showphotolinks]
	[countsonly|positivecountsonly]
        [formatjson]
```
Use `my_commentable_items` for `<DriveFileEntity>` to query only for files that can have comments.

By default, all non-deleted comments for a file are displayed; use these options to modify that behavior.
* `showdeleted` - Display deleted comments
* `start <Date>|<Time>` - Display comments modified on or after `<Date>|<Time>`

By default, all comment and reply fields except author photolinks are displayed; use these options to modify that behavior.
* `fields <CommentsFieldNameList>` - Select fields to display
* `showphotolinks` - Display author photolinks
* `countsonly` - Display just the number of comments and replies; no fields
* `positivecountsonly` - Display just the number of comments and replies only for files that have comments; no fields

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
Each comment/reply pair is output on a separate CSV file row.
```
gam <UserTypeEntity> print filecomments <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [showdeleted] [start <Date>|<Time>] [countsonly|positivecountsonly]
        [fields <CommentsFieldNameList>] [showphotolinks]
        (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
Use `my_commentable_items` for `<DriveFileEntity>` to query only for files that can have comments.

By default, all non-deleted comments for a file are displayed; use these options to modify that behavior.
Files with no comments will not be displayed.
* `showdeleted` - Display deleted comments
* `start <Date>|<Time>` - Display comments modified on or after `<Date>|<Time>`

By default, all comment and reply fields except author photolinks are displayed; use these options to modify that behavior.
* `fields <CommentsFieldNameList>` - Select fields to display
* `showphotolinks` - Display author photolinks
* `countsonly` - Display just the number of comments and replies; no fields. Files with no comments will display zero counts.
* `positivecountsonly` - Display just the number of comments and replies only for files that have comments; no fields

Add additional columns of data from the command line to the output:
* `addcsvdata <FieldName> <String>`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Example
```
# Get files that may have comments
$ gam redirect csv ./CheckForComments.csv user testsimple@domain.com print filelist showmimetype gdoc,gpresentation,gsheet fields id,name,mimetype
Getting all Drive Files/Folders that match query ('me' in owners and (mimeType = 'application/vnd.google-apps.presentation' or mimeType = 'application/vnd.google-apps.spreadsheet' or mimeType = 'application/vnd.google-apps.document')) for testsimple@domain.com
Got 131 Drive Files/Folders that matched query ('me' in owners and (mimeType = 'application/vnd.google-apps.presentation' or mimeType = 'application/vnd.google-apps.spreadsheet' or mimeType = 'application/vnd.google-apps.document')) for testsimple@domain.com...

# Display file comments
$ gam redirect csv ./FilesWithComments.csv multiprocess csv CheckForComments.csv gam user "~Owner" print filecomments "~id" addcsvdata fileName "~name" addcsvdata mimeType "~mimeType" fields author.displayName,author.me,content,createdTime,deleted,modifiedTime,resolved,reply.author.displayName,reply.author.me,reply.content,reply.createdTime,reply.deleted,reply.modifiedTime
2024-03-24T08:04:46.235-07:00,0/131,Using 10 processes...
2024-03-24T08:04:58.122-07:00,0,Processing item 100/131
2024-03-24T08:05:01.345-07:00,0,Processing item 131/131
2024-03-24T08:07:11.731-07:00,0/131,Processing complete

$ more FilesWithCommnts.csv
User,fileId,fileName,mimeType,commentId,replyId,author.displayName,author.me,content,createdTime,deleted,modifiedTime,resolved,reply.author.displayName,reply.author.me,reply.content,reply.createdTime,reply.deleted,reply.modifiedTime
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwm0,,Test-Simple,True,XXX Comment,2024-03-14T11:34:39-07:00,False,2024-03-14T11:34:39-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwkw,,Test-Simple,True,Grack Comment,2024-03-14T11:26:30-07:00,False,2024-03-14T11:26:30-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwkY,,Test-Simple,True,Again commnt,2024-03-14T11:24:13-07:00,False,2024-03-14T11:24:13-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwkQ,,Test-Simple,True,More Comment,2024-03-14T11:23:48-07:00,False,2024-03-14T11:23:48-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwkA,,Test-Simple,True,Comment 8,2024-03-14T11:23:14-07:00,False,2024-03-14T11:34:01-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwj4,,Test-Simple,True,Comment 7,2024-03-14T11:23:05-07:00,False,2024-03-14T11:23:05-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwj0,,Test-Simple,True,Comment 6,2024-03-14T11:22:55-07:00,False,2024-03-14T11:22:55-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwjs,,Test-Simple,True,Comment 5,2024-03-14T11:22:38-07:00,False,2024-03-14T11:22:38-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedwjo,,Test-Simple,True,Comment 4,2024-03-14T11:22:19-07:00,False,2024-03-14T11:22:19-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedtKQ,,Test-Simple,True,End Comment,2024-03-14T10:32:16-07:00,False,2024-03-14T10:32:16-07:00,False,,,,,,
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedtKI,AAABJFedwik,Test-Simple,True,My first comment,2024-03-14T10:32:03-07:00,False,2024-03-14T11:15:05-07:00,False,Test-Simple,True,My first reply,2024-03-14T11:14:13-07:00,False,2024-03-14T11:14:13-07:00
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,AAABJFedtKI,AAABJFedwiw,Test-Simple,True,My first comment,2024-03-14T10:32:03-07:00,False,2024-03-14T11:15:05-07:00,False,Test-Simple,True,Yet another reply,2024-03-14T11:15:05-07:00,False,2024-03-14T11:15:05-07:00
testsimple@domain.com,yyy,TS Sheet,application/vnd.google-apps.spreadsheet,AAABJM6zbc0,,Test-Simple,True,Sheet Comment,2024-03-14T20:43:18-07:00,False,2024-03-14T20:43:18-07:00,False,,,,,,
testsimple@domain.com,zzz,TS Pres,application/vnd.google-apps.presentation,AAABJLy5DpA,,Test-Simple,True,Presentation Comment,2024-03-14T20:42:48-07:00,False,2024-03-14T20:42:48-07:00,False,,,,,,

$ gam redirect csv ./FilesWithComments.csv multiprocess csv CheckForComments.csv gam user "~Owner" print filecomments "~id" addcsvdata fileName "~name" addcsvdata mimeType "~mimeType" fields author.displayName,author.me,content,createdTime,deleted,modifiedTime,resolved,reply.author.displayName,reply.author.me,reply.content,reply.createdTime,reply.deleted,,reply.modifiedTime
2024-03-24T08:04:46.235-07:00,0/131,Using 10 processes...
2024-03-24T08:04:58.122-07:00,0,Processing item 100/131
2024-03-24T08:05:01.345-07:00,0,Processing item 131/131
2024-03-24T08:07:11.731-07:00,0/131,Processing complete


# Display file comment counts
$ gam redirect csv ./FileCommentCounts.csv multiprocess csv CheckForComments.csv gam user "~Owner" print filecomments "~id" addcsvdata fileName "~name" addcsvdata mimeType "~mimeType" countsonly
2024-03-24T07:51:16.881-07:00,0/131,Using 10 processes...
2024-03-24T07:51:28.909-07:00,0,Processing item 100/131
2024-03-24T07:51:32.241-07:00,0,Processing item 131/131
2024-03-24T07:51:37.404-07:00,0/131,Processing complete

$ more FileCommentCounts.csv
User,fileId,fileName,mimeType,comments,replies
...
testsimple@domain.com,yyy,TS Sheet,application/vnd.google-apps.spreadsheet,1,0
testsimple@domain.com,aaa,ViewTest,application/vnd.google-apps.document,0,0
testsimple@domain.com,xxx,TS Doc,application/vnd.google-apps.document,11,2
testsimple@domain.com,zzz,TS Pres,application/vnd.google-apps.presentation,1,0
...
```