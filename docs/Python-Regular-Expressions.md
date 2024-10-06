!# Python Regular Expressions
- [Documentation](#documentation)
- [Match function](#match-function)
- [Sub function](#sub-function)
- [Search function](#search-function)

## Documentation
* https://docs.python.org/3/library/re.html
* https://www.regular-expressions.info/python.html

## Match function
When matching, Gam uses the match function which always looks for a match at the beginning of a string.
* "^Foo Bar$" - match the entire string "Foo Bar"
* "Foo Bar" - match a string that starts with "Foo Bar"
* ".*Foo Bar" - match a string that contains "Foo Bar"
* ".*Foo Bar$" - match a string that ends with "Foo Bar"

Select Aliases to display
```
gam print aliases [todrive <ToDriveAttribute>*]
        [aliasmatchpattern <RegularExpression>]
```
Collections
```
matchfield|skipfield <FieldName> <RegularExpression>
keypattern <RegularExpression>
```

Display Classroom courses based on owner's email address
```
gam print courses [todrive <ToDriveAttribute>*]
        [owneremailmatchpattern <RegularExpression>]
```

Clear Contacts based on email address
```
gam <UserTypeEntity> clear contacts
        emailmatchpattern <RegularExpression>
        emailclearpattern <RegularExpression>
```

Display Contacts based on email address
```
gam <UserTypeEntity> print contacts
        emailmatchpattern <RegularExpression>
```

Delete Gmail labels based on label names
```
gam <UserTypeEntity> delete labels regex:<RegularExpression>
```

Display Gmail messages based on label names
```
gam <UserTypeEntity> print|show messages|threads
        [labelmatchpattern <RegularExpression>
```

Display Gmail messages based on sender email address
```
gam <UserTypeEntity> print|show messages|threads
        [sendermatchpattern <RegularExpression>]
<LabelName>|regex:<RegularExpression>
```

Display Gmail messages based on attachment names
```
gam <UserTypeEntity> print|show messages|threads
        [showattachments [attachmentnamepattern <RegularExpression>]]
```

Save Gmail message attachments based on attachment names
```
gam <UserTypeEntity> show messages|threads
        [saveattachments [attachmentnamepattern <RegularExpression>]]
```

Select Groups to display and which members to display
```
gam print groups
        [emailmatchpattern [not] <RegularExpression>] [namematchpattern [not] <RegularExpression>]
        [descriptionmatchpattern [not] <RegularExpression>]
        [memberemaildisplaypattern|memberemailskippattern <RegularExpression>]
```

Select Groups to display membership and which members to display
```
gam print group-members
        [emailmatchpattern [not] <RegularExpression>] [namematchpattern [not] <RegularExpression>]
        [descriptionmatchpattern [not] <RegularExpression>]
        [memberemaildisplaypattern|memberemailskippattern <RegularExpression>]
```

Manage Group membership
```
gam update group|groups <GroupEntity> clear [member] [manager] [owner]
        [emailclearpattern|emailretainpattern <RegularExpression>]
```

Select User aliases to display
```
gam print users
        [aliasmatchpattern <RegularExpression>]
```

Display Drive file information based on file names
```
gam <UserTypeEntity> print|show filecounts
        [filenamematchpattern <RegularExpression>]
gam <UserTypeEntity> print filelist
        [filenamematchpattern <RegularExpression>]
gam <UserTypeEntity> print|show filetree
        [filenamematchpattern <RegularExpression>]
```

Update Drive file name based on a pattern
```
gam <UserTypeEntity> update drivefile <DriveFileEntity>
        (replacefilename <RegularExpression> <String>)*
```

Select Vault exports to download
```
gam download vaultexport <ExportItem> matter <MatterItem>
        [bucketmatchpattern <RegularExpression>] [objectmatchpattern <RegularExpression>]
```

## Sub function
When substituting, Gam uses the sub function which looks for a match anywhere in a string.

* "^Foo Bar$"` - match the entire string "Foo Bar"
* "^Foo Bar"` - match a string that starts with "Foo Bar"
* "Foo Bar"` - match a string that contains "Foo Bar"
* "Foo Bar$"` - match a string that ends with "Foo Bar"

Collections
```
keypattern <RegularExpression> keyvalue <String>
```

Updating Calendar event descriptions uses the search function which looks for a match anywhere in a string.
```
gam calendars <CalendarEntity> update events [<EventEntity>] replacedescription <RegularExpression> <String>
gam <UserTypeEntity> update events <UserCalendarEntity> [<EventEntity>] replacedescription <RegularExpression> <String>
```

Updating Drive file names uses the search function which looks for a match anywhere in a string.
```
gam <UserTypeEntity> update drivefile <DriveFileEntity>
    replacefilename <RegularExpression> <String>

replacefilename "^(.+) (.+)$" "\2 \1" - swap the two words separated by space, e.g. "Foo Bar" becomes "Bar Foo"

```

Updating Gmail label names uses the search function which looks for a match anywhere in a string.
```
gam <UserTypeEntity> update label
        search <RegularExpression> replace <LabelReplacement>

search "^Foo Bar$" replace "Doodle" - replace the entire string "Foo Bar" with "Doodle"

```

Updating User primary email addresses uses the search function which looks for a match anywhere in a string.

```
gam <UserTypeEntity> update user
    updateprimaryemail <RegularExpression> <EmailReplacement>

updateprimaryemail "^(.).*_(.+)@(.+)$" <\1\2@\3> - replace "first_last@domain.com" with "flast@domain.com"

```

## Search function
When searching, Gam uses the search function which always looks for a match anywhere in a string.

* "^Foo Bar$"` - match the entire string "Foo Bar"
* "^Foo Bar"` - match a string that starts with "Foo Bar"
* "Foo Bar"` - match a string that contains "Foo Bar"
* "Foo Bar$"` - match a string that ends with "Foo Bar"

CSV input and output row filtering use the search function which looks for a match anywhere in a string.
```
<FieldNameFilter> :: = <RegularExpression>
<RowValueFilter> ::=
        [(any|all):]regex:<RegularExpression>|
        [(any|all):]regexcs:<RegularExpression>|
        [(any|all):]notregex:<RegularExpression>|
        [(any|all):]notregexcs:<RegularExpression>
```

Calendar event matchfields use the search function which looks for a match anywhere in a string.
```
<EventMatchProperty> ::=
        (matchfield attendees <EmailAddressEntity>)|
        (matchfield attendeespattern <RegularExpression>)|
        (matchfield attendeesstatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddressEntity>)|
        (matchfield creatoremail <RegularExpression>)|
        (matchfield creatorname <RegularExpression>)|
        (matchfield description <RegularExpression>)|
        (matchfield location <RegularExpression>)|
        (matchfield organizeremail <RegularExpression>)|
        (matchfield organizername <RegularExpression>)|
        (matchfield status <RegularExpression>)|
        (matchfield summary <RegularExpression>)|
        (matchfield transparency <RegularExpression>)|
        (matchfield visibility <RegularExpression>)
<EventSelectEntity> ::=
        (<EventSelectProperty>+ <EventMatchProperty>*)
```
Updating user primary email addresses uses the search function which looks for a match anywhere in a string.

```
gam <UserTypeEntity> update user <UserAttribute>* updateprimaryemail <RegularExpression> <EmailReplacement>
```
