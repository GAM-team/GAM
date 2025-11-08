# Chrome Device Counts
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Count titles](#count-titles)
- [Display Chrome device counts](#display-chrome-device-counts)

## API documentation
* [Chrome Management API - Count Active Devices](https://developers.google.com/chrome/management/reference/rest/v1/customers.reports/countActiveDevices)
* [Chrome Management API - Count Devices per Boot Type](https://developers.google.com/chrome/management/reference/rest/v1/customers.reports/countDevicesPerBootType)
* [Chrome Management API - Count Devices per Release Channel](https://developers.google.com/chrome/management/reference/rest/v1/customers.reports/countDevicesPerReleaseChannel)

## Notes
To use these features you must add the `Chrome Management API` to your project and authorize
the appropriate scope: `Chrome Management API - read only`.
```
gam update project
gam oauth create
```

## Definitions
```
<Date> ::=
        <Year>-<Month>-<Day> |
        (+|-)<Number>(d|w|y) |
        today
```

## Count titles
`active` - `sevenDaysCount,thirtyDaysCount`
`perboottype` - `devBootTypeCount,unreportedBootTypeCount,verifiedBootTypeCount`
`perreleasechanneel` - `betaChannelCount,canaryChannelCount,devChannelCount,ltcChannelCount,ltsChannelCount,stableChannelCount,unreportedChannelCount,unsupportedChannelCount`

## Display Chrome device counts
```
gam show chromedevicecounts
        (mode all|active|perboottype|perreleasechannel)*
        [date <Date>]
        [formatjson]
```
By default, `mode all` is selected

By default, `date today` is selected.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chromedevicecounts [todrive <ToDriveAttribute>*]
        (mode all|active|perboottype|perreleasechannel)*
        [date <Date>]
        [formatjson [quotechar <Character>]]
```
By default, `mode all` is selected

By default, `date today` is selected.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
