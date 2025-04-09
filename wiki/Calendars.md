# Calendars
- [Notes](#Notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Modify calendar settings](#modify-calendar-settings)
- [Display calendar settings](#display-calendar-settings)

## Notes
These commands use Client access for all commands except those that reference user's primary calendars
where Service Account access is used. When using Client access on user's secondary calendars, some operations are restricted.
In general, you should use the following commands to manage user's calendars.
* [Users - Calendars](Users-Calendars)

Client access works when accessing Resource calendars.

## API documentation
* [Calendar API - Calendars](https://developers.google.com/google-apps/calendar/v3/reference/calendars)

## Definitions
```
<CalendarItem> ::= <EmailAddress>
<CalendarList> ::= "<CalendarItem>(,<CalendarItem>)*"
<CalendarEntity> ::= <CalendarList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<TimeZone> ::= <String>
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

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
```
## Modify calendar settings
```
gam calendar <CalendarEntity> modify <CalendarSettings>+
```
## Display calendar settings
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

