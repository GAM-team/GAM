# Calendars - Events
- [Notes](#Notes)
- [API documentation](#api-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Search function
- [Collections of Users](Collections-of-Users)
- [Definitions](#definitions)
- [Recurrence rules](#recurrence-rules)
- [Event colors](#event-colors)
- [Event selection](#event-selection)
- [Add and import calendar events](#add-and-import-calendar-events)
  - [Add calendar attendees](#add-calendar-attendees)
- [Update calendar events](#update-calendar-events)
  - [Update calendar attendees](#update-calendar-attendees)
- [Specify calendar attendees with JSON data](#specify-calendar-attendees-with-json-data)
- [Delete selected calendar events](#delete-selected-calendar-events)
- [Delete all calendar events](#delete-all-calendar-events)
- [Move calendar events to another calendar](#move-calendar-events-to-another-calendar)
- [Empty calendar trash](#empty-calendar-trash)
- [Display calendar events](#display-calendar-events)
- [Old format commands](#old-format-commands)

## Notes
These commands use Client access for all commands except those that reference user's primary calendars
where Service Account access is used. When using Client access on user's secondary calendars, some operations are restricted.
In general, you should use the following commands to manage user's calendars events.
* [Users - Calendars - Events](Users-Calendars-Events)

Client access works when accessing Resource calendars.

## API documentation:
* [Calendar API - Events](https://developers.google.com/calendar/v3/reference/events)
* [Calendar API - Import Events](https://developers.google.com/calendar/v3/reference/events/import)

## Definitions
```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<Year> ::= <Digit><Digit><Digit><Digit>
<Month> ::= <Digit><Digit>
<Day> ::= <Digit><Digit>
<Hour> ::= <Digit><Digit>
<Minute> ::= <Digit><Digit>
<Second> ::= <Digit><Digit>
<MilliSeconds> ::= <Digit><Digit><Digit>
<Date> ::=
        <Year>-<Month>-<Day> |
        (+|-)<Number>(d|w|y) |
        never|
        today
<DateTime> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute> |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
<TimeZone> ::= <String>
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<CalendarItem> ::= <EmailAddress>
<CalendarList> ::= "<CalendarItem>(,<CalendarItem>)*"
<CalendarEntity> ::= <CalendarList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<EmailAddressList> ::= "<EmailAddress>(,<EmailAddress>)*"
<EmailAddressEntity> ::=
        <EmailAddressList> | <FileSelector> | <CSVFileSelector> |
        <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<iCalUID> ::= <String>

<EventAttachmentsSubfieldName> ::=
        attachments.fileid|
        attachments.fileurl|
        attachments.iconlink|
        attachments.mimetype|
        attachments.title

<EventAttendeesSubfieldName> ::=
        attendees.additionalguests|
        attendees.comment|
        attendees.displayname|
        attendees.email|
        attendees.id|
        attendees.optional|
        attendees.organizer|
        attendees.resource|
        attendees.responseStatus|
        attendees.self

<EventConferenceDataSubfieldName> ::=
        conferencedata.conferenceid|
        conferencedata.conferencesolution|
        conferencedata.createrequest|
        conferencedata.entrypoints|
        conferencedata.notes|
        conferencedata.signature

<EventCreatorSubfieldName> ::=
        creator.displayname|
        creator.email|
        creator.id|
        creator.self

<EventFocusTimePropertiesSubfieldName> ::=
        focustimeproperties.chatstatus|
        focustimeproperties.declinemode|
        focustimeproperties.declinemessage

<EventOrganizerSubfieldName> ::=
        organizer.displayname|
        organizer.email|
        organizer.id|
        organizer.self

<EventOutOfOfficePropertiesSubfieldName> ::=
        outofoffice.declinemode|
        outofoffice.declinemessage

<EventWorkingLocationPropertiesSubfieldName> ::=
        workinglocationproperties.homeoffice|
        workinglocationproperties.customlocation|
        workinglocationproperties.officelocation

<EventFieldName> ::=
        anyonecanaddself|
        attachments|
        <EventAttachmentsSubfieldName>|
        attendees|
        <EventAttendeesSubfieldName>|
        attendeesomitted|
        colorid|
        conferencedata|
        <EventConferenceDataSubfieldName>|
        created|
        creator|
        <EventCreatorSubfieldName>|
        description|
        end|endtime|
        endtimeunspecified|
        extendedproperties|
        eventtype|
        <EventFocusTimePropertiesSubfieldName>
        gadget|
        guestscaninviteothers|
        guestscanmodify|
        guestscanseeotherguests|
        hangoutlink|
        htmllink|
        icaluid|
        id|
        location|
        locked|
        organizer|
        <EventOrganizerSubfieldName>|
        originalstart|originalstarttime|
        <EventOutOfOfficePropertiesSubfieldName>
        privatecopy|
        recurrence|
        recurringeventid|
        reminders|
        sequence|
        source|
        start|starttime|
        status|
        summary|
        transparency|
        updated|
        visibility|
        workinglocationproperties|
        <EventWorkingLocationPropertiesSubfieldName>
<EventFieldNameList> ::= "<EventFieldName>(,<EventFieldName>)*"

<AttendeeAttendance> ::= optional|required
<AttendeeStatus> ::= accepted|declined|needsaction|tentative

<EventType> ::=
        birthday|
        default|
        focustime|
        fromgmail|
        outofoffice|
        workinglocation
<EventTypeList> ::= "<EventType>(,<EventType>)*"

<EventSelectProperty> ::=
        (after|starttime|timemin <Time>)|
        (before|endtime|timemax <Time>)|
        (eventtype|eventtypes <EventTypeList>)|
        (query <QueryCalendar>)|
        (privateextendedproperty <String>)|
        (sharedextendedproperty <String>)|
        showdeletedevents|
        showhiddeninvitations|
        singleevents|
        (updatedmin <Time>)

<EventMatchProperty> ::=
        (matchfield attendees <EmailAddressEntity>)|
        (matchfield attendeesonlydomainlist <DomainNameList>)|
        (matchfield attendeesdomainlist <DomainNameList>)|
        (matchfield attendeesnotdomainlist <DomainNameList>)|
        (matchfield attendeespattern <RESearchPattern>)|
        (matchfield attendeesstatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddressEntity>)|
        (matchfield creatoremail <RESearchPattern>)|
        (matchfield creatorname <RESearchPattern>)|
        (matchfield description <RESearchPattern>)|
        (matchfield hangoutlink <RESearchPattern>)|
        (matchfield location <RESearchPattern>)|
        (matchfield organizeremail <RESearchPattern>)|
        (matchfield organizername <RESearchPattern>)|
        (matchfield organizerself <Boolean>)|
        (matchfield status <RESearchPattern>)|
        (matchfield summary <RESearchPattern>)|
        (matchfield transparency <RESearchPattern>)|
        (matchfield visibility <RESearchPattern>)

<EventIDEntity> ::=
        (id|eventid <EventId>) |
        (event|events <EventIdList> |
        <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>)
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<EventSelectEntity> ::=
        (<EventSelectProperty>+ <EventMatchProperty>*)

<EventEntity> ::=
        <EventIDEntity> | <EventSelectEntity>

<EventColorIndex> ::= <Number in range 1-11>
<EventColorName> ::=
        banana|basil|blueberry|flamingo|graphite|grape|
        lavender|peacock|sage|tangerine|tomato
<PropertyKey> ::= <String>
<PropertyValue> ::= <String>
<TimeZone> ::= <String>

<EventAttribute> ::=
        (allday <Date>)|
        (anyonecanaddself [<Boolean>])|
        (attachment <String> <URL>)|
        (attendee <EmailAddress>)|
        (attendeestatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddress>)|
        available|
        (birthday <Date>)|
        (color <EventColorName>)|
        (colorindex|colorid <EventColorIndex>)|
        (description <String>)|
        (end|endtime (allday <Date>)|<Time>)|
        (guestscaninviteothers <Boolean>)|
        guestscantinviteothers|
        (guestscanmodify <Boolean>)|
        (guestscanseeotherguests <Boolean>)|
        guestscantseeotherguests|
        hangoutsmeet|
        <JSONData>|
        (jsonattendees [charset <Charset>] <String>)|
        (jsonattendees file <FileName> [charset <Charset>])|
        (location <String>)|
        (noreminders|(reminder email|popup <Number>))|
        (optionalattendee <EmailAddress>)|
        (originalstart|originalstarttime (allday <Date>)|<Time>)|
        (privateproperty <PropertyKey> <PropertyValue>)|
        (range <Date> <Date>)|
        (recurrence <RRULE, EXRULE, RDATE and EXDATE line>)|
        (reminder <Number> email|popup)|
        (resource <ResourceID>)|
        (selectattendees [<AttendeeAttendance>] [<AttendeeStatus>] <UserTypeEntity>)|
        (sequence <Integer>)|
        (sharedproperty <PropertyKey> <PropertyValue>)|
        (source <String> <URL>)|
        (start|starttime (allday <Date>)|<Time>)|
        (status confirmed|tentative|cancelled)|
        (summary <String>)|
        tentative|
        (timerange <Time> <Time>)|
        (timezone <TimeZone>)|
        (transparency opaque|transparent)|
        (visibility default|public|private)

The following attributes are equivalent:
        available - transparency transparent
        guestscantinviteothers - guestscaninviteothers False
        guestscantseeothers - guestscanseeotherguests False
        tentative - status tentative

<EventImportAttribute> ::=
        <EventAttribute>|
        (organizername <String>)|
        (organizeremail <EmailAddress>)

<EventUpdateAttribute> ::=
        <EventAttribute>|
        clearattachments|
        clearattendees|
        clearhangoutsmeet|
        (clearprivateproperty <PropertyKey>)|
        clearresources|
        (clearsharedproperty <PropertyKey>)|
        (removeattendee <EmailAddress>)|
        (removeresource <ResourceID>)|
        (replacedescription <REMatchPattern> <RESubstitution>)|
        (selectremoveattendees <UserTypeEntity>)

<EventNotificationAttribute> ::=
        notifyattendees|(sendnotifications <Boolean>)|(sendupdates all|enternalonly|none)

The following attributes are equivalent:
        notifyattendees - sendupdates all
        sendnotifications false - sendupdates none
        sendnotifications true - sendupdates all

<EventDisplayProperty> ::=
        (alwaysincludeemail)|
        (icaluid <String>)|
        (maxattendees <Integer>)|
        (orderby starttime|updated)|
        (timezone <TimeZone>)
```
## Recurrence rules
Recurring events require a rule: `recurrence <RRULE, EXRULE, RDATE and EXDATE line>`
* https://tools.ietf.org/html/rfc5545#section-3.8.5

This is dense reading; a simpler approach is to define a test event in Google Calendar with
the recurrence rule that you want, then use `gam info event` to get the recurrence rule and use it in subsequent commands.

```
RRULE:FREQ=DAILY - Daily
RRULE:FREQ=DAILY;COUNT=30 - Daily for 30 days
RRULE:FREQ=WEEKLY - Weekly on the same day of the week as the starting day; e.g., every Wednesday
RRULE:FREQ=WEEKLY;COUNT=13 - Weekly on the same day of the week as the starting day; e.g., every Wednesday, for 13 weeks
RRULE:FREQ=MONTHLY - Monthly on the same day of the month as the starting day; e.g., every 15th of the month
RRULE:FREQ=MONTHLY;BYDAY=4TH - Monthly on the fourth instance of the starting day; e.g., every 4th Thursday
```

## Event colors
The event color grid presented in calendar.google.com and `<EventColorIndex>` are related like this:
```
11:tomato 4:flamingo
6:tangerine 5:banana
2:sage 10:basil
7:peacock 9:blueberry
1:lavender 3:grape
8:graphite
```

## Event selection
These are the possible values for `<EventEntity>`; you either specify event IDs or properties used to select events.
If none of the following options are selected, all events are selected.
* `id|eventid <EventId>` - A single event ID
* `event|events <EventIdList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>)` - A collection of event IDs: [Collections of Items](Collections-of-Items)
* `<EventSelectProperty>* <EventMatchProperty>*` - Properties used to select events

The Google Calendar API processes `<EventSelectProperty>*`; you may specify none or multiple properties.
* `after|starttime|timemin <Time>` - Lower bound (exclusive) for an event's end time to filter by. If timeMax is set, timeMin must be smaller than timeMax.
* `before|endtime|timemax <Time>` - Upper bound (exclusive) for an event's start time to filter by. If timeMin is set, timeMax must be greater than timeMin.
* `eventtypes <EventTypeList>` - Select events based on their type.
* `query <QueryCalendar>` - Free text search terms to find events that match these terms in any field, except for extended properties
* `privateextendedproperty <String>` - A required private property; `<String>` must be of the form `propertyName=value`
* `sharedextendedproperty <String>` - A required shared property; `<String>` must be of the form `propertyName=value`
* `showdeletedevents` - Whether to include deleted events (with status equals "cancelled") in the result
* `showhiddeninvitations` - Whether to include hidden invitations in the result
* `singleevents` - Whether to expand recurring events into instances and only return single one-off events and instances of recurring events, but not the underlying recurring events themselves
* `updatedmin <Time>` - Lower bound for an event's last modification time (as a RFC3339 timestamp) to filter by. When specified, entries deleted since this time will always be included regardless of showdeletedevents

GAM processes `<EventMatchProperty>*`; you may specify none or multiple properties.
* `matchfield attendees <EmailAddressEntity>` - All of the attendees in `<EmailAddressEntity>` must be present
* `matchfield attendeesonlydomainlist <DomainNameList>` - All attendee's email addresses must be in a domain in `<DomainNameList>`
  * For example, this lets you look for events with all attendees in your internal domains. You should include `resource.calendar.google.com`
    in `<DomainNameList>` if the events use resources.
* `matchfield attendeesdomainlist <DomainNameList>` - Some attendee's email address must be in a domain in `<DomainNameList>`
  * For example, this lets you look for events with attendees in specific external domains
* `matchfield attendeesnotdomainlist <DomainNameList>` - Some attendee's email address must be in a domain not in `<DomainNameList>`
  * For example, this lets you look for events with attendees not in your internal domains. You should include `resource.calendar.google.com`
    in `<DomainNameList>` if the events use resources.
* `matchfield attendeespattern <RESearchPattern>` - Some attendee's email address must match `<RESearchPattern>`
* `matchfield attendeesstatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddressEntity>` - All of the attendees in `<EmailAddressEntity>` must be present
and must have the specified values.
    * `<AttendeeAttendance>` - Default is `required`
    * `<AttendanceStatus>` - Default is`needsaction`
* `matchfield creatoremail <RESearchPattern>` - The creator email address must match `<RESearchPattern>`
* `matchfield creatorname <RESearchPattern>` - The creator name must match `<RESearchPattern>`
* `matchfield description <RESearchPattern>` - The description (summary) must match `<RESearchPattern>`
* `matchfield location <RESearchPattern>` - The location must match `<RESearchPattern>`
* `matchfield organizeremail <RESearchPattern>` - The organizer email address must match `<RESearchPattern>`
* `matchfield organizername <RESearchPattern>` - The orgainzer name must match `<RESearchPattern>`
* `matchfield status <RESearchPattern>` - The summary must match `<RESearchPattern>`. The API documented values are:
    * `confirmed`
    * `tentative`
    * `cancelled`
* `matchfield summary <RESearchPattern>` - The summary must match `<RESearchPattern>`
* `matchfield transparency <RESearchPattern>` - The summary must match `<RESearchPattern>`. The API documented values are:
    * `opaque` - Busy. The API does not seem to return this value; use `"(^$)|opaque"` to match no value or `opaque`.
    * `transparent` -  Free/Available
* `matchfield visibility <RESearchPattern>` - The summary must match `<RESearchPattern>`. The API documented values are:
    * `default` - The API does not seem to return this value; use `"(^$)|default"` to match no value or `default`.
    * `public` - The API does not seem to return this value if it is the default; use `"(^$)|public"` to match no value or `public`.
    * `private` - The API does not seem to return this value if it is the default; use `"(^$)|private"` to match no value or `private`.
    * `confidential`

## Add and import calendar events
```
gam calendar <CalendarEntity> add event [id <String>] <EventAttribute>+ [<EventNotificationAttribute>]
        [showdayofweek]
        [csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
gam calendar <CalendarEntity> import event icaluid <iCalUID> <EventImportAttribute>+
        [showdayofweek]
        [csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
```
By default, when an event is created|imported, GAM outputs the calendar name and event ID.
* `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` - Output the event details in CSV format.

You can specify multiple attachments; `<String>` is the title of the attachment and `<URL>` is a sharable link from Google Drive.
You must specify all attachments in each command, you can not incrementally add attachments.

Importing events is similar to adding events; the principal difference
is that you must specify an `iCalUID`. All instances of recurring events will have the same
`iCalUID` but different `EventIDs`. The import command supports two new attributes to set the
event organizer, but the API doesn't seem to honor the values; the organizer is set to
the calendar owner.

## Add calendar attendees
You can specify attendees in the following ways:
* `attendee <EmailAddress>` - The attendee attendance is required with status `needsaction'
* `optionalattendee <EmailAddress>` - The attendee attendance is optional with status `needsaction'
* `attendeestatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddress>` - One attendee
  * If `<AttendeeAttendance>` is not specified, the attendee is required to attend
  * If `<AttendeeStatus>` is not specified, `needsaction` is chosen
* `jsonattendees [charset <Charset>] <String>`
* `jsonattendees file <FileName> [charset <Charset>]`
* `selectattendees [<AttendeeAttendance>] [<AttendeeStatus>] <UserTypeEntity>` - Multiple attendees
  * If `<AttendeeAttendance>` is not specified, all attendees are required to attend
  * If `<AttendeeStatus>` is not specified, `needsaction` is chosen
* `resource <ResourceID>` - Add a resource attendee to the event

To add an attendee to a single recurring calendar event, you need to specify the ID of that specific event. 
```
gam calendar <CalendarEntity> update event id xxxxxxx_YYYYMMDDTHHMMSSZ attendee attendee@domain.com
```
For `<UserTypeEntity>` See: [Collections of Users](Collections-of-Users)

## Update calendar events
```
gam calendar <CalendarEntity> update event [<EventEntity>] <EventUpdateAttribute>+ [<EventNotificationAttribute>]
        [showdayofweek]
        [csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
```
If `<EventEntity>` is not specified, all events in `<CalendarEntity>` are selected. This is not typically used
unless you're trying to change a basic `<EventAttribute>`, e.g., `color`, on all events.

By default, when an event is updated, GAM outputs the calendar name and event ID.
* `csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` - Output the event details in CSV format.

You can clear/modify existing attributes:
* `clearattachments` - Delete all attachments
* `clearhangoutsmeet` - Clear Hangouts/Meet link
* `clearprivateproperty <PropertyKey>` - Clear private properties
* `clearsharedproperty <PropertyKey>` - Clear shared properties
* `replacedescription <REMatchPattern> <RESubstitution>` - Modify the description

## Update calendar attendees
The default behavior is to allow incremental changes to the attendees list;
the current attendee list is downloaded and the specified changes are applied.

The `replacemode` option causes the current attendee list to be replaced with the specified changes.

You can add attendees in the following ways:
* `attendee <EmailAddress>` - The attendee attendance is required with status `needsaction'
* `optionalattendee <EmailAddress>` - The attendee attendance is optional with status `needsaction'
* `attendeestatus [<AttendeeAttendance>] [<AttendeeStatus>] <EmailAddress>` - One attendee
  * If `<AttendeeAttendance>` is not specified, the attendee is required to attend
  * If `<AttendeeStatus>` is not specified, `needsaction` is chosen
* `jsonattendees [charset <Charset>] <String>`
* `jsonattendees file <FileName> [charset <Charset>]`
* `selectattendees [<AttendeeAttendance>] [<AttendeeStatus>] <UserTypeEntity>` - Multiple attendees
  * If `<AttendeeAttendance>` is not specified, all attendees are required to attend
  * If `<AttendeeStatus>` is not specified, `needsaction` is chosen
* `resource <ResourceID>` - Add a resource attendee to the event

You can remove attendees in the following ways:
* `clearattendees` - Clear all current attendees from the attendee list
* `removeattendee <EmailAddress>` - Remove a single attendee from the attendee list
* `selectremoveattendees <UserTypeEntity>` - Remove a selected collection of attendees from the attendee list
* `clearresources` - Clear all resource attendees from the event
* `removeresource <ResourceID>` - Remove a resource attendee from the event

For `<UserTypeEntity>` See: [Collections of Users](Collections-of-Users)

## Specify calendar attendees with JSON data
You can predefine lists of attendees and use them when creating/updating events. If you set `responseStatus` to `accepted`, no notifications are sent.
```
$ more attendees.json
{"attendees": [{"email": "testuser2@domain.com", "responseStatus": "needsAction", "optional": "True"}, {"email": "testuser3@domain.com", "responseStatus": "accepted"}, {"email": "testuser4@domain.com", "responseStatus": "accepted"}]}
```
You can use output the attendee information for an event in a calendar and use that data when defining other events.
```
$ gam redirect stdout ./attendees.json calendar testuser1@domain.com info event id 0000h8kk7c9o2tonk73hu2zzzz fields attendees formatjson 
$ more attendees.json 
{"calendarId": "testuser1@domain.com", "event": {"attendees": [{"email": "testuser3@domain.com", "responseStatus": "accepted"}, {"email": "testuser4@domain.com", "responseStatus": "accepted"}], "id": "0000h8kk7c9o2tonk73hu2zzzz"}}
```
Use `jsonattendees file ./attendees.json` in `create/update event`.

## Delete selected calendar events
```
gam calendar <CalendarEntity> delete events [<EventEntity>] [doit] [<EventNotificationAttribute>]
gam calendar <CalendarEntity> purge events [<EventEntity>] [doit] [<EventNotificationAttribute>]
```
If `<EventEntity>` is not specified, all events in `<CalendarEntity>` are selected. This is not typically used.

No events are deleted unless you specify the `doit` option; omit `doit` to verify that you properly selected the events to delete.

When events are deleted from a calendar, they are moved to the calendar's trash and are only permanently deleted (purged) after 30 days.
Following a suggestion here (https://stackoverflow.com/questions/41043053/how-to-empty-calendar-trash-via-google-services) you can permanently delete
calendar events with `purge events`. This is achieved by creating a temporary calendar, deleting the events, moving the deleted events to the temporary calendar
and then deleting the temporary calendar.

## Delete all calendar events
For a user's primary calendar:
```
gam calendar <CalendarEntity> wipe events
```
For non-primary calendars:
```
gam calendar <CalendarEntity> delete events [doit] [<EventNotificationAttribute>]
```
No events are deleted unless you specify the `doit` option; omit `doit` to verify that you properly selected the events to delete.

## Move calendar events to another calendar
Generally you won't move all events from one calendar to another; typically, you'll move events created by the event creator
using `matchfield creatoremail <RESearchPattern>` in conjunction with other `<EventSelectProperty>` and `<EventMatchProperty>` options.
```
gam calendar <CalendarEntity> move event [<EventEntity>] destination|to <CalendarItem> [<EventNotificationAttribute>]
```

## Empty calendar trash
A user signed in to Google Calendar can empty the calendar trash but there is no direct API support for this operation.
To empty the calendar trash a temporary calendar is created, the deleted events are moved to the temporary calendar and then the temporary calendar is deleted.
```
gam calendar|calendars <CalendarEntity> empty calendartrash
```

## Display calendar events
```
gam calendar <CalendarEntity> info events [<EventEntity>] [maxinstances <Number>]
        [fields <EventFieldNameList>] [showdayofweek]
        [formatjson]
```
In `<EventEntity>`, any `<EventSelectProperty>` options must precede all other options.

* `maxinstances -1` - Default, display base event
* `maxinstances 0` - Display all instances of a recurring event
* `maxinstances N` - Display first N instances of a recurring event

`showdayofweek` displays `dayOfWeek` when event start and end times are displayed.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam calendar <CalendarEntity> show events [<EventEntity>] <EventDisplayProperty>*
        [fields <EventFieldNameList>] [showdayofweek]
        [countsly] [formatjson]
```
In `<EventEntity>`, any `<EventSelectProperty>` options must precede all other options.

By default, only the base event of a recurring event is displayed. Use the `<EventSelectProperty>`
option `singleevents` to display all instances of a recurring event.

`<EventDisplayProperty> orderby starttime` is only valid with `<EventSelectProperty> singleevents`.

`showdayofweek` displays `dayOfWeek` when event start and end times are displayed.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

By default, Gam displays event details, use `countsonly` to display only the number of events. `formatjson` does not apply in this case.

```
gam calendar <CalendarEntity> print events [<EventEntity>] <EventDisplayProperty>*
        [fields <EventFieldNameList>] [showdayofweek]
        [countsonly [eventrowfilter]]
        [formatjson [quotechar <Character>]] [todrive <ToDriveAttribute>*]
```
In `<EventEntity>`, any `<EventSelectProperty>` options must precede all other options.

By default, only the base event of a recurring event is displayed. Use the `<EventSelectProperty>`
option `singleevents` to display all instances of a recurring event.

`<EventDisplayProperty> orderby starttime` is only valid with `<EventSelectProperty> singleevents`.

`showdayofweek` displays columns `start.dayOfWeek` and `end.dayOfWeek` when event start and end times are displayed.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, Gam displays event details, use `countsonly` to display only the number of events. `formatjson` does not apply in this case.

When `countsonly` is specified, the `eventrowfilter` option causes
GAM to apply `config csv_output_row_filter` to the event details rather than the event counts.
This will be useful when `<EventSelectProperty>` and `<EventMatchProperty>` do not have the
capabilty to select the events of interest; e.g., you want to filter based on the event `created` property.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Special character processing
When outputting events with `formatjson` with the goal of adding the events to another calendar,
use these options at the beginning of the command:
```config csv_output_convert_cr_nl false csv_output_no_escape_char true```

On the subsequent command to add the events, use this option at the beginning of the command:
```config csv_input_no_escape_char true```

These options ensure that newline `\n`, double quote `"`, single quote `'` and backslash `\` are
properly processed.

### Old format commands
These commands are backwards compatible with Legacy GAM.
```
gam calendar <CalendarEntity> addevent <EventAttribute>+ [<EventNotificationAttribute>]
gam calendar <CalendarEntity> deleteevent (id|eventid <EventID>)+ [doit] [<EventNotificationAttribute>]
gam calendar <CalendarEntity> moveevent (id|eventid <EventID>)+ destination <CalendarItem> [<EventNotificationAttribute>]
gam calendar <CalendarEntity> updateevent <EventID> <EventAttribute>+ [<EventNotificationAttribute>]
gam calendar <CalendarEntity> wipe
gam calendar <CalendarEntity> printevents <EventSelectProperty>* <EventDisplayProperty>*
        [fields <EventFieldNameList>]
        [countsonly [eventrowfilter]]
        [formatjson [quotechar <Character>]] [todrive <ToDriveAttribute>*]
```
