# Chrome Version History
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Display Chrome platforms](#display-chrome-platforms)
- [Display Chrome channels](#display-chrome-channels)
- [Display Chrome versions](#display-chrome-versions)
- [Display Chrome releases](#display-chrome-releases)

## API documentation
* [Version History API](https://developer.chrome.com/docs/versionhistory/guide)
* [Version Filter](https://developer.chrome.com/docs/versionhistory/reference/#filter)
* [Version Orderby](https://developer.chrome.com/docs/versionhistory/reference/#order)

## Definitions
```
<ChromePlatfornType> ::=
        all|
        android|
        ios|
        lacros|
        linux|
        mac|
        macarm64|
        sebview|
        win|
        win64
<ChromeChannelType> ::=
        beta|
        canary|
        canaryasan|
        dev|
        stable
<ChromeVersionsOrderByFieldName> ::=
        channel|
        name|
        platform|
        version|
<ChromeReleasesOrderByFieldName> ::= 
        channel|
        endtime|
        fraction|
        name|
        platform|
        starttime|
        version
```
## Display Chrome platforms
```
gam show chromehistory platforms
        [formatjson]
```

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chromehistory platforms [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Chrome channels
```
gam show chromehistory channels
        [platform <ChromePlatformType>]
        [formatjson]
```

By default, channels for all platforms are displayed; use `platform <ChromePlatformType>]`
to select a specific platform.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chromehistory channels [todrive <ToDriveAttribute>*]
        [platform <ChromePlatformType>]
        [formatjson [quotechar <Character>]]
```
By default, channels for all platforms are displayed; use `platform <ChromePlatformType>]`
to select a specific platform.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Chrome versions
```
gam show chromehistory versions
        [platform <ChromePlatformType>] [channel <ChromeChannelType>]
        [filter <String>]
        (orderby <ChromeVersionsOrderByFieldName> [ascending|descending])*
        [formatjson]
```
By default, versions for all platforms and channels are displayed; use `platform <ChromePlatformType>]`
and/or `channel <ChromeChannelType>` to select a specific platform and/or channel.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chromehistory versions [todrive <ToDriveAttribute>*]
        [platform <ChromePlatformType>] [channel <ChromeChannelType>]
        [filter <String>]
        (orderby <ChromeVersionsOrderByFieldName> [ascending|descending])*
        [formatjson [quotechar <Character>]]
```
By default, versions for all platforms and channels are displayed; use `platform <ChromePlatformType>]`
and/or `channel <ChromeChannelType>` to select a specific platform and/or channel.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Chrome releases
```
gam show chromehistory releases
        [platform <ChromePlatformType>] [channel <ChromeChannelType>] [version <String>]
        [filter <String>]
        (orderby <ChromeReleasessOrderByFieldName> [ascending|descending])*
        [formatjson]
```
By default, versions for all platforms, channels and versions are displayed; use `platform <ChromePlatformType>]`
and/or `channel <ChromeChannelType>` and/or `version <String>` to select a specific platform and/or channel and/or version.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chromehistory releases [todrive <ToDriveAttribute>*]
        [platform <ChromePlatformType>] [channel <ChromeChannelType>] [version <String>]
        [filter <String>]
        (orderby <ChromeReleasessOrderByFieldName> [ascending|descending])*
        [formatjson [quotechar <Character>]]
```
By default, versions for all platforms, channels and versions are displayed; use `platform <ChromePlatformType>]`
and/or `channel <ChromeChannelType>` and/or `version <String>` to select a specific platform and/or channel and/or version.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
