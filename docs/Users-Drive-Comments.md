# Users - Drive - Comments
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Definitions](#definitions)
- [Display file comments](#display-file-comments)

## API documentation
* https://developers.google.com/drive/api/v3/reference/comments

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
        replies.action|
        replies.author|
        replies.author.<CommentsAuthorSubfieldName>|
        replies.content|
        replies.createddate|createdtime|
        replies.deleted|
        replies.htmlcontent|
        replies.id|
        replies.modifieddate|modifiedtime

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
        replies|
        resolved
<CommentsFieldNameList> ::= "<CommentsFieldName>(,<CommentsFieldName>)*"
```

## Display file comments
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> show filecomments <DriveFileEntity>
        [showdeleted] [start <Date>|<Time>]
        [fields <CommentsFieldNameList>] [showphotolinks]
	[countsonly]
        [formatjson]
```
By default, all non-deleted comments for a file are displayed; use these options to modify that behavior.
* `showdeleted` - Display deleted comments
* `start <Date>|<Time>` - Display comments modified on or after `<Date>|<Time>`

By default, all comment and reply fields except author photolinks are displayed; use these options to modify that behavior.
* `fields <CommentsFieldNameList>` - Select fields to display
* `showphotolinks` - Display author photolinks
* `countsonly` - Display just the number of comments and replies; no fields

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
Each comment/reply pair is output on a separate CSV file row.
```
gam <UserTypeEntity> print filecomments <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [showdeleted] [start <Date>|<Time>] [countsonly]
        [fields <CommentsFieldNameList>] [showphotolinks]
        (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
By default, all non-deleted comments for a file are displayed; use these options to modify that behavior.
Files with no comments will not be displayed.
* `showdeleted` - Display deleted comments
* `start <Date>|<Time>` - Display comments modified on or after `<Date>|<Time>`

By default, all comment and reply fields except author photolinks are displayed; use these options to modify that behavior.
* `fields <CommentsFieldNameList>` - Select fields to display
* `showphotolinks` - Display author photolinks
* `countsonly` - Display just the number of comments and replies; no fields. Files with no comments will display zero counts.

Add additional columns of data from the command line to the output:
* `addcsvdata <FieldName> <String>`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
