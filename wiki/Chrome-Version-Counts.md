# Chrome Version Counts
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Quoting rules](#quoting-rules)
- [Display Chrome version counts](#display-chrome-version-counts)

## API documentation
* [Chrome Management API - Count Chrome Versions](https://developers.google.com/chrome/management/reference/rest/v1/customers.reports/countChromeVersions)

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
        never|
        today
<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String>)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>
<OrgUnitList> ::= "<OrgUnitItem>(,<OrgUnitItem>)*"
```
## Quoting rules
Items in a list can be separated by commas or spaces; if an item itself contains a comma, a space or a single quote, special quoting must be used.
Typically, you will enclose the entire list in double quotes and quote each item in the list as detailed below.

- Items, separated by commas, without spaces, commas or single quotes in the items themselves
   * ```"item,item,item"```
- Items, separated by spaces, without spaces, commas or single quotes in the items themselves
   * ```"item item item"```
- Items, separated by commas, with spaces, commas or single quotes in the items themselves
   * ```"'it em','it,em',\"it'em\""```
- Items, separated by spaces, with spaces, commas or single quotes in the items themselves
   * ```"'it em' 'it,em' \"it'em\""```

## Display Chrome version counts
These counts are for provisioned devices.
```
gam show chromeversions
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [start <Date>] [end <Date>]
        [recentfirst [<Boolean>]]
        [formatjson]
```
Use these options to select Chrome devices; if none are chosen, all Chrome devices in the account are selected.

- `ou <OrgUnitItem>` - Select devices directly in the OU `<OrgUnitItem>`
- `ou_and_children <OrgUnitItem>` - Select devices in the OU `<OrgUnitItem>` and its sub OUs
- `ous <OrgUnitList>` - Select devices directly in the OUs `<OrgUnitList>`
- `ous_and_children <OrgUnitList>` - Select devices in the OUs `<OrgUnitList>` and their sub OUs
- `start <Date>` - The minimum `last_active_date` for the devices
- `end <Date>` - The maximum `last_active_date` for the devices

By default, the versions are displayed from oldest to most recent; use the `recentfirst` option to reverse this order.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print chromeversions [todrive <ToDriveAttribute>*]
        [(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
         (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
        [start <Date>] [end <Date>]
        [recentfirst [<Boolean>]]
        [formatjson [quotechar <Character>]]
```
Use these options to select Chrome devices; if none are chosen, all Chrome devices in the account are selected.

- `ou <OrgUnitItem>` - Select devices directly in the OU `<OrgUnitItem>`
- `ou_and_children <OrgUnitItem>` - Select devices in the OU `<OrgUnitItem>` and its sub OUs
- `ous <OrgUnitList>` - Select devices directly in the OUs `<OrgUnitList>`
- `ous_and_children <OrgUnitList>` - Select devices in the OUs `<OrgUnitList>` and their sub OUs
- `start <Date>` - The minimum `last_active_date` for the devices
- `end <Date>` - The maximum `last_active_date` for the devices

By default, the versions are displayed from oldest to most recent; use the `recentfirst` option to reverse this order.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
