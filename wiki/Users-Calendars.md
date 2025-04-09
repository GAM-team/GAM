# Users - Calendars
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Calendar colors](#calendar-colors)
- [Calendar selection](#calendar-selection)
- [Display calendar UI settings](#display-calendar-ui-settings)
- [Manage calendars](#manage-calendars)
  - [Create and remove calendars](#create-and-remove-calendars)
  - [Modify calendar settings](#modify-calendar-settings)
  - [Display calendar settings](#display-calendar-settings)
- [Manage calendar lists](#manage-calendar-lists)
- [Display specific calendars from list](#display-specific-calendars-from-list)
- [Display calendar lists](#display-calendar-lists)

## API documentation
* [Calendar API - Calendars](https://developers.google.com/google-apps/calendar/v3/reference/calendars)
* [Calendar API - Calendar Lists](https://developers.google.com/google-apps/calendar/v3/reference/calendarList)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<CalendarItem> ::= <EmailAddress>
<CalendarList> ::= "<CalendarItem>(,<CalendarItem>)*"
<CalendarEntity> ::= <CalendarList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
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

<CalendarACLRole> ::=
        editor|freebusy|freebusyreader|owner|reader|writer

<CalendarSettings> ::=
        (description <String>)|
        (location <String>)|
        (summary <String>)|
        (timezone <TimeZone>)

<CalendarSettingsField> ::=
        conferenceproperties|
        description|
        id|
        location|
        summary|
        timezone
<CalendarSettingsFieldList> ::= "<CalendarSettingsField>(,<CalendarSettingsField>)*"

<CalendarSelectProperty> ::=
        minaccessrole <CalendarACLRole>|
        showdeleted|
        showhidden

<UserCalendarAddEntity> ::=
        <EmailAddress>|
        <UniqueID>|
        (courses <CourseIDList>)|
        ((courses_with_teacher <UserItem>)|my_courses_as_teacher
          [coursestates <CourseStateList>])|
        ((courses_with_student <UserItem>)|my_courses_as_student
          [coursestates <CourseStateList>])|
        (resource <ResourceID>)|
        (resources <ResourceIDList>)|
        ((calendars <CalendarList>) | <FileSelector> | <CSVFileSelector> |
                                      <CSVkmdSelector> | <CSVDataSelector>)
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<UserCalendarEntity> ::=
        allcalendars|
        primary|
        <EmailAddress>|
        <UniqueID>|
        (courses <CourseIDList>)|
        ((courses_with_teacher <UserItem>)|my_courses_as_teacher
          [coursestates <CourseStateList>])|
        ((courses_with_student <UserItem>)|my_courses_as_student
          [coursestates <CourseStateList>])|
        (resource <ResourceID>)|
        (resources <ResourceIDList>)|
        ((calendars <CalendarList>) | <FileSelector> | <CSVFileSelector> |
                                      <CSVkmdSelector> | <CSVDataSelector>)|
        <CalendarSelectProperty>*
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<UserCalendarSettingsField> ::=
        autoaddhangouts|
        datefieldorder|
        defaulteventlength|
        format24hourtime|
        hideinvitations|
        hideweekends|
        locale|
        remindonrespondedeventsonly|
        showdeclinedevents|
        timezone|
        usekeyboardshortcuts|
        weekstart
<UserCalendarSettingsFieldList> ::= "<UserCalendarSettingsField>(,<UserCalendarSettingsField>)*"

<CalendarColorIndex> ::= <Number in range 1-24>
<CalendarColorName> ::=
        amethyst|avocado|banana|basil|birch|blueberry|
        cherryblossom|citron|cobalt|cocoa|eucalyptus|flamingo|
        grape|graphite|lavender|mango|peacock|pistachio|
        pumpkin|radicchio|sage|tangerine|tomato|wisteria|

<CalendarEmailNotificatonEventType> ::=
        eventcreation|eventchange|eventcancellation|eventresponse|agenda
<CalendarEmailNotificatonEventTypeList> ::=
        <CalendarEmailNotificatonEventType>(,<CalendarEmailNotificatonEventType>)*"

<CalendarAttribute> ::=
        (backgroundcolor <ColorValue>)|
        (colorindex|colorid <CalendarColorIndex>)|
        (foregroundcolor <ColorValue>)|
        (hidden <Boolean>)|
        (notification clear|(email <CalendarEmailNotificatonEventTypeList>))|
        (reminder clear|(email|popup <Number>)|(<Number> email|popup))|
        (selected <Boolean>)|
        (summary <String>)

<CalendarListField> ::=
        accessrole|
        backgroundcolor|
        colorid|
        conferenceproperties|
        defaultreminders|
        deleted|
        description|
        foregroundcolor|
        hidden|
        id|
        location|
        notificationsettings|
        primary|
        selected|
        summary|
        summaryoverride|
        timezone
<CalendarListFieldList> ::= "<CalendarListField>(,<CalendarListField>)*"
```
## Calendar colors
The calendar color grid presented in calendar.google.com and `<CalendarColorIndex>` are related like this:
```
21:radicchio 4:tangerine 11:citron 8:basil 16:blueberry 23:grape
22:cherryblossom 5:pumpkin 10:avacado 7:eucalyptus 17:lavender 1:cocoa
3:tomato 6:mango 9:pistachio 14:peacock 18:wisteria 19:graphite
2:flamingo 12:banana 13:sage 15:cobalt 24:amethyst 20:birch
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

## Display calendar UI settings
```
gam <UserTypeEntity> show calsettings
        [fields <UserCalendarSettingsFieldList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print calsettings [todrive <ToDriveAttribute>*]
        [fields <UserCalendarSettingsFieldList>]
        [formatjson [quotechar <Character>]]
```
By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage calendars
### Create and remove calendars
```
gam <UserTypeEntity> create calendar <CalendarSettings>
gam <UserTypeEntity> remove calendars <UserCalendarEntity>
```

### Modify calendar settings
```
gam <UserTypeEntity> modify calendars <UserCalendarEntity> <CalendarSettings>
```

### Display calendar settings
```
gam calendar <CalendarEntity> show settings
        [fields <CalendarSettingsFieldList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam calendar <CalendarEntity> print settings [todrive <ToDriveAttribute>*]
        [fields <CalendarSettingsFieldList>]
        [formatjson [quotechar <Character>]]
```
By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage calendar lists
These commands manage a user's list of calendars.
```
gam <UserTypeEntity> add calendars <UserCalendarAddEntity> <CalendarAttribute>*
gam <UserTypeEntity> update calendars <UserCalendarEntity> <CalendarAttribute>+
gam <UserTypeEntity> delete calendars <UserCalendarEntity>
```

### Examples
A student accidentally removed his course calendars and needs them back.
```
gam user student@domain.com add calendars my_courses_as_student
```
An advisor wants to monitor the course calendars for a student.
```
gam user advisor@domain.com add calendars courses_with_student student@domain.com
```

## Display specific calendars from list
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> info calendars <UserCalendarEntity>
        [fields <CalendarListFieldList>] [permissions]
        [formatjson]
```
* `permissions` adds permission information for user owned calendars to the output.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display calendar lists
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> show calendars
         [primary] <CalendarSelectProperty>*
         [noprimary] [nogroups] [noresources] [nosystem] [nousers]
         [fields <CalendarListFieldList>] [permissions]
         [formatjson]
```
By default, information for all visible, non-deleted calendars is shown.
* `primary` - Limits the selection to the user's primary calendar
* `<CalendarSelectProperty>`
    * `minaccessrole <CalendarACLRole>`- Limits the selection to those calendars where the user's role is at least `<CalendarACLRole>`
    * `showdeleted` - Adds deleted calendars to the selection
    * `showhidden` - Adds hidden calendars to the selection
* `noprimary` - Do not display the users's primary calendar
* `nogroups` - Do not display group calendars, email address ends in "@group.calendar.google.com"
* `noresources` - Do not display resource calendars, email address ends in "@resource.calendar.google.com"
* `nosystem` - Do not display system calendars, email address ends in "@group.v.calendar.google.com"
* `nousers` - Do not display users calendars, email address ends in `domain` value from `gam.cfg`.

* `permissions` adds permission information for user owned calendars to the output.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam <UserTypeEntity> print calendars [todrive <ToDriveAttribute>*]
         [primary] <CalendarSelectProperty>*
         [noprimary] [nogroups] [noresources] [nosystem] [nousers]
         [fields <CalendarListFieldList>] [permissions]
         [formatjson] [delimiter <Character>] [quotechar <Character>]
```
By default, information for all visible, non-deleted calendars is shown.
* `permissions` adds permission information for user owned calendars to the output.
* `primary` - Limits the selection to the user's primary calendar
* `<CalendarSelectProperty>`
    * `minaccessrole <CalendarACLRole>`- Limits the selection to those calendars where the user's role is at least `<CalendarACLRole>`
    * `showdeleted` - Adds deleted calendars to the selection
    * `showhidden` - Adds hidden calendars to the selection
* `noprimary` - Do not display the users's primary calendar
* `nogroups` - Do not display group calendars, email address ends in "@group.calendar.google.com"
* `noresources` - Do not display resource calendars, email address ends in "@resource.calendar.google.com"
* `nosystem` - Do not display system calendars, email address ends in "@group.v.calendar.google.com"
* `nousers` - Do not display users calendars, email address ends in `domain` value from `gam.cfg`.

By default, list items are separated by the `csv_output_field_delimiter' from `gam.cfg`.
* `delimiter <Character>` - Separate list items with `<Character>`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
