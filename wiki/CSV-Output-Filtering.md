# CSV Output Filtering
- [Python Regular Expressions](Python-Regular-Expressions) Search function
- [Definitions](#definitions)
- [Quoting rules](#quoting-rules)
- [Column header filtering](#column-header-filtering)
- [Column row filtering](#column-row-filtering)
  - [Field names](#field-names)
  - [Inclusive filters](#inclusive-filters)
  - [Exclusive filters](#exclusive-filters)
  - [Matches](#matches)
- [Column row limiting](#column-row-limiting)
- [Saving filters in gam.cfg](#saving-filters-in-gamcfg)

There are seven values in `gam.cfg` that can be used to filter the output from `gam print` commands.
* `csv_output_header_filter` - A list of `<RegularExpressions>` used to select specific column headers to include
* `csv_output_header_drop_filter` - A list of `<RegularExpressions>` used to select specific column headers to exclude
* `csv_output_header_force` - A list of <Strings> used to specify the exact column headers to include
* `csv_output_header_order` - A list of <Strings> used to specify the column header order; any headers in the file but not in the list will appear after the headers in the list.
* `csv_output_row_filter` - A list or JSON dictionary used to include specific rows based on column values
* `csv_output_row_drop_filter` - A list or JSON dictionary used to exclude specific rows based on column values
* `csv_output_row_limit` - A limit on the number of rows written

The original implementation required that row filters be expressed in JSON notation; these are almost
impossible to enter correctly in Windows; on Mac OS or Linux, it's easy. You can now enter the row filters as lists
on all platforms.

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
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<FieldNameFilter> :: = <REMatchPattern>
<ColumnFieldNameFilterList> ::= "<FieldNameFilter>(,<FieldNameFilter>)*"
<RowValueFilter> ::=
        [(any|all):]boolean:<Boolean>|
        [(any|all):]count<Operator><Number>|
        [(any|all):]countrange!=<Number>/<Number>|
        [(any|all):]countrange=<Number>/<Number>|
        [(any|all):]data:<DataSelector>|
        [(any|all):]date<Operator><Date>|
        [(any|all):]daterange!=<Date>/<Date>|
        [(any|all):]daterange=<Date>/<Date>|
        [(any|all):]length<Operator><Number>|
        [(any|all):]lengthrange!=<Number>/<Number>|
        [(any|all):]lengthrange=<Number>/<Number>|
        [(any|all):]notdata:<DataSelector>
        [(any|all):]notregex:<RESearchPattern>|
        [(any|all):]notregexcs:<RESearchPattern>|
        [(any|all):]regex:<RESearchPattern>|
        [(any|all):]regexcs:<RESearchPattern>|
        [(any|all):]text<Operator><String>|
        [(any|all):]textrange!=<String>/<String>|
        [(any|all):]textrange=<String>/<String>|
        [(any|all):]time<Operator><Time>|
        [(any|all):]timeofdayrange!=<Hour>:<Minute>/<Hour>:<Minute>|
        [(any|all):]timeofdayrange=<Hour>:<Minute>/<Hour>:<Minute>|
        [(any|all):]timerange!=<Time>/<Time>|
        [(any|all):]timerange=<Time>/<Time>|
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
* If `<RESearchPattern>` or `<DataSelector>` in `<RowValueFilter>` contain a space, it should be enclosed in `\"`.
* If `<FieldNameFilter>` or `<RESearchPattern>` in `<RowValueFilter>` contain a `\` to escape a special character
or enter a special sequence, enter `\\\` on Linux and Mac OS, `\\` on Windows,

Examples:
```
csv_output_row_filter "'\"accounts:used_quota_in_mb\":count>15000'"
csv_output_row_filter "'email:data:\"csvfile gsheet:email user@domain.com FileID Sheet1\"'"
Linux and Mac OS
csv_output_row_filter "'phones.\\\d+.value:regex:(?:^\\\(510\\\) )|(?:^510[- ])\\\d{3}-\\\d{4}'"
Windows
csv_output_row_filter "'phones.\\d+.value:regex:(?:^\\(510\\) )|(?:^510[- ])\\d{3}-\\d{4}'"
```
JSON form.
```
<RowValueFilterJSONList> ::=
        '{"<FieldNameFilter>": "<RowValueFilter>"(,"<FieldNameFilter>": "<RowValueFilter>")*}' |
        "{\"<FieldNameFilter>\": \"<RowValueFilter>\"(,\"<FieldNameFilter>\": \"<RowValueFilter>\")*}"
```
* The first form can be used on Linux and Mac OS; it can not be used on Windows.
* The second form can be used on Linux, Mac OS and Windows.
* If `<FieldNameFilter>` contains a `:`, no additional quoting is required

Example:
```
csv_output_row_filter '{"accounts:used_quota_in_mb": "count>=150"}'
csv_output_row_filter "{\"accounts:used_quota_in_mb\": \"count>=150\"}"
```

## Column header filtering
Gam gives you the ability to select fields(column headers) in its print commands, but there may be cases
where you get more columns than is desirable.
* `csv_output_header_filter` - Used to select the column headers to include in the output
* `csv_output_header_drop_filter` - Used to select the column headers to exclude from the output

Typically, you would use the option that involves typing the fewest column names but both options can be used.
When both options are used, `csv_output_header_drop_filter` is processed first, then `csv_output_header_filter`.

Field names are specified by regular expressions; at its simplest, you specify a complete field name.
Field names are matched in a case insensitive manner.
```
gam config csv_output_header_filter <ColumnFieldNameFilterList> ...
gam config csv_output_header_drop_filter <ColumnFieldNameFilterList> ...
```
### Example
you want a list of user email addresses and full names; you do not need the given or family names.

No filtering.
```
gam print users name
primaryEmail,name.givenName,name.familyName,name.fullName
testuser1@domain.com,Test,User1,Test User1
testuser2@domain.com,Test,User2,Test User2
...
```
With inclusion filtering.
```
gam config csv_output_header_filter "primaryEmail,name.fullName" print users name
primaryEmail,name.fullName
testuser1@domain.com,Test User1
testuser2@domain.com,Test User2
...
```
With exclusion filtering.
```
gam config csv_output_header_drop_filter "name.givenName,name.familyName" print users name
primaryEmail,name.fullName
testuser1@domain.com,Test User1
testuser2@domain.com,Test User2
...
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
config csv_output_row_filter "'externalIds:countrange=1/10'"

primaryEmail,externalIds,externalIds.0.type,externalIds.0.value,externalIds.1.type,externalIds.1.value,...
```

### Inclusive filters
You can include rows generated by gam print commands based on column values. You specify a list
of fields (headers) and the values they must have. `csv_output_row_filter` is used to specify the 
fields and values. Each field name/expression can appear only once in the list.
```
gam config csv_output_row_filter <RowValueFilterList> ...
gam config csv_output_row_filter <RowValueFilterJSONList> ...
```

You optionally specify whether all or any value filters must match for the row to be included in the output.

* `csv_output_row_filter_mode allmatch` - All value filters must match for the row to be included in the output; this is the default
* `csv_output_row_filter_mode anymatch` - Any value filter must match for the row to be included in the output
```
gam config csv_output_row_filter_mode anymatch csv_output_row_filter <RowValueFilterList> ...
gam config csv_output_row_filter_mode anymatch csv_output_row_filter <RowValueFilterJSONList> ...
```


### Exclusive filters
You can exclude rows generated by gam print commands based on column values. You specify a list
of fields (headers) and the values they must not have. `csv_output_row_drop_filter` is used to specify the 
fields and values. Each field name/expression can appear only once in the list.
```
gam config csv_output_row_drop_filter <RowValueFilterList> ...
gam config csv_output_row_drop_filter <RowValueFilterJSONList> ...
```

You optionally specify whether all or any value filters must match for the row to be excluded from the output.

* `csv_output_row_drop_filter_mode allmatch` - If all value filters match, the row is excluded from the output
* `csv_output_row_drop_filter_mode anymatch` - If any value filter matches, the row is excluded from the output; this is the default
```
gam config csv_output_row_drop_filter_mode allmatch csv_output_row_drop_filter <RowValueFilterList> ...
gam config csv_output_row_drop_filter_mode allmatch csv_output_row_drop_filter <RowValueFilterJSONList> ...
```

### Matches
A filter matches if the field has the desired value. lf you specify a regular expression for a field name that matches
several columns, the filter matches if any of the columns has a match. In the case of `notregex|notregexcs|notdata`,
the filter matches if none (not any) of the columns has a match.

`<RowValueFilter>` allows specifying that the filter will match only if all of the columns have a match.
In the case of `notregex|notregexcs|notdata`, the filter matches if some (not all) of the columns have a match.
If neither `any` or `all` is explicitly specified, `any` is the default.

These are the row value filter types:
* `boolean:<Boolean>` - Used on fields with Boolean values; a blank field is considered False
* `count<Operator><Number>` - Used on fields with numbers; a blank field will not match
* `countrange=<Number>/<Number>` - Used on fields with numbers; a blank field will not match
  * The field value must be `>=` the left `<Number>` and `<=` the right `<Number>`
* `countrange!=<Number>/<Number>` - Used on fields with numbers; a blank field will not match
  * The field value must be `<` the left `<Number>` or `>` the right `<Number>`
* `data:<DataSelector>` - Used on fields with text; field value must match some value in `<DataSelector>`; case sensitive
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
* `notdata:<DataSelector>` - Used on fields with text; field value must not match any value in `<DataSelector>`; case sensitive
* `notregex:<RESearchPattern>` - Used on fields with text; field value must not match `<RESearchPattern>`; case insensitive
* `notregexcs:<RESearchPattern>` - Used on fields with text; field value must not match `<RESearchPattern>`; case sensitive
* `regex:<RESearchPattern>` - Used on fields with text; field value must match `<RESearchPattern>`; case insensitive
* `regexcs:<RESearchPattern>` - Used on fields with text; field value must match `<RESearchPattern>`; case sensitive
* `text<Operator><String>` - Used on fields with text
* `textrange=<String>/<String>` - Used on fields with strings
  * The field value must be `>=` the left `<String>` and `<=` the right `<String>`
* `textrange!=<String>/<String>` - Used on fields with strings
  * The field value must be `<` the left `<String>` or `>` the right `<String>`
* `time<Operator><Time>` - Used on fields with times; a blank field will not match
* `timeofdayrange=<Hour>:<Minute>/<Hour>:<Minute>` - Used on fields with times; a blank field will not match
  * The field value must be `>=` the left `<Hour>:<Minute>` and `<=` the right `<Hour>:<Minute>`
* `timeofdayrange!=<Hour>:<Minute>/<Hour>:<Minute>` - Used on fields with times; a blank field will not match
  * The field value must be `<` the left `<Hour>:<Minute>` or `>` the right `<Hour>:<Minute>`
* `timerange=<Time>/<Time>` - Used on fields with times; a blank field will not match
  * The field value must be `>=` the left `<Time>` and `<=` the right `<Time>`
* `timerange!=<Time>/<Time>` - Used on fields with times; a blank field will not match
  * The field value must be `<` the left `<Time>` or `>` the right `<Time>`

### Examples
You want a list of groups with 100 or more direct members.
```
gam config csv_output_row_filter "'directMembersCount:count>100'" print groups fields directmemberscount
```
You want a list of users created in the last 30 days.
```
gam config csv_output_row_filter "'creationTime:date>=-30d'" print users fields creationtime
```
You want a list of users in the OU /Test that are consuming more than 15GB of storage.
Special quoting is required because the field name contains a colon.
```
gam config csv_output_row_filter "'\"accounts:used_quota_in_mb\":count>15000'" report users select ou /Test fields accounts:used_quota_in_mb
```
You want the names of users directly in the OU /Test, you do not want users in any sub-OUs of /Test.
* The Google API will only supply users in an OU and sub-OUs, GAM has to filter out the users in the sub-OU.
```
gam config csv_output_row_filter "'orgUnitPath:regex:^/Test$'" print users query "orgUnitPath=/Test" fields name,ou
```
You want the names of female users directly in the OU /Test, you do not want users in any sub-OUs of /Test.
* The Google API will only supply users in an OU and sub-OUs, GAM has to filter out the users in the sub-OU.
```
gam config csv_output_row_filter "'orgUnitPath:regex:^/Test$','gender:regex:female'" print users query "orgUnitPath=/Test" fields name,ou,gender
```
You want a list of groups not created by an administrator.
```
gam config csv_output_row_filter "'adminCreated:boolean:false'" print groups fields admincreated
```
You want a list of users with phone numbers in the area code 510; the number can be in the format `(510) ddd-dddd` or `510-ddd-dddd` or `510 ddd-dddd`.
```
gam config csv_output_header_filter "primaryEmail,name.fullName,phones.*value" csv_output_row_filter "'"'phones.\\\d+.value:regex:(?:^\\\(510\\\) )|(?:^510[- ])\\\d{3}-\\\d{4}'"'" print users name phones
primaryEmail,name.fullName,phones.0.value
testuser1@domain.com,Test User1,(510) 555-1212
testuser2@domain.com,Test User2,510-555-1212
testuser3@domain.com,Test User3,510 555-1212
```
You want a list of users not in the organization cost center "Tech Support".
```
gam config csv_output_header_filter "primaryEmail,name.fullName,orgUnitPath,organizations.*costCenter" csv_output_row_filter 'organizations.*costCenter:notregex:"Tech Support"' print users fields name,ou,organizations
gam config csv_output_header_filter "primaryEmail,name.fullName,orgUnitPath,organizations.*costCenter" csv_output_row_drop_filter 'organizations.*costCenter:regex:"Tech Support"' print users fields name,ou,organizations
primaryEmail,name.fullName,orgUnitPath,organizations.0.costCenter
testuser1@domain.com,Test User1,/Test,Sales
testuser2@domain.com,Test User2,/Test,Development
```
You want a list of recurring events with at least one external guest.
```
gam config csv_output_row_filter "'^attendees$:count>1','recurrence:count>=1','attendees.*email:all:notregex:(^$)|(.+@domain.com)'" csv_output_row_drop_filter "'attendees.*email:regex:.+@resource.calendar.google.com'" redirect csv ./externalrecurringEvents.csv calendar <CalendarEntity> print events
```
## Column row limiting
You can limit the number of rows written to a CSV file.

When single processing, the limit is on the total number of rows written to the file.

When multiprocessing, the limit is on the number of rows written to the file by each subprocess.

### Examples
Display the 10 files with the largest quotaBytesUsed values for a single user.
```
gam config csv_output_row_limit 10 redirect csv ./BigQuotaFiles.csv user user@domain.com print filelist fields id,name,quotabytesused orderby quotabytesused descending
```

Display the 10 files with the largest quotaBytesUsed values for all users
```
gam config csv_output_row_limit 10 auto_batch_min 1 redirect csv ./BigQuotaFiles.csv multiprocess all users print filelist fields id,name,quotabytesused orderby quotabytesused descending
```

## Saving filters in gam.cfg
If you define a value for `csv_output_header_filter`, `csv_output_header_drop_filter`, `csv_output_header_force`, `csv_output_header_order`, `csv_output_row_filter`, `csv_output_row_drop_filter` or `csv_output_row_limit` in the `[DEFAULT]` section of `gam.cfg`,
it will apply to every `gam print` command which is probably not desirable. You can store them in `gam.cfg` in named sections.
```
[Filter510]
csv_output_header_filter = primaryEmail,name.fullName,phones.*value
csv_output_row_filter = 'phones.\\\d+.value:regex:(?:^\\\(510\\\) )|(?:^510[- ])\\\d{3}-\\\d{4}'

$ gam selectfilter Filter510 print users name phone
primaryEmail,name.fullName,phones.0.value
testuser1@domain.com,Test User1,(510) 555-1212
testuser2@domain.com,Test User2,510-555-1212
testuser3@domain.com,Test User3,510 555-1212
```

If you have multiple customers or domains in separate sections of gam.cfg, you use `select` to choose the customer/domain
and `selectfilter` to choose a filter.
```
[foo]
domain = foo.com
customer_id = C111111111
config_dir = foo

[goo]
domain = goo.com
customer_id = C222222222
config_dir = goo

[Filter510]
csv_output_header_filter = primaryEmail,name.fullName,phones.*value
csv_output_row_filter = 'phones.\\\d+.value:regex:(?:^\\\(510\\\) )|(?:^510[- ])\\\d{3}-\\\d{4}'

$ gam select foo selectfilter Filter510 print users name phone
primaryEmail,name.fullName,phones.0.value
testuser1@foo.com,Test User1,(510) 555-1212
testuser2@foo.com,Test User2,510-555-1212
testuser3@foo.com,Test User2,510 555-1212
```
