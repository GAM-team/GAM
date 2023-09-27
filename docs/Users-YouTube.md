# Users - YouTube
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Selected YouTube Channels](#display_selected-youtube_channels)
- [Display Owned YouTube Channels](#display-owned-youtube_channels)

## API documentation
* https://developers.google.com/youtube/v3/docs/channels/list

## Notes
To use these commands you must add the 'YouTube API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
```
<YouTubeChannelID> ::= <String>
<YouTubeChannelIDList> ::= "<YouTubeChannelID>(,<YouTubeChannelID>)*"

<YouTubeChannelFieldName> ::=
        brandingsettings|
        contentdetails|
        contentownerdetails|
        id|
        localizations|
        snippet|
        statistics|
        status|
        topicdetails
<YouTubeChannelFieldNameList> ::= "<YouTubeChannelFieldName>(,<YouTubeChannelFieldName>)*"
```
## Display Selected YouTube Channels
Display YouTube channels selected by ID.
```
gam <UserTypeEntity> show youtubechannels
        channels <YouTubeChannelIDList>
        [allfields|(fields <YouTubeChannelFieldNameList>)]
        [formatjson]
```
By default, only the YouTube channel ID is displayed; use `allfields|fields` to selct additional fields for display.

By default, Gam displays the YouTube channels as an indented list of keys and values.
* `formatjson` - Display the YouTube channels in JSON format

```
gam <UserTypeEntity> print youtubechannels [todrive <ToDriveAttribute>*]
        [channels <YouTubeChannelIDList>]
        [allfields|(fields <YouTubeChannelFieldNameList>)]
        [formatjson [quotechar <Character>]]
```
By default, only the YouTube channel ID is displayed; use `allfields|fields` to selct additional fields for display.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/proces output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/procesable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Owned YouTube Channels
Display YouTube channels owned by a user.
```
gam <UserTypeEntity> show youtubechannels
        [allfields|(fields <YouTubeChannelFieldNameList>)]
        [formatjson]
```
By default, only the YouTube channel ID is displayed; use `allfields|fields` to selct additional fields for display.

By default, Gam displays the YouTube channels as an indented list of keys and values.
* `formatjson` - Display the YouTube channels in JSON format

```
gam <UserTypeEntity> print youtubechannels [todrive <ToDriveAttribute>*]
        [allfields|(fields <YouTubeChannelFieldNameList>)]
        [formatjson [quotechar <Character>]]
```
By default, only the YouTube channel ID is displayed; use `allfields|fields` to selct additional fields for display.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/proces output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/procesable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

