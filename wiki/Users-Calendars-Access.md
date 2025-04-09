# Users - Calendars - Access
- [Notes](#Notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Calendar selection](#calendar-selection)
- [Manage calendar access](#manage-calendar-access)
- [Display calendar access](#display-calendar-access)
- [Transfer calendar ownership](#transfer-calendar-ownership)

## Notes
Calendar ACL roles (as seen in Calendar GUI):
  * `reader` - See all event details
  * `writer` & `editor`  Make changes to events
  * `owner` - Make changes to events and manage sharing
  * `freebusy` & `freebusyreader` - See only free/busy (hide details)

## API documentation
* [Calendar API - ACLs](https://developers.google.com/google-apps/calendar/v3/reference/acl)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<CalendarItem> ::= <EmailAddress>
<CalendarList> ::= "<CalendarItem>(,<CalendarItem>)*"
<CourseAlias> ::= <String>
<CourseID> ::= <Number>|d:<CourseAlias>
<CourseIDList> ::= "<CourseID>(,<CourseID>)*"
<CourseState> ::= active|archived|provisioned|declined
<CourseStateList> ::= all|"<CourseState>(,<CourseState>)*"
<ResourceID> ::= <String>
<ResourceIDList> ::= "<ResourceID>(,<ResourceID>)*"
<TimeZone> ::= <String>
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<CalendarAttribute> ::=
        (backgroundcolor <ColorValue>)|
        (color <CalendarColorName>)|
        (colorindex|colorid <CalendarColorIndex>)|
        (foregroundcolor <ColorValue>)|
        (hidden <Boolean>)|
        (notification clear|(email <CalendarEmailNotificatonEventTypeList>))|
        (reminder clear|(email|pop <Number>)|(<Number> email|pop))|
        (selected <Boolean>)|
        (summary <String>)

<CalendarSettings> ::=
        (description <String>)|
        (location <String>)|
        (summary <String>)|
        (timezone <TimeZone>)

<CalendarACLRole> ::=
         editor|freebusy|freebusyreader|owner|reader|writer
<CalendarACLScope> ::=
        <EmailAddress>|user:<EmailAdress>|group:<EmailAddress>|
         domain:<DomainName>|domain|default
<CalendarACLScopeList> ::=
        "<CalendarACLScope>(,<CalendarACLScope>)*"
<CalendarACLScopeEntity>::=
        <CalendarACLScopeList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>

<CalendarSelectProperty> ::=
        minaccessrole <CalendarACLRole>|
        showdeleted|
        showhidden

<UserCalendarEntity> ::=
        allcalendars|
        primary|
        <EmailAddress>|
        <UniqueUD>|
        (courses <CourseIDList>)|
        ((courses_with_teacher <UserItem>)|my_courses_as_teacher
          [coursestates <CourseStateList>])|
        ((courses_with_student <UserItem>)|my_courses_as_student
          [coursestates <CourseStateList>])|
        (resource <ResourceID>)|
        (resources <ResourceIDList>)|
        ((calendars <CalendarList>) | <FileSelector> | <CSVFileSelector> |
                                      <CSVkmdSelector> | <CSVDataSelector>)|
        <CalendarSelectProperty>+
```
## Calendar selection

* `allcalendars` - All calendars in a user's calendar list
* `primary` - The user's primary calendar
* `<EmailAddress>` - The address of a calendar in a user's calendar list
* `<UniqueID>` - The uniqueid of a calendar in a user's calendar list
* `courses <CourseIDList>`- The calendars associated with a list of courses
* `courses_with_teacher <UserItem>` - The calendars associated with courses with `<UserItem>` as a teacher
* `my_courses_as_teacher` - The calendars associated with the User from `<UserTypeEntity>` as a teacher
* `courses_with_student <UserItem>` - The calendars associated with courses with `<UserItem>` as a student
* `my_courses_as_student` - The calendars associated with the User from `<UserTypeEntity>` as a student
* `coursestates <CourseStateList>` - Used with the previous four options to select courses in a particular state; the default is all
* `resource <ResourceID>` - The calendar associated with a resource ID
* `resources <ResourceIDList>` - The calendars associated with a list of resource IDs
* `calendars (<CalendarList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>)` - A collection of calendars: [Collections of Items](Collections-of-Items)
* `<CalendarSelectProperty>+` - The calendars in a user's calendar list with the specified properites

## Manage calendar access
```
gam <UserTypeEntity> add calendaracls <UserCalendarEntity>
        <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
gam <UserTypeEntity> update calendaracls <UserCalendarEntity>
        <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
gam <UserTypeEntity> delete calendaracls <UserCalendarEntity>
        [<CalendarACLRole>] <CalendarACLScopeEntity>
```
By default, when you add or update a calendar ACL, notification is sent to the members referenced in the `<CalendarACLScopeEntity>`.
Use `sendnotifications false` to suppress sending the notification.

## Display calendar access
```
gam <UserTypeEntity> info calendaracls <UserCalendarEntity>
        <CalendarACLScopeEntity> [formatjson]
gam <UserTypeEntity> show calendaracls <UserCalendarEntity>
        [noselfowner]
        [formatjson]
```
Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print calendaracls <UserCalendarEntity> [todrive <ToDriveAttribute>*]
        [noselfowner] (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

Add additional columns of data from the command line to the output
* `addcsvdata <FieldName> <String>`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Transfer calendar ownership

You can transfer ownership of calendars from one user to another; only non-primary calendars owned by the source user can be transferred.
```
gam <UserTypeEntity> transfer calendars|seccals <UserItem> [<UserCalendarEntity>]
        [keepuser | (retainrole <CalendarACLRole>)] [sendnotifications <Boolean>]
        [noretentionmessages]
        [<CalendarSettings>] [append description|location|summary] [noupdatemessages]
        [deletefromoldowner] [addtonewowner <CalendarAttribute>*] [nolistmessages]
```
If `<UserCalendarEntity>` is not specified, all of a user's owned secondary calendars will be transferrdd.

By default, the users in `<UserTypeEntity>` retain no role in the transferred calendars.
* `keepuser` - The users in `<UserTypeEntity>` retain their ownership.
* `retainrole <CalendarACLRole>` - The users in `<UserTypeEntity>` retain the specified role.
* `noretentionmessages` - Suppress the original owner role retention messages.

By default, when you add or update a calendar ACL, a notification is sent to the affected users; use `sendnotifications false` to suppress sending the notifications.

You can update calendar settings as part of the transfer. In description, location and summary, #email#, #user# and #username# will be replaced
by the original owner's full email address or just the name portion; #timestamp# will be replaced by the current date and time.
* `<CalendarSettings>` - The value specified will replace the existing value.
* `append description|location|summary` - The specified <CalendarSettings> value will be appended to the existing value.
* `noupdatemessages` - Suppress the settings update messages.

You can manipulate the old and new owner's calendar lists.
* `deletefromoldowner` - Delete the calendar from the old owner's calendar list
* `addtonewowner <CalendarAttribute>*` - Add the calendar to the new owner's calendar list; optionally specify attributes
* `nolistmessages` - Suppress the calendar list add/delete messages.

### Example
Transfer a secondary calendar from oldowner to newowner. Remove the calendar from the old owner's calendar list and add to the new owner's  calendar list.
```
gam user oldowner@domain.com transfer calendars newowner@domain.com c_aaa123zzz@group.calendar.google.com removefromoldowner addtonewowner
```

Transfer ownership of all non-primary calendars from oldowner to newowner; append a message to the calendar description noting the old owner and the time of transfer.
```
gam user oldowner@domain.com transfer calendars newowner@domain.com minaccessrole owner description "(Transferred from #user# on #timestamp#)" append description
```
