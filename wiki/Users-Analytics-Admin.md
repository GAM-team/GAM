# Users - Analytics Admin
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Analytic Accounts](#display-analytic-accounts)
- [Display Analytic Account Summaries](#display-analytic-account-summaries)
- [Display Analytic Properties](#display-analytic-properties)
- [Display Analytic Datastreams](#display-analytic-datastreams)
- [Examples](#examples)

## API documentation
* [Analytics Admin API](https://developers.google.com/analytics/devguides/config/admin/v1/rest)

## Notes
To use these commands you must add 'Analytics Admin API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Display Analytic Accounts
```
gam <UserTypeEntity> show analyticaccounts
        [maxresults <Number>] [showdeleted [<Boolean>]]
        [formatjson]
```
By default, deleted accounts are not displayed, use `showdeleted` to display them.

By default, GAM asks the API for 50 accounts per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print analyticaccounts [todrive <ToDriveAttribute>*]
        [maxresults <Number>] [showdeleted [<Boolean>]]
        [formatjson [quotechar <Character>]]
```
By default, deleted accounts are not displayed, use `showdeleted` to display them.

By default, GAM asks the API for 50 accounts per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Analytic Account Summaries
```
gam <UserTypeEntity> show analyticaccountsummaries
        [maxresults <Number>]
        [formatjson]
```
By default, GAM asks the API for 50 account summaries per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print analyticaccountsummaries [todrive <ToDriveAttribute>*]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
By default, GAM asks the API for 50 account summaries per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Analytic Properties
```
gam <UserTypeEntity> show analyticproperties
        filter <String>
        [maxresults <Number>] [showdeleted [<Boolean>]]
        [formatjson]
```
The required `filter <String>` must be in the format: 'parent:accounts/123', 'parent:properties/123', 'ancestor:accounts/123' or 'firebase_project:123'

By default, deleted properties are not displayed, use `showdeleted` to display them.

By default, GAM asks the API for 50 properties per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print analyticproperties [todrive <ToDriveAttribute>*]
        filter <String>
        [maxresults <Number>] [showdeleted [<Boolean>]]
        [formatjson [quotechar <Character>]]
```
The required `filter <String>` must be in the format: 'parent:accounts/123', 'parent:properties/123', 'ancestor:accounts/123' or 'firebase_project:123'

By default, deleted properties are not displayed, use `showdeleted` to display them.

By default, GAM asks the API for 50 properties per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Analytic Datastreams
```
gam <UserTypeEntity> show analyticdatastreams
        parent <String>
        [maxresults <Number>]
        [formatjson]
```
The required `parent <String>` must be in the format: 'properties/123'.

By default, GAM asks the API for 50 datastreams per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print analyticdatastreams [todrive <ToDriveAttribute>*]
        parent <String>
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
The required `parent <String>` must be in the format: 'properties/123'.

By default, GAM asks the API for 50 datastreams per page of results,
* `maxresults` - Maximum number of results per page; range is 1-200; the default is 50.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.


## Examples
Get all analytic accounts
```
gam config auto_batch_min 1 redirect csv ./AnalyticAccounts.csv multiprocess all users print analyticaccounts

```
Get all analytic account summaries
```
gam config auto_batch_min 1 redirect stdout - multiprocess redirect stderr stdout redirect csv ./AnalyticAccountSummaries.csv multiprocess all users print analyticaccountsummaries

```
Get all analytic account properties (GA4)
```
gam redirect stdout - multiprocess redirect stderr stdout redirect csv ./GA4AnalyticAccountProperties.csv multiprocess csv AnalyticAccounts.csv gam user "~User" print analyticproperties filter "parent:~~name~~"
```
