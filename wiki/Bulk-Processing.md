# Bulk Processing
- [Introduction](#introduction)
- [Python Regular Expressions](Python-Regular-Expressions)
- [GAM Configuration](gam.cfg)
- [Meta Commands and File Redirection](Meta-Commands-and-File-Redirection)
- [Definitions](#definitions)
- [Batch files](#batch-files)
- [CSV files](#csv-files)
- [CSV files with redirection and select](#csv-files-with-redirection-and-select)
- [Automatic batch processing](#automatic-batch-processing)
- [Process Google Sheet commands and save results](#process-google-sheet-commands-and-save-results)

## Introduction
Batch and CSV file processing can improve performance by executing Gam commands in parallel.
The variables `num_threads`, `num_tbatch_threads` and `auto_batch_min` in `gam.cfg` control parallelism.

## Definitions
* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
`gdoc <UserGoogleDoc>` and `gsheet <UserGoogleSheet>`

## Batch files
There are two types of batch processing, one that uses processes and one that uses threads. Using processes is higher performance but `gam csv` commands are not supported.
* `gam batch` - gam commands are run as processes, gam csv commands are not allowed in the batch file
* `gam tbatch` - gam commands are run as threads, gam csv commands are allowed in the batch file
```
gam batch <FileName>|-|(gdoc <UserGoogleDoc>) [charset <Charset>] [showcmds [<Boolean>]]
gam tbatch <FileName>|-|(gdoc <UserGoogleDoc>) [charset <Charset>] [showcmds [<Boolean>]]
```
* `<FileName>` - A flat file containing Gam commands
* `-` - Gam commands coming from stdin
* `gdoc <UserGoogleDoc>` - A Google Doc containing Gam commands
* `showcmds` - Write `timestamp,command number/number of commands,command` to stderr when each command starts; write `timestamp, command number/numberof commands,complete` to stderr when command completes

Batch files can contain the following types of lines:
* Blank lines - Ignored
* \# Comment line - Ignored
* gam \<GAMArgumentList\> - Execute a GAM command 
* commit-batch
  * GAM waits for all running GAM commands to complete
  * GAM continues
* commit-batch \<String\>
  * GAM waits for all running GAM commands to complete
  * GAM prints \<String\> and waits for the user to press any key
  * GAM continues
* sleep \<Integer\> - Batch processing will suspend for \<Integer\> seconds before the next command line is processed
  * To be effective, this should immediately follow commit-batch
* print \<String\> - Print \<String\> on stderr
* set \<KeywordString\> \<ValueString\>
  * Subsequent lines will have %\<KeywordString\>% replaced with \<ValueString\>
* clear \<KeywordString\>
  * Subsequent lines will not be scanned for %\<KeywordString\>%

Tbatch files can also contain the following line:
* execute \<Program\> \<ArgumentList\> - Execute an arbitrary command; use the full path to specify \<Program\>

### Example
* You need to create accounts for your new students and assign them to groups based on their graduation year.
* You have a CSV file NewStudents.csv with columns: Email,First,Last,GradYear,Password
* You have a batch file NewStudents.bat containing these commands:
```
gam csv NewStudents.csv gam create user "~Email" firstname "~First" lastname "~Last" org "/Students/~~GradYear~~" password "~Password"
commit-batch
gam update group seniors sync members ou /Students/2020
gam update group juniors sync members ou /Students/2021
gam update group sophomores sync members ou /Students/2022
gam update group highschool sync members ous "'/Students/2020','/Students/2021','/Students/2022'"
```
* Execute the batch file
```
gam redirect stdout ./NewStudents.out redirect stderr ./NewStudents.err tbatch NewStudents.bat showcmds
```
## CSV files
```
gam csv <FileName>|-|(gsheet <UserGoogleSheet>)|(gdoc <UserGoogleDoc>) [charset <Charset>] [warnifnodata]
        [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>] [fields <FieldNameList>]
        (matchfield|skipfield <FieldName> <RESearchPattern>)* [showcmds [<Boolean>]]
        [skiprows <Integer>] [maxrows <Integer>]
        gam <GAMArgumentList>

gam loop <FileName>|-|(gsheet <UserGoogleSheet>)|(gdoc <UserGoogleDoc>) [charset <Charset>] [warnifnodata]
        [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>] [fields <FieldNameList>]
        (matchfield|skipfield <FieldName> <RESearchPattern>)* [showcmds [<Boolean>]]
        [skiprows <Integer>] [maxrows <Integer>]
        gam <GAMArgumentList>
```
* `gam csv` - Use parallel processing
* `gam loop` - Use serial processing
* `<FileName>` - A CSV file and the one or more columns that contain data
* `-` - The one or more columns that contain data from stdin
* `gsheet <UserGoogleSheet>` - A Google Sheet and the one or more columns that contain data
* `gdoc <UserGoogleDoc>` - A Google Doc and the one or more columns that contain data
* `columndelimiter <Character>` - Columns are separated by `<Character>`; if not specified, the value of `csv_input_column_delimiter` from `gam.cfg` will be used
* `noescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `csv_input_no_escape_char` from `gam.cfg` will be used
* `quotechar <Character>` - The column quote characer is `<Character>`; if not specified, the value of `csv_input_quote_char` from `gam.cfg` will be used
* `fields <FieldNameList>` - The column headings of a CSV file that does not contain column headings.
* `(matchfield|skipfield <FieldName> <RESearchPattern>)*` - The criteria to select rows from the CSV file; can be used multiple times; if not specified, all rows are selected
* `showcmds` - Write `timestamp,command number/number of commands,command` to stderr when each command starts; write `timestamp, command number/numberof commands,complete` to stderr when command completes
* `skiprows <Integer>` - Skip filtered rows from the CSV file/Google Sheet.
  * `skiprows 0` - All rows are processed, this is the default
  * `skiprows N` - The first N filtered rows are skipped
* `maxrows <Integer>` - Limit the number of filtered rows processed from the CSV file/Google Sheet after any skipped rows.
  * `maxrows 0` - All rows are processed, this is the default
  * `maxrows N` - N filtered rows are processed

### Use CSV file values in command line
You can make substitutions in `<GAMArgumentList>` with values from the CSV file.
- Reference the field xxx with `~xxx` if the argument contains no other text
- Reference the field xxx with `~~xxx~~` if the argument contains other text
- An argument containing exactly `~xxx` is replaced by the value of field xxx
- An argument containing instances of `~~xxx~~` has `~~xxx~~` replaced by the value of field xxx
- An argument containing instances of `~~xxx~!~pattern~!~replacement~~` has `~~xxx~!~pattern~!~replacement~~` replaced by re.sub(pattern, replacement, value of field xxx) See: https://docs.python.org/3/library/re.html

If an argument is specifying a file path and it starts with a `~`, e.g., `targetfolder "~/Documents/GamWork"`, GAM will flag it as an error:
```
ERROR: Header "/Documents/GamWork/" not found in CSV headers of "Owner,id,title".
```
Put a space in front of the `~`: `targetfolder " ~/Documents/GamWork"` to avoid the error.

### Example
* You need to update the work addresses of a set of users
* You want a note field that shows their email address as name AT domain.com
* You have a CSV file Users.csv with columns: primaryEmail,Street,City,State,ZIP
```
gam csv Users.csv gam update user "~primaryEmail" address type work unstructured "~~Street~~, ~~City~~, ~~State~~ ~~ZIP~~" primary note text_plain "~~primaryEmail~!~^(.+)@(.+)$~!~\1 AT \2~~"
```
* You want to do the above using a Google Sheet
```
gam csv gsheet <user> <fileID> "<sheetName>" gam update user "~primaryEmail" address type work unstructured "~~Street~~, ~~City~~, ~~State~~ ~~ZIP~~" primary note text_plain "~~primaryEmail~!~^(.+)@(.+)$~!~\1 AT \2~~"
```

## CSV files with redirection and select
You should use the `multiprocess` option on any redirected files: `csv`, `stdout`, `stderr`.
```
gam redirect csv ./filelistperms.csv multiprocess csv Users.csv gam user "~primaryEmail" print filelist fields id,name,mimetype,basicpermissions
gam redirect csv - multiprocess todrive csv Users.csv gam user "~primaryEmail" print filelist fields id,name,mimetype,basicpermissions
```

If you want to select a `gam.cfg` section for the command, you can select the section at the outer `gam` and save it
or select the section at the inner `gam`.
```
gam select <Section> save redirect csv ./filelistperms.csv multiprocess csv Users.csv gam user "~primaryEmail" print filelist fields id,name,mimetype,basicpermissions
gam redirect csv ./filelistperms.csv multiprocess csv Users.csv gam select <Section> user "~primaryEmail" print filelist fields id,name,mimetype,basicpermissions
gam select <Section> save redirect csv - multiprocess todrive csv Users.csv gam user "~primaryEmail" print filelist fields id,name,mimetype,basicpermissions
gam redirect csv - multiprocess todrive csv Users.csv gam select <Section> user "~primaryEmail" print filelist fields id,name,mimetype,basicpermissions
```

## Automatic batch processing
You can enable automatic batch (parallel) processing when issuing commands of the form `gam <UserTypeEntity> ...`.
In the following example, if the number of users in group sales@domain.com exceeds 1, then the `print filelist` command will be processed in parallel.
```
gam config auto_batch_min 1 redirect csv ./filelistperms.csv multiprocess group sales@domain.com print filelist fields id,name,mimetype,basicpermissions
gam config auto_batch_min 1 redirect csv - multiprocess todrive group sales@domain.com print filelist fields id,name,mimetype,basicpermissions
```
With automatic batch processing, you should use the `multiprocess` option on any redirected files: `csv`, `stdout`, `stderr`.

If you want to select a `gam.cfg` section for the command, you must select and save it for it to be processed correctly.
```
gam select <Section> save config auto_batch_min 1 redirect csv ./filelistperms.csv multiprocess group sales@domain.com print filelist fields id,name,mimetype,basicpermissions
```

## Process Google Sheet commands and save results
You want to process data from a Google Sheet tab and save the results to another tab in the same sheet.
Make a Google sheet with two tabs: Commands, Results; get the File ID and the two tab IDs.
Put your command data in the Commands tab.

Run your command, write the results to Results.txt
```
gam redirect stdout ./Results.txt multiprocess redirect stderr stdout csv gsheet user@domain.com <FileID> id:<CommandsTabID> gam ... Command
```

Upload Results.txt to the Results tab of the sheet.
```
gam user user@domain.com update drivefile <FileID> localfile Results.txt retainname gsheet id:<ResultsTabID>
```
