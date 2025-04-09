# Python Regular Expressions
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
        [aliasmatchpattern <REMatchPattern>]
```
Collections
```
matchfield|skipfield <FieldName> <REMatchPattern>
keypattern <REMatchPattern>
```

Display Classroom courses based on owner's email address
```
gam print courses [todrive <ToDriveAttribute>*]
        [owneremailmatchpattern <REMatchPattern>]
```

Clear Contacts based on email address
```
gam <UserTypeEntity> clear contacts
        emailmatchpattern <REMatchPattern>
        emailclearpattern <REMatchPattern>
```

Display Contacts based on email address
```
gam <UserTypeEntity> print contacts
        emailmatchpattern <REMatchPattern>
```

Delete Gmail labels based on label names
```
gam <UserTypeEntity> delete labels regex:<REMatchPattern>
```

Display Gmail messages based on label names
```
gam <UserTypeEntity> print|show messages|threads
        [labelmatchpattern <REMatchPattern>
```

Display Gmail messages based on sender email address
```
gam <UserTypeEntity> print|show messages|threads
        [sendermatchpattern <REMatchPattern>]
<LabelName>|regex:<REMatchPattern>
```

Display Gmail messages based on attachment names
```
gam <UserTypeEntity> print|show messages|threads
        [showattachments [attachmentnamepattern <REMatchPattern>]]
```

Save Gmail message attachments based on attachment names
```
gam <UserTypeEntity> show messages|threads
        [saveattachments [attachmentnamepattern <REMatchPattern>]]
```

Select Groups to display and which members to display
```
gam print groups
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
```

Select Groups to display membership and which members to display
```
gam print group-members
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
```

Manage Group membership
```
gam update group|groups <GroupEntity> clear [member] [manager] [owner]
        [emailclearpattern|emailretainpattern <REMatchPattern>]
```

Select User aliases to display
```
gam print users
        [aliasmatchpattern <REMatchPattern>]
```

Display Drive file information based on file names
```
gam <UserTypeEntity> print|show filecounts
        [filenamematchpattern <REMatchPattern>]
gam <UserTypeEntity> print filelist
        [filenamematchpattern <REMatchPattern>]
gam <UserTypeEntity> print|show filetree
        [filenamematchpattern <REMatchPattern>]
```

Update Drive file name based on a pattern
```
gam <UserTypeEntity> update drivefile <DriveFileEntity>
        (replacefilename <REMatchPattern> <String>)*
```

Select Vault exports to download
```
gam download vaultexport <ExportItem> matter <MatterItem>
        [bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
```

## Sub function
When substituting, Gam uses the sub function which looks for a match anywhere in a string.

* "^Foo Bar$"` - match the entire string "Foo Bar"
* "^Foo Bar"` - match a string that starts with "Foo Bar"
* "Foo Bar"` - match a string that contains "Foo Bar"
* "Foo Bar$"` - match a string that ends with "Foo Bar"

Collections
```
keypattern <RESearchPattern> keyvalue <RESubstitution>
```

Updating Calendar event descriptions uses the search function which looks for a match anywhere in a string.
```
gam calendars <CalendarEntity> update events [<EventEntity>]
    replacedescription <REMatchPattern> <RESubstitution>
gam <UserTypeEntity> update events <UserCalendarEntity> [<EventEntity>]
    replacedescription <REMatchPattern> <RESubstitution>
```

Updating Drive file names uses the search function which looks for a match anywhere in a string.
```
gam <UserTypeEntity> update drivefile <DriveFileEntity>
    replacefilename <REMatchPattern> <RESubstitution>

replacefilename "^(.+) (.+)$" "\2 \1" - swap the two words separated by space, e.g. "Foo Bar" becomes "Bar Foo"

```

Updating Gmail label names uses the search function which looks for a match anywhere in a string.
```
gam <UserTypeEntity> update label
        search <REMatchPattern> replace <RESubstitution>

search "^Foo Bar$" replace "Doodle" - replace the entire string "Foo Bar" with "Doodle"

```

Updating User primary email addresses uses the search function which looks for a match anywhere in a string.

```
gam <UserTypeEntity> update user
    updateprimaryemail <RESearchPattern> <RESubstitution>

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
<FieldNameFilter> :: = <REMatchPattern>
<RowValueFilter> ::=
        [(any|all):]regex:<RESearchPattern>|
        [(any|all):]regexcs:<RESearchPattern>|
        [(any|all):]notregex:<RESearchPattern>|
        [(any|all):]notregexcs:<RESearchPattern>
```

Calendar event matchfields use the search function which looks for a match anywhere in a string.
```
<EventMatchProperty> ::=
        (matchfield attendees <EmailAddressEntity>)|
        (matchfield attendeespattern <RESearchPattern>)|
        (matchfield attendeesstatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddressEntity>)|
        (matchfield creatoremail <RESearchPattern>)|
        (matchfield creatorname <RESearchPattern>)|
        (matchfield description <RESearchPattern>)|
        (matchfield location <RESearchPattern>)|
        (matchfield organizeremail <RESearchPattern>)|
        (matchfield organizername <RESearchPattern>)|
        (matchfield status <RESearchPattern>)|
        (matchfield summary <RESearchPattern>)|
        (matchfield transparency <RESearchPattern>)|
        (matchfield visibility <RESearchPattern>)
<EventSelectEntity> ::=
        (<EventSelectProperty>+ <EventMatchProperty>*)
```
Updating user primary email addresses uses the search function which looks for a match anywhere in a string.

```
gam <UserTypeEntity> update user <UserAttribute>* updateprimaryemail <RESearchPattern> <RESubstitution>
```
