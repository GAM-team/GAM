# Users - Drive - Revisions
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Definitions](#definitions)
- [Delete file revisions](#delete-file-revisions)
- [Manage file revisions publishing](#manage-file-revisions-publishing)
- [Display file revisions](#display-file-revisions)

## API documentation
* [Drive API - Revisions](https://developers.google.com/drive/api/v3/reference/revisions)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<DriveFileRevisionID> ::= <String>
<DriveFileRevisionIDList> ::= "<DriveFileRevisionID>(,<DriveFileRevisionID>)*"
<DriveFileRevisionIDEntity> ::=
        (<DriveFileRevisionID>)|
        (id <DriveFileRevisionID>)|(id:<DriveFileRevisionID>)|
        (ids <DriveFileRevisionIDList>)|(ids:<DriveFileRevisionIDList>)|
        (first|last|allexceptfirst|allexceptlast <Number>)|
        (before|after <Time>)|(range <Time> <Time>)

<RevisionsFieldName> ::=
        filesize|
        id|
        keepforever|
        lastmodifyinguser|
        lastmodifyingusername|
        md5checksum|
        mimetype|
        modifieddate|
        modifiedtime|
        originalfilename|
        pinned|
        publishauto|
        published|
        publishedoutsidedomain|
        size
<RevisionsFieldNameList> ::= "<RevisionsFieldName>(,<RevisionsFieldName>)*"
```
`<DriveFileRevisionIDEntity>` can select specific revisions by ID or can select revisions by position in the list or by modification date.
* `first <Number>` - process the first `<Number>` revisions.
* `last <Number>` - process the last `<Number>` revisions.
* `allexceptfirst <Number>` - process all revisions except the first `<Number>` revisions.
* `allexceptlast <Number>` - process all revisions except the last `<Number>` revisions.
* `before <Time>` - process all revisions with a modification date before `<Time>`.
* `after <Time>` - process all revisions with a modification date equal to or after `<Time>`.
* `range <Time> <Time>` - process all revisions with a modification date equal to or after the first `<Time>` and before the second `<Time>`.

## Delete file revisions
```
gam <UserTypeEntity> delete filerevisions <DriveFileEntity> select <DriveFileRevisionIDEntity>
        [previewdelete] [showtitles] [doit] [max_to_delete <Number>]
```
* `showtitles` - output file title as well as file id in messages; this requires an additional API call per file.
* `previewdelete` - output revisions to be deleted but do not delete them
* `doit` - no revisions are deleted unless doit is specified
* `max_to_delete <Number>` - no revisions are deleted if the number of revisions to delete exceeds `<Number>`; the default value is one. Set `<Number>` to 0 for no limit.

When deleting revisions, the last remaining revision can not be deleted. If the `<Number>` or `<Time>` selections identify all of the revisions for a file,
the following adjustments are made:
* `first <Number>` - leave the latest revision
* `last <Number>` - leave the earliest revision
* `allexceptfirst <Number>` - not applicable, can't select all revisions
* `allexceptlast <Number>` -  not applicable, can't select all revisions
* `before <Time>` - leave the latest revision
* `after <Time>` - leave the earleist revision
* `range <Time> <Time>` - leave the earliest revision

## Manage file revisions publishing
If you publish a revision, Google doesn't return the Web link, so setting `published true` is of little
value at the moment.
```
gam <UserTypeEntity> update filerevisions <DriveFileEntity> select <DriveFileRevisionIDEntity>
        [published [<Boolean>]] [publishauto [<Boolean>]] [publishedoutsidedomain [<Boolean>]]
        [previewupdate] [showtitles] [doit] [max_to_update <Number>]
```
When `select <DriveFileRevisionIDEntity>` is omitted, all revisions are updated. 

* `keepforever true` - Keep revision forever, even if it is no longer the head revision
* `keepforever false` - Do not keep revision forever
* `published true` - Publish these revision to the web
* `published false` - Do not publish these revision to the web
* `publishauto true` - Automaticaly publish subsequent revisions to the web
* `publishauto false` - Do not automaticaly publish subsequent revisions to the web
* `publishedoutsidedomain true` - Publish these revisions outside the domain
* `publishedoutsidedomain  false` - Do not publish these revisions outside the domain

* `showtitles` - output file title as well as file id in messages; this requires an additional API call per file.
* `previewupdate` - output revisions to be updated but do not update them
* `doit` - no revisions are updated unless doit is specified
* `max_to_update <Number>` - no revisions are updated if the number of revisions to update exceeds `<Number>`; the default value is one. Set `<Number>` to 0 for no limit.

## Display file revisions
```
gam <UserTypeEntity> show filerevisions <DriveFileEntity>
        [select <DriveFileRevisionIDEntity>]
        [previewdelete] [showtitles]
        [<RevisionsFieldName>*|(fields <RevisionsFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [stripcrsfromname]
gam <UserTypeEntity> print filerevisions <DriveFileEntity> [todrive <ToDriveAttribute>*]
        [select <DriveFileRevisionIDEntity>]
        [previewdelete] [showtitles] [oneitemperrow]
        [<RevisionsFieldName>*|(fields <RevisionsFieldNameList>)]
        (orderby <DriveFileOrderByFieldName> [ascending|descending])*
        [stripcrsfromname]
```
When `select <DriveFileRevisionIDEntity>` is omitted, all revisions are displayed. When `select <DriveFileRevisionIDEntity>`is specified,
`previewdelete` will make the list of revisions displayed match the list that would be processed by `delete filerevisions` due to the fact
that the last remaining revision can not be deleted.

* `showtitles` - output file title as well as file id in output; this requires an additional API call per file.

With `print filerevisions`, by default the revisions selected for display are all output on one line as a repeating item with the matching file id.
When `oneitemperrow` is specified, each revision is output on a separate row with the matching file id. This simplifies processing the CSV file with subsequent Gam commands.

The `stripcrsfromname` option strips nulls, carriage returns and linefeeds from drive file names.
This option is special purpose and will not generally be used.
