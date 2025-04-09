# Users - Gmail - Filters
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Create filters](#create-filters)
- [Delete filters](#delete-filters)
- [Display information about individual filters](#display-information-about-individual-filters)
- [Display information about multiple filters](#display-information-about-multiple-filters)
- [Examples](#examples)

## API documentation
* [Gmail API - Filters](https://developers.google.com/gmail/api/v1/reference/users.settings.filters)
## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<ByteCount> ::= <Number>[m|k|b]
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<LabelID> ::= <String>
<LabelName> ::= <String>

<FilterID> ::= <String>
<FilterIDList> ::= "<FilterID>(,<FilterID>)*"
<FilterIDEntity> ::=
        <FilterIDList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<GmailCategory> ::=
        forums|
        personal|
        promotions|
        social|
        updates

<FilterCriteria> ::=
        excludechats|
        (from <String>)|
        (haswords|query <String>)|
        (musthaveattachment|hasattachment)|
        (nowords|negatedquery <String>)|
        (size larger|smaller <ByteCount>)|
        (subject <String>)|
        (to <String>)

<FilterAction> ::=
        archive|
        (category <GmailCategory>)|
        (forward <EmailAddress>)|
        (important|notimportant)|
        (label <LabelName>)|
        markread|
        neverspam|
        star|
        trash
```
## Create filters
You create filters by defining criteria for selecting messages and actions to perform on them.
```
gam <UserTypeEntity> [create|add] filter
        (<FilterCriteria>+ <FilterAction>+) |
        ((json [charset <Charset>] <String>) |
         (json file <FileName> [charset <Charset>]))
        [buildpath [<Boolean>]]
```
You specify criteria by selecting individual `<FilterCriteria>` or by selecting JSON data created by
`gam <UserTypeEntity> print filters formatjson`.

The `excludechats` criteria is not typically used as it will never apply to incoming messages.
It can be used in filters that are used to identify messages that have already been received.

All `<FilterAction>s` except `forward <EmailAddress>` involve adding/removing labels from a message.
* `archive` - Remove the label INBOX
* `category <GmailCategory>` - Add a CATEGORY label; only one CATEGORY label can be specified 
* `important` - Add the label IMPORTANT
* `notimportant` - Remove the label IMPORTANT
* `markread` - Remove the label UNREAD
* `neverspam` - Remove the label SPAM
* `star` - Add the label STARRED
* `trash` - Add the label TRASH
* `label <LabelName>` - Add the user label `<LabelName>`; only one user label can be specified. It will be created if necessary.

In Gmail, you can have a multi-level label like `Top/Middle/Bottom`; you can also have a single-level label like `Top/Middle/Bottom`,
* If `buildpath` is omitted or `<Boolean>` is set to False, a <labelName>` containing `/` will be created as single-level.
* If `buildpath` is present and `<Boolean>` is omitted or set to True, a <labelName>` containing `/` will be created as multi-level;
all parent labels are created as necessary.

If `forward <EmailAddress>` is specified, the filter creation will fail if the user has not defined `<EmailAddress>` as a forwarding address.

## Delete filters
```
gam <UserTypeEntity> delete filters <FilterIDEntity>
```

## Display information about individual filters
When you get a filter from Google, all labels mentioned in the filter are specified with their internal Id, not the label name the user sees.
Gam has to make an extra API call to get the labels so it can map from id to name so the output reflects the label names that are familiar to the user.
If you don't need to see the label names, you can eliminate the extra API call by specifying `labelidsonly`.
```
gam <UserTypeEntity> info filters <FilterIDEntity> [labelidsonly] [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display information about multiple filters
When you get a filter from Google, all labels mentioned in the filter are specified with their internal Id, not the label name the user sees.
Gam has to make an extra API call to get the labels so it can map from id to name so the output reflects the label names that are familiar to the user.
If you don't need to see the label names, you can eliminate the extra API call by specifying `labelidsonly`.
```
gam <UserTypeEntity> show filters [labelidsonly] [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print filters [labelidsonly] [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the filters as columns of fields; the following option adds a column displaying the filter in JSON format.
* `formatjson` - Display the fields in JSON format.
The columns of fields are for looking at filter characteristics, but are basically unusable as input to `create filter`;
the JSON data can be used by `create filter`.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Examples

### Multi-level labels
When copying filters from one user to another user, you will typically use the `buildpath` option so that
labels like `Top/Middle/Bottom` get created as multi-level.

### Copy all filters from one user to another
Generate a CSV file of the source user's Gmail filters; include JSON data, only save the JSON column.
```
gam config csv_output_header_filter JSON redirect csv filterjson.csv user sourceuser@domain.com print filters formatjson quotechar "'"
```
Create those filters for the target user.
Use a single thread as Google has issues occasionally when multiple filters are being created simultaneously.
```
gam config num_threads 1 csv filterjson.csv quotechar "'" gam user targetuser@domain.com create filter json "~JSON" buildpath
```

### Copy all filters from one user to multiple other users
Generate a CSV file of the source user's Gmail filters; include JSON data, only save the JSON column.
```
gam config csv_output_header_filter JSON redirect csv filterjson.csv user sourceuser@domain.com print filters formatjson quotechar "'"
```
Create those filters for the target users.
Make a file CopyFilters.bat containing a line like the following for each user.
Use a single thread as Google has issues occasionally when multiple filters are being created simultaneously.
```
gam config num_threads 1 csv filterjson.csv quotechar "'" gam user targetuser@domain.com create filter json "~JSON" buildpath
```

Execute the batch.
```
gam tbatch CopyFilters.bat
```

### Copy a specific filter from one user to another
Find the desired Filder ID from all the source user's filters to use in the next command.
```
gam redirect stdout ./filter.json user sourceuser@domain.com info filter <FilterID> formatjson
```
Create the filter for the target user.
```
gam user targetuser@domain.com create filter json file ./filter.json buildpath
```

### Copy selected filters from one user to another
Generate a CSV file of all of the source user's Gmail filters; include JSON data, save all columns for selection during creation.
```
gam redirect csv filterjson.csv user sourceuser@domain.com print filters formatjson quotechar "'"
```
Create filters that have the label Staff for the target user.
Use a single thread as Google has issues occasionally when multiple filters are being created simultaneously.
```
gam config num_threads 1 csv_input_row_filter "'label:regex:^label Staff$'" csv filterjson.csv quotechar "'" gam user targetuser@domain.com create filter json "~JSON"
```

### Delete filters referencing a particular label for a user
This can be done in one of two ways; select the filters during `print filters` or during `delete filter`.

Generate a CSV file of the user's Gmail filters that reference label Staff; delete them.
```
gam config csv_output_row_filter "'label:regex:^label Staff$'" redirect csv filter.csv user user@domain.com print filters
gam csv filter.csv gam user "~User" delete filter "~id"
```

Generate a CSV file of all of the user's Gmail filters; delete filters that reference label Staff.
```
gam redirect csv filter.csv user user@domain.com print filters
gam config csv_input_row_filter "'label:regex:^label Staff$'" csv filter.csv gam user "~User" delete filter "~id"
```

