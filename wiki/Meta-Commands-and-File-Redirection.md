# Meta Commands and File Redirection

- [GAM Configuration](gam.cfg)
- [Todrive](Todrive)
- [Introduction](#introduction)
- [Meta Commands](#meta-commands)
  - [Select section](#select-section)
  - [Display sections](#display-sections)
  - [Select output filter section](#select-output-filter-section)
  - [Select input filter section](#select-input-filter-section)
  - [Set configuration variables](#set-configuration-variables)
  - [Specify multiprocessing termination return code](#specify-multiprocessing-termination-return-code)
- [File Redirection](#file-redirection)

## Introduction

Meta commands are used to configure GAM operation. File redirection is used to intelligently redirect output from GAM: CSV data, stdout and stderr.

The meta commands and file redirection must come before all other arguments and in this order,  ... indicates that additional GAM arguments may appear.
```
gam [<Select>] [showsections] [<SelectOutputFilter>|<SelectInputFilter>] [<Config>] [<MultiprocessExit>] [<Redirect>] ...
```

## Meta Commands

### Select section
Select a section from gam.cfg and process a GAM command using values from that section.
```
<Select> ::=
        select <Section> [save] [verify]
```
- `save`
  - Set `section = <Section>` in the `[DEFAULT]` section and write configuration data to gam.cfg
- `verify`
  - Print the variable values for the selected section
  - Values are determined in this order: Selected section, DEFAULT section, Program default

### Display sections
Display all of the sections in gam.cfg and mark the currently selected section with a *.
```
showsections
```

### Select output filter section
Select an output filter section from gam.cfg and process a GAM command using values from that section.
```
<SelectOutputFilter> ::=
        selectfilter|selectoutputfilter <Section>
```
The only `<VariableNames>` recognized in this `<Section>` are:
* `csv_output_header_filter`
* `csv_output_header_drop_filter`
* `csv_output_header_force`
* `csv_output_header_order`
* `csv_output_row_filter`
* `csv_output_row_filter_mode`
* `csv_output_row_drop_filter`
* `csv_output_row_drop_filter_mode`
* `csv_output_row_limit`
* `csv_output_sort_headers`

### Select input filter section
Select an input filter section from gam.cfg and process a GAM command using values from that section.
```
<SelectInputFilter> ::=
        selectinputfilter <Section>
```
The only `<VariableNames>` recognized in this `<Section>` are:
* `csv_input_row_filter`
* `csv_input_row_filter_mode`
* `csv_input_row_drop_filter`
* `csv_input_row_drop_filter_mode`
* `csv_input_row_limit`

### Set configuration variables
Set variables in gam.cfg.

```
<Config> ::=
        config (<VariableName> [=] <Value>)* [save] [verify]
```
- `<VariableName> [=] <Value>`
  - Set `<VariableName> = <Value>` in the current section
  - All `<VariableNames>` except section are allowed.
  - The `=` is optional but must be surrounded by spaces if included.
- `save`
  - Write configuration data to gam.cfg
- `verify`
  - Print the variable values for the current section
  - Values are determined in this order: Current section, DEFAULT section, Program default

You can prefix `<Config>` with `<Select>` to set a variable in a particular section.
* `select default <Config>` - Set a variable in the `DEFAULT` section
* `select xyz <Config>` - Set a variable in the `xyz` section

### Specify multiprocessing termination return code
Terminate processing of a CSV or batch file when one of the subprocesses returns a matching return code.
```
<Operator> ::= <|<=|>=|>|=|!=

<ReturnCodeSelection> ::=
        rc<Operator><Number>|
        rcrange=<Number>/<Number>|
        rcrange!=<Number>/<Number>

<MultiProcessExit> :=
        multiprocessexit <ReturnCodeSelection>
```

## File Redirection
You can redirect CSV file output and stdout/stderr output to files. By using redirect, you have more control over the output from GAM.

You can redirect stdout and stderr to null and stderr can be redirected to stdout.
```
<Redirect> ::=
        redirect csv <FileName> [multiprocess] [append] [noheader] [charset <Charset>]
                     [columndelimiter <Character>] [quotechar <Character>] [noescapechar [<Boolean>]]
                     [sortheaders <StringList>] [timestampcolumn <String>] [transpose [<Boolean>]]
                     [todrive <ToDriveAttribute>*] |
        redirect stdout <FileName> [multiprocess] [append] |
        redirect stdout null [multiprocess] |
        redirect stderr <FileName> [multiprocess] [append] |
        redirect stderr null [multiprocess] |
        redirect stderr stdout [multiprocess]
```
For `redirect`, the optional subarguments must appear in the order shown.

If `<FileName>` specifies a relative path, the file will be put in the directory specified by `drive_dir` in gam.cfg.
If `<FileName>` specifies an absolute path, the file will be put in the directory specified.
Specify `./<FileName>` to put the file in your current working directory.

The `multiprocess` subargument allows the multiple subprocesses started by `gam csv` to write intelligently
to a single redirected CSV/stdout/stderr file. If you don't specify `multiprocess`, each subprocess
writes `<FileName>` independently; you end up with a single file written by the last subprocess.
For `redirect csv`, if you don't specify `multiprocess` and do specify `todrive`, each subprocess uploads a separate Google sheet.

The `append` subargument causes GAM to append data to `<FileName>` rather that rewriting the file.

The `noheader` subargument causes GAM to suppress writing a CSV file header. This might be used when you are running
several GAM commands that output the same CSV columns but want all of the data in a single file; the second and
subsequent GAM commands specify `append noheader`.

The `charset <Charset>` subargument sets the character set of the CSV file; the default is the value of `charset`
in `gam.cfg` which defaults to UTF-8.

The `columndelimiter <Character>` subargument sets the intercolumn delimiter of the CSV file; the default value
is the value of `csv_output_column_delimiter` in `gam.cfg` which defaults to comma.

The `quotechar <Character>` subargument sets the character used to quote fields in the CSV file
that contain special charactere; the default value is the value of `csv_output_quote_char` in `gam.cfg`
which defaults to double quote.

The `noescapechar <Boolean>` subargument controls whether `\` is used as an escape character when writing the CSV file; the default value
is the value of `csv_output_no_escape_char` in `gam.cfg` which defaults to False.

The `sortheaders <StringList>` argument causes GAM to sort CSV output rows by the column headers specified in `<StringList>`.
The column headers are case insensitive and if column header does not appear in the CSV output, it is ignored.

The `timestampcolumn <String>` adds a column named `<String>` to the CSV file; the value is the
timestamp of when the GAM command started.

The `transpose <Boolean>` subargument controls whether GAM transposes CSV output rows and columns. This will most useful
when a `countsonly` option is used in a `print` or `report` command. When not specified, the value is False, there is no transposition.

If you are doing `redirect csv <FileName> multiprocess`, it is more efficient to specify `todrive <ToDriveAttribute>*` as part of
the redirect as verification of the `todrive` settings, which can involve several API calls, is done once rather than in each of the subprocesses.

By setting `<FileName>` to `-`, you can redirect to stdout/stderr rather than a file; this is typically used when `multiprocess` is specified.
* `redirect csv - multiprocess` - Send CSV output to stdout; intelligently aggregate data by process
* `redirect stdout - multiprocess` - Send normal output stdout; intelligently aggregate data by process
* `redirect stderr - multiprocess` - Send `getting` messages and error messages to stderr; intelligently aggregate data by process

If the pattern `{{Section}}` appears in `<FileName>`, it will be replaced with the name of the current section of gam.cfg.

### Examples - redirect CSV
Suppose that you have a CSV file CourseList.csv with a column labeled CourseId that contains course Ids. You want a single CSV file with participant information for these courses.
```
gam redirect csv ./CourseInfo.csv multiprocess csv CourseList.csv gam print course-participants course "~CourseId"
```
`redirect csv ./CourseInfo.csv multiprocess` causes gam to collect output from all of the processes started by `csv CourseList.csv gam print course-participants course "~CourseId"` and produces a single CSV file CourseInfo.csv.

Generate a list of CrOS devices and update an existing sheet in a Google spreadsheet. The file ID and sheet IDs are preserved so other appplications can access the data using the file ID and sheet ID.
By setting 'tdtimestamp true`, the file name will the updated to reflect the time of execution, but the file ID will not change.
```
gam redirect csv - todrive tdtitle "CrOS" tdtimestamp true tdfileid 12345-mizZ6Q2vP1rcHQH3tAZQt_NVB2EOxmS2SU3yM tdsheet id:0 tdupdatesheet true print cros fields deviceId,notes,orgUnitPath,serialNumber,osversion
```

For a collection of users, generate a list of files shared with anyone; combine the output for all users into a single file.
```
gam redirect csv - multiprocess todrive tdtitle AnyoneShares-All csv Users.csv gam user "~primaryEmail" print filelist fields id,name,permissions pm type anyone em
```

For a collection of users, generate a list of files shared with anyone; generate a separate file for each user.
The two forms of the command are equivalent.
```
gam csv Users.csv gam redirect csv - todrive tdtitle "AnyoneShares-~~primaryEmail~~" user "~primaryEmail" print filelist fields id,name,permissions pm type anyone em

gam csv Users.csv gam user "~primaryEmail" print filelist fields id,name,permissions pm type anyone em todrive tdtitle "AnyoneShares-~~primaryEmail~~" 
```

### Examples - Redirect stdout
The output from each of the `gam info user "~primaryEmail"` commands will be combined into the single file Users.txt.
The value of `show_multiprocess_info` from `gam.cfg` controls whether information identifying the processes is also shown.

```
$ gam config show_multiprocess_info false redirect stdout ./Users.txt multiprocess csv Users.csv gam info user "~primaryEmail"
$ more Users.txt
User: testuser1@domain.com (1/1)
  Settings:
    First Name: Test
    Last Name: User1
    Full Name: Test User1
...
User: testuser2@domain.com@ (1/1)
  Settings:
    First Name: Test
    Last Name: User2
    Full Name: Test User2
...

$ gam config show_multiprocess_info true redirect stdout ./Users.txt multiprocess csv Users.csv gam info user "~primaryEmail"
$ more Users.txt
stdout:      0, Start: 2017-01-26T11:35:00.897773-08:00, RC:   0, Cmd: /Users/admin/gam config show_multiprocess_info true redirect stdout ./Users.txt multiprocess csv Users.csv gam info user "~primaryEmail"
stdout:      1, Start: 2017-01-26T11:35:00.902709-08:00, RC:   0, Cmd: gam info user testuser1@domain.com
User: testuser1@domain.com (1/1)
  Settings:
    First Name: Test
    Last Name: User1
    Full Name: Test User1
...
stdout:      1,   End: 2017-01-26T11:35:02.656837-08:00, RC:   0, Cmd: gam info user testuser1@domain.com
stdout:      2, Start: 2017-01-26T11:35:00.910729-08:00, RC:   0, Cmd: gam info user testuser2@domain.com
User: testuser2@domain.com@ (1/1)
  Settings:
    First Name: Test
    Last Name: User2
    Full Name: Test User2
...
stdout:      2,   End: 2017-01-26T11:35:02.849646-08:00, RC:   0, Cmd: gam info user testuser2@domain.com
stdout:      0,   End: 2017-01-26T11:35:02.907141-08:00, RC:   0, Cmd: /Users/admin/gam config show_multiprocess_info true redirect stdout ./Users.txt multiprocess csv Users.csv gam info user "~primaryEmail"
```
