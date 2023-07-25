# CSV Input Filtering
- [Python Regular Expressions](Python-Regular-Expressions) Search function
- [Definitions](#definitions)
- [Quoting rules](#quoting-rules)
- [Column row filtering](#column-row-filtering)
- [Column row limiting](#column-row-limiting)
- [Saving filters in gam.cfg](#saving-filters-in-gamcfg)
- [Validate filters](#validate-filters)

There are two values in `gam.cfg` that can be used to filter the input from `gam csv` commands.
* `csv_input_row_filter` - A list or JSON dictionary used to include specific rows based on column values
* `csv_input_row_drop_filter` - A list or JSON dictionary used to exclude specific rows based on column values

These filters can be used alone or in conjunction with the `matchfield|skipfield <FieldName> <RegularExpression>` options.
* https://github.com/taers232c/GAMADV-XTD3/wiki/Bulk-Processing#csv-files

## Definitions
[Data Selectors](Collections-of-items)
```
<DataSelector> ::=
        <ListSelector>|
        <FileSelector>|
        <CSVFileSelector>
```
```
<Date> ::=
        <Year>-<Month>-<Day> |
        (+|-)<Number>(d|w|y) |
        never|
        today
<Time> ::=
        <Year>-<Month>-<Day>T<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
<Operator> ::= <|<=|>=|>|=|!=
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html>

<FieldNameFilter> :: = <RegularExpression>
<RowValueFilter> ::=
        [(any|all):]count<Operator><Number>|
        [(any|all):]countrange=<Number>/<Number>|
        [(any|all):]countrange!=<Number>/<Number>|
        [(any|all):]date<Operator><Date>|
        [(any|all):]daterange=<Date>/<Date>|
        [(any|all):]daterange!=<Date>/<Date>|
        [(any|all):]length<Operator><Number>|
        [(any|all):]lengthrange=<Number>/<Number>|
        [(any|all):]lengthrange!=<Number>/<Number>|
        [(any|all):]text<Operator><String>|
        [(any|all):]textrange=<String>/<String>|
        [(any|all):]textrange!=<String>/<String>|
        [(any|all):]time<Operator><Time>|
        [(any|all):]timerange=<Time>/<Time>|
        [(any|all):]timerange!=<Time>/<Time>|
        [(any|all):]boolean:<Boolean>|
        [(any|all):]regex:<RegularExpression>|
        [(any|all):]regexcs:<RegularExpression>|
        [(any|all):]notregex:<RegularExpression>|
        [(any|all):]notregexcs:<RegularExpression>|
        [(any|all):]data:<DataSelector>|
        [(any|all):]notdata:<DataSelector>|
<RowValueFilterList> ::=
        "'<FieldNameFilter>:<RowValueFilter>'(,'<FieldNameFilter>:<RowValueFilter>')*"
<RowValueFilterJSONList> ::=
        '{"<FieldNameFilter>": "<RowValueFilter>"(,"<FieldNameFilter>": "<RowValueFilter>")*}' |
        "{\"<FieldNameFilter>\": \"<RowValueFilter>\"(,\"<FieldNameFilter>\": \"<RowValueFilter>\")*}"
```
## Quoting rules
Name:value form.
```
<RowValueFilterList> ::=
        "'<FieldNameFilter>:<RowValueFilter>'(,'<FieldNameFilter>:<RowValueFilter>')*"
```
* `<RowValueFilterList>`, even if it has one element, should be enclosed in `"`.
* Each `<FieldNameFilter>:<RowValueFilter>` pair should be enclosed in `'`.
* If `<FieldNameFilter>` contains a `:` or a space, it should be enclosed in `\"`.
* If `<RegularExpression>` or `<DataSelector>` in `<RowValueFilter>` contain a space, it should be enclosed in `\"`.

Example:
```
csv_input_row_filter "'\"accounts:used_quota_in_mb\":count>15000'"
csv_input_row_filter "'email:data:\"csvfile gsheet:email user@domain.com FileID Sheet1\"'"
```
JSON form.
```
<RowValueFilterJSONList> ::=
        '{"<FieldNameFilter>": "<RowValueFilter>"(,"<FieldNameFilter>": "<RowValueFilter>")*}' |
        "{\"<FieldNameFilter>\": \"<RowValueFilter>\"(,\"<FieldNameFilter>\": \"<RowValueFilter>\")*}"
```
* The first JSON form can be used on Linux and Mac OS; it can not be used on Windows.
* The second JSON form can be used on Linux, Mac OS and Windows.
* If `<FieldNameFilter>` contains a `:` or a space, no additional quoting is required

Example:
```
csv_input_row_filter '{"accounts:used_quota_in_mb": "count>=150"}'
csv_input_row_filter "{\"accounts:used_quota_in_mb\": \"count>=150\"}"
```

## Column row filtering
Row filtering includes/excludes rows based on column values.

### Field names
Field names are specified by regular expressions; at its simplest, you specify a complete field name.
Field names are matched in a case insensitive manner.

If the field name doesn't contain any of the following regular expression characters `^$*+|$[{(`,
it will be surrounded with `^$` so that it doesn't match any subfields that begin with the field name as a prefix.

The following filter will match the count field and not the subfields.
```
config csv_input_row_filter "'externalIds:countrange=1/10'"

primaryEmail,externalIds,externalIds.0.type,externalIds.0.value,externalIds.1.type,externalIds.1.value,...
```

### Inclusive filters
You can include rows for gam csv commands based on column values. You specify a list
of fields(headers) and the values they must have. `csv_input_row_filter` is used to specify the 
fields and values. Each field name/expression can appear only once in the list.

You specify whether all or any value filters must match for the row to be included in the input.

* `csv_input_row_filter_mode allmatch` - All value filters must match for the row to be included in the input; this is the default
* `csv_input_row_filter_mode anymatch` - Any value filter must match for the row to be included in the input

```
gam config csv_input_row_filter <RowValueFilterList> ...
gam config csv_input_row_filter <RowValueFilterJSONList> ...
```

### Exclusive filters
You can exclude rows for gam csv commands based on column values. You specify a list
of fields(headers) and the values they must not have. `csv_input_row_drop_filter` is used to specify the 
fields and values. Each field name/expression can appear only once in the list.

You specify whether all or any value filters must match for the row to be excluded from the input.

* `csv_input_row_filter_drop_mode allmatch` - If all value filters match, the row is excluded from the input
* `csv_input_row_filter_drop_mode anymatch` - If any value filter matches, the row is excluded from the input; this is the default

```
gam config csv_input_row_drop_filter <RowValueFilterList> ...
gam config csv_input_row_drop_filter <RowValueFilterJSONList> ...
```

### Matches
A filter matches if the field has the desired value. lf you specify a regular expression for a field name that matches
several columns, the filter matches if any of the columns has a match. In the case of `notregex|notregexcs|notdata`,
the filter matches if none (not any) of the columns has a match.

`<RowValueFilter>` allows specifying that the filter will match only if all of the columns have a match.
In the case of `notregex|notregexcs|notdata`, the filter matches if some (not all) of the columns have a match.
If neither `any` or `all` is explicitly specified, `any` is the default.

These are the row value filter types:
* `count<Operator><Number>` - Used on fields with numbers; a blank field will not match
* `countrange=<Number>/<Number>` - Used on fields with numbers; a blank field will not match
  * The field value must be `>=` the left `<Number>` and `<=` the right `<Number>`
* `countrange!=<Number>/<Number>` - Used on fields with numbers; a blank field will not match
  * The field value must be `<` the left `<Number>` or `>` the right `<Number>`
* `date<Operator><Date>` - Used on fields with dates or times; only the date portion of a time field is compared; a blank field will not match
* `daterange=<Date>/<Date>` - Used on fields with dates or times; only the date portion of a time field is compared; a blank field will not match
  * The field value must be `>=` the left `<Date>` and `<=` the right `<Date>`
* `daterange!=<Date>/<Date>` - Used on fields with dates or times; only the date portion of a time field is compared; a blank field will not match
  * The field value must be `<` the left `<Date>` or `>` the right `<Date>`
* `length<Operator><Number>` - Used on fields with strings; non string fields will not match
* `lengthrange=<Number>/<Number>` - Used on fields with strings; non string fields will not match
  * The field length must be `>=` the left `<Number>` and `<=` the right `<Number>`
* `lengthrange!=<Number>/<Number>` - Used on fields with strings; non string fields will not match
  * The field length must be `<` the left `<Number>` or `>` the right `<Number>`
* `text<Operator><String>` - Used on fields with text
* `textrange=<String>/<String>` - Used on fields with strings
  * The field value must be `>=` the left `<String>` and `<=` the right `<String>`
* `textrange!=<String>/<String>` - Used on fields with strings
  * The field value must be `<` the left `<String>` or `>` the right `<String>`
* `time<Operator><Time>` - Used on fields with times; a blank field will not match
* `timerange=<Time>/<Time>` - Used on fields with times; a blank field will not match
  * The field value must be `>=` the left `<Time>` and `<=` the right `<Time>`
* `timerange!=<Time>/<Time>` - Used on fields with times; a blank field will not match
  * The field value must be `<` the left `<Time>` or `>` the right `<Time>`
* `boolean:<Boolean>` - Used on fields with Boolean values; a blank field is considered False
* `regex:<RegularExpression>` - Used on fields with text; field value must match `<RegularExpression>`; case insensitive
* `regexcs:<RegularExpression>` - Used on fields with text; field value must match `<RegularExpression>`; case sensitive
* `notregex:<RegularExpression>` - Used on fields with text; field value must not match `<RegularExpression>`; case insensitive
* `notregexcs:<RegularExpression>` - Used on fields with text; field value must not match `<RegularExpression>`; case sensitive
* `data:<DataSelector>` - Used on fields with text; field value must match some value in `<DataSelector>`; case sensitive
* `notdata:<DataSelector>` - Used on fields with text; field value must not match any value in `<DataSelector>`; case sensitive

### **Change in behavior.**
In versions prior to `5.12.00`, `regex:<RegularExpression>` and `notregex:<RegularExpression>` were processed in a case sensitive manner;
in many cases this is probably not desirable; e.g., matching file names which are case insensitive.

Now, `regex:<RegularExpression>` and `notregex:<RegularExpression>` are processed in a case insensitive manner.
To get the prior case sensitive processing, use `regexcs:<RegularExpression>` and `notregexcs:<RegularExpression>`.

### Examples
You want to process groups with 100 or more direct members.
```
gam redirect csv GroupInfo.csv print groups fields directmemberscount
gam config csv_input_row_filter "'directMembersCount:count>100'" csv GroupInfo.csv gam group "~email" ...
```
You want to process groups not created by an administrator.
```
gam redirect csv GroupInfo.csv print groups fields admincreated
gam config csv_input_row_drop_filter "'adminCreated:boolean:true'" csv GroupInfo.csv gam group "~email" ...
```
You want to process users created in the last 30 days.
```
gam redirect csv UserInfo.csv print users fields creationtime
gam config csv_input_row_filter "'creationTime:date>=-30d'" csv UserInfo.csv gam user "~primaryEmail" ...
```
You want to process users that are consuming more than 15GB of storage.
Special quoting is required because the field name contains a colon.
```
gam redirect csv UserInfo.csv report user services accounts fields "accounts:used_quota_in_mb"
gam config csv_input_row_filter "'\"accounts:used_quota_in_mb\":count>15000'" csv UserInfo.csv gam user "~primaryEmail" ...
```
## Column row limiting
You can limit the number of rows read from a CSV file.

You want to process the first 10 users that are consuming more than 15GB of storage.
Special quoting is required because the field name contains a colon.
```
gam redirect csv UserInfo.csv report user services accounts fields "accounts:used_quota_in_mb"
gam config csv_input_row_filter "'\"accounts:used_quota_in_mb\":count>15000'" csv_input_row_limit 10 csv UserInfo.csv gam user "~primaryEmail" ...
```

## Saving filters in gam.cfg
If you define a value for `csv_input_row_filter`, `csv_input_row_drop_filter` or `csv_input_row_limit` in the `[DEFAULT]` section of `gam.cfg`,
it will apply to every `gam csv` command which is probably not desirable. You can store them in `gam.cfg` in named sections.
```
[Filter510]
csv_input_row_filter = 'phones.\\\d+.value:regex:(?:^\\\(510\\\) )|(?:^510[- ])\\\d{3}-\\\d{4}'
```
You want to process users with phone numbers in the area code 510; the number can be in the format `(510) ddd-dddd` or `510-ddd-dddd` or `510 ddd-dddd`.
```
gam redirect csv UserInfo.csv print users fields name,phones
gam selectinputfilter Filter510 csv UserInfo.csv gam user "~primaryEmail" ...
```

## Validate filters
Version `6.30.00` added the `gam comment <String>*` command that can be used to validate input row filters.
```
$ more Comment.csv 
col1,col2
aaa,111
bbb,222
ccc,333
$ gam config csv_input_row_drop_filter "col1:regex:bbb" csv Comment.csv gam comment "Col1:~~col1~~" "Col2:~~col2~~"
2022-12-16T12:41:50.045-08:00,0/2,Using 2 processes...
Col1:aaa Col2:111
Col1:ccc Col2:333
$ gam config csv_input_row_filter "col1:regex:bbb"  csv Comment.csv gam comment "Col1:~~col1~~" "Col2:~~col2~~"
2022-12-18T09:42:26.108-08:00,0/1,Using 1 process...
Col1:bbb Col2:222
```