# Calendars - Access
- [Notes](#Notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage calendar access](#manage-calendar-access)
- [Display calendar access](#display-calendar-access)
- [Old format commands](#old-format-commands)

## Notes
These commands use Client access for all commands except those that reference user's primary calendars
where Service Account access is used. When using Client access on user's secondary calendars, some operations are restricted.
In general, you should use the following commands to manage user's calendars access.
* [Users - Calendars - Access](Users-Calendars-Access)

Client access works when accessing Resource calendars.

Calendar ACL roles (as seen in Calendar GUI):
  * `reader` - See all event details
  * `writer` & `editor`  Make changes to events
  * `owner` - Make changes to events and manage sharing
  * `freebusy` & `freebusyreader` - See only free/busy (hide details)

## API documentation
* [Calendar API - ACLs](https://developers.google.com/google-apps/calendar/v3/reference/acl)

## Definitions
```
<CalendarItem> ::= <EmailAddress>
<CalendarList> ::= "<CalendarItem>(,<CalendarItem>)*"
<CalendarEntity> ::= <CalendarList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<CalendarACLRole> ::= editor|freebusy|freebusyreader|owner|reader|writer
<CalendarACLScope> ::= <EmailAddress>|user:<EmailAdress>|group:<EmailAddress>|domain:<DomainName>|domain|default
<CalendarACLScopeList> ::= "<CalendarACLScope>(,<CalendarACLScope>)*"
<CalendarACLScopeEntity>::= <CalendarACLScopeList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
```
## Manage calendar access
```
gam calendars <CalendarEntity> add acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
gam calendars <CalendarEntity> update acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity> [sendnotifications <Boolean>]
gam calendars <CalendarEntity> delete acls|calendaracls [<CalendarACLRole>] <CalendarACLScopeEntity>
```
By default, when you add or update a calendar ACL, notification is sent to the members referenced in the `<CalendarACLScopeEntity>`.
Use `sendnotifications false` to suppress sending the notification.

## Display calendar access
```
gam calendars <CalendarEntity> info acls|calendaracls <CalendarACLScopeEntity> [formatjson]
gam calendars <CalendarEntity> show acls|calendaracls
        [noselfowner]
        [formatjson]
```
Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam calendars <CalendarEntity> print acls|calendaracls [todrive <ToDriveAttribute>*]
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

### Old format commands
These commands are backwards compatible with Legacy GAM.
```
gam calendar <CalendarEntity> add <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default [sendnotifications <Boolean>]
gam calendar <CalendarEntity> update <CalendarACLRole> ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default [sendnotifications <Boolean>]
gam calendar <CalendarEntity> delete [<CalendarACLRole>] ([user] <EmailAddress>)|(group <EmailAddress>)|(domain [<DomainName>])|default
gam calendar <CalendarEntity> showacl [formatjson]
gam calendar <CalendarEntity> printacl [todrive <ToDriveAttribute>*]
        (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
By default, when you add or update a calendar ACL, notification is sent to the members referenced in the `<CalendarACLScopeEntity>`.
Use `sendnotifications false` to suppress sending the notification.
