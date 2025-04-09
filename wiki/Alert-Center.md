# Alert Center
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Definitions](#definitions)
- [Introduction](#introduction)
- [Manage alerts](#manage-alerts)
- [Display alerts](#display-alerts)
- [Manage alert feedback](#manage-alert-feedback)
- [Display alert feedback](#display-alert-feedback)

## API documentation
* [Alert Center API](https://developers.google.com/admin-sdk/alertcenter/reference/rest/)

## Query documentation
* [Query Filters](https://developers.google.com/admin-sdk/alertcenter/guides/query-filters)
* [Query Fields](https://developers.google.com/admin-sdk/alertcenter/reference/filter-fields)

## Definitions
```
<AlertID> ::= <String>
<QueryAlert> ::= <String> See: https://developers.google.com/admin-sdk/alertcenter/guides/query-filters
```
## Introduction
For an introduction, start here: https://support.google.com/a/answer/9105393

This API is in beta, most things seem to work although the filter queries don't all work, in particular those that
select alertId and feedbackId.

To use these commands you must update your gam project and service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
```
## Manage alerts
```
gam delete alert <AlertID>
gam undelete alert <AlertID>
```
## Display alerts
```
gam info alert <AlertID> [formatjson]
gam show alerts [filter <QueryAlert>] [orderby createtime [ascending|descending]]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print alerts [todrive <ToDriveAttributes>*] [filter <QueryAlert>] [orderby createtime [ascending|descending]]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Eliminate unwanted fields
You can use [CSV Print Filtering](CSV-Print-Filtering) to reduce the amount of output.
This command will drop all of the data.messages columns.
```
gam config csv_output_header_drop_filter "^data.messages" redirect csv alerts.csv print alerts
```

## Manage alert feedback
```
gam create alertfeedback <AlertID> not_useful|somewhat_useful|very_useful
```
## Display alert feedback
```
gam show alertfeedback [alert <AlertID>] [filter <QueryAlert>] [orderby createtime [ascending|descending]]
        [formatjson]
```
By default, Gam displays feedback for all alerts.
* `alert <AlertID>` - Display feedback for the selected alert
* `filter <QueryAlert>` - Display feebback for the filtered alerts

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print alertfeedback [todrive <ToDriveAttributes>*] [alert <AlertID>] [filter <QueryAlert>] [orderby createtime [ascending|descending]]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays feedback for all alerts.
* `alert <AlertID>` - Display feedback for the selected alert
* `filter <QueryAlert>` - Display feebback for the filtered alerts

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
