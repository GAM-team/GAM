# Users - Meet
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Manage Meet Spaces](#manage-meet-spaces)
- [Display Meet Conferences](#display-meet-conferences)
- [Display Meet Participants](#display-meet-participants)
- [Display Meet Recordings](#display-meet-recordings)
- [Display Meet Transcripts](#display-meet-transcripts)

## API documentation
* [Meet API](https://developers.google.com/meet/api/reference/rest/v2)
* [Meet API - Spaces](https://developers.google.com/meet/api/reference/rest/v2/spaces)
* [Meet API - Conference Records](https://developers.google.com/meet/api/reference/rest/v2/conferenceRecords)
* [Meet API - Conference Record Participants](https://developers.google.com/meet/api/reference/rest/v2/conferenceRecords.participants)
* [Meet API - Conference Record Recordings](https://developers.google.com/meet/api/reference/rest/v2/conferenceRecords.recordings)
* [Meet API - Conference Record Transcripts](https://developers.google.com/meet/api/reference/rest/v2/conferenceRecords.transcripts)

## Query documentation
* [Search Conference Records](https://developers.google.com/meet/api/reference/rest/v2/conferenceRecords/list)
* [Search Conference Participants](https://developers.google.com/meet/api/reference/rest/v2/conferenceRecords.participants/list)

## Introduction
These features were added in version 6.81.00.

To use these commands you must add the 'Meet API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
...
[*] 36)  Meet API (supports readonly)

```
## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
```
<MeetConferenceName> ::= conferenceRecords/<String>
<MeetSpaceName> ::= spaces/<String> | <String>
<MeetSpaceOptions> ::=
        accesstype open|trusted|restricted |
        entrypointaccess all|creatorapponly |
        moderation <Boolean> |
        chatrestriction hostsonly|norestriction |
        reactionrestriction hostsonly|norestriction |
        presentrestriction hostsonly|norestriction |
        defaultjoinasviewer <Boolean> |
        firstjoiner hostsonly|anyone |
        recording <Boolean> |
        transcription <Boolean> |
        smartnotes <Boolean>
```

## Manage Meet Spaces
### Create a meet space
```
gam <UserTypeEntity> create meetspace
        <MeetSpaceOptions>*
        [formatjson|returnidonly]
```
By default, Gam displays the information about the created meetspace as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display the meetspace name only

### Update a meet space
```
gam <UserTypeEntity> update meetspace <MeetSpaceName>
        <MeetSpaceOptions>*
        [formatjson]
```
By default, Gam displays the information about the created meetspace as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display information about a specific meet space for a user
```
gam <UserTypeEntity> info meetspace <MeetSpaceName>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### End a meet space conference
```
gam <UserTypeEntity> end meetconference <MeetSpaceName>
```

## Display Meet Conferences
```
gam <UserItem> show meetconferences
        [space <MeetSpaceName>] [code <String>]
        [andquery|orquery <String>] [querytime<String> <Time>]
        [formatjson]
```
By default, conferences are shown for all of a user's meet spaces. To limit the display use:
  * `space <MeetSpaceName>` - Display conferences for a specifc space by giving its name
  * `code <String>` - Display conferences for a specifc space by giving its code
  
By default, Gam displays the information about the meet conferences as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserItem> print meetconferences [todrive <ToDriveAttribute>*]
        [space <MeetSpaceName>] [code <String>]
        [andquery|orquery <String>] [querytime<String> <Time>]
        [formatjson [quotechar <Character>]]
```
By default, conferences are shown for all of a user's meet spaces. To limit the display use:
  * `space <MeetSpaceName>` - Display conferences for a specifc space by giving its name
  * `code <String>` - Display conferences for a specifc space by giving its code
  
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.


## Display Meet Participants
```
gam <UserItem> show meetparticipants <MeetConferenceName>
        [query <String>] [querytime<String> <Time>]
        [formatjson]
```
By default, Gam displays the information about the meet participants as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserItem> print meetparticipants <MeetConferenceName> [todrive <ToDriveAttribute>*]
        [query <String>] [querytime<String> <Time>]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.


## Display Meet Recordings
```
gam <UserItem> show meetrecordings <MeetConferenceName>
        [formatjson]
```
By default, Gam displays the information about the meet recordings as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserItem> print meetrecordings <MeetConferenceName> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.


## Display Meet Transcripts
```
gam <UserItem> show meettranscripts <MeetConferenceName>
        [formatjson]
```
By default, Gam displays the information about the meet transcripts as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserItem> print meettranscripts <MeetConferenceName> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

