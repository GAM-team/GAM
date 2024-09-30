# Upgrade Benefits
- [Configuration](#Configuration)
- [Syntax Checking](#syntax-checking)
- [API error checking](#api-error-checking)
- [Batch files](#batch-files)
- [CSV processing redirects](#csv-processing-redirects)
- [Data selection](#data-selection)
- [Specifying Google Drive files](#specifying-google-drive-files)
- [Uploading CSV files from gam print commands to Google Drive](#uploading-csv-files-from-gam-print-commands-to-google-drive)
- [Calendars](#calendars)
- [Contacts](#contacts)
- [Courses](#courses)
- [Data Studio](#data-studio)
- [Drive File Copy and Move](#drive-file-copy-and-move)
- [Drive File Orphans](#drive-file-orphans)
- [Drive File Ownership](#drive-file-ownership)
- [Drive File Revisions](#drive-file-revisions)
- [Drive File Transfer](#drive-file-transfer)
- [Send email messages](#send-email-messages)
- [Forms](#forms)
- [Gmail](#gmail)
- [Groups](#groups)
- [Keep](#keep)
- [Organizational Units](#organizational-units)
- [Resource Calendars](#resource-calendars)
- [Shared Drives](#shared-drives)
- [Spreadsheets](#Spreadsheets)
- [Tasks](#tasks)

## Configuration

GAM7 uses a configuration file, gam.cfg, to store the values of the various environment variables
and signal files used by earlier versions of GAM. Configuration files client_secrets.json, oauth2.txt, oauth2service.json and extra_args.txt
are moved to a version independent location. This should simplify upgrading GAM versions in the future.
Additionally, if you support multiple clients/domains or have multiple users running GAM,
gam.cfg lets you easily manage your configuration.

See: [gam.cfg](gam.cfg)

## Syntax Checking

GAM7 produces better error messages when syntax errors are found on the command line.

## API error checking

In GAM, most API calls are made without error handling; if an API call fails for a particular item and the command
was an operation on multiple items, the items after the failing item are not processed. The GAM solution is to have
you produce a CSV file containing the items you want to process; as each item is an independent excution, API failures for some items
do not affect other items. Capturing meaningful output from the CSV execution is hard and you have to create the CSV file as a separate step.

In GAM7, every API call is made with error handling; if an API call fails, a message is output and execution continues with additional items if possible.

## Batch files

GAM uses multiprocessing for processing batch files and CSV files; this offers better performance than using threads. Unfortunately, one
multiprocess subprocess can not create another subprocess; this prevents using gam csv commands inside GAM batch files.

GAM7 supports two commands for processing batch files, batch and tbatch. gam batch uses multiprocessing and gam tbatch uses threads.
If you have a batch file that contains gam csv commands, gam tbatch can successfuly process the batch file.

See: [Bulk Processing](Bulk-Processing)

## CSV processing redirects

With GAM, if you want to process a CSV file and capture the output, you do one of the following:
```
gam csv File.csv gam <Command> > File.out 2> File.err
gam csv File.csv gam <Command> > File.out 2>&1
```
Multiple processes are writing to File.out(.err) simultaneously resulting in interleaved output that can be hard to read.

With GAM7, you can capture the output from the multiple processes such that all of the output from each process is contiguous.
```
gam redirect stdout ./File.out multiprocess redirect stderr ./File.err multiprocess csv File.csv gam <Command>
gam redirect stdout ./File.out multiprocess redirect stderr stderr csv File.csv gam <Command>
```

You can choose to have GAM7 bracket the output from each process with lines that show the command being executed.
```
gam config show_multiprocess_info true redirect stdout ./File.out multiprocess redirect stderr ./File.err multiprocess csv File.csv gam <Command>
gam config show_multiprocess_info true redirect stdout ./File.out multiprocess redirect stderr stderr csv File.csv gam <Command>
```

See: [Meta Commands and File Redirection](Meta-Commands-and-File-Redirection)

## Data selection

GAM7 has many more ways to specify collections of ChromeOS devices, Users and other items.

See: [Collections of ChromeOS Devices](Collections-of-ChromeOS-Devices)

See: [Collections of Users](Collections-of-Users)

See: [Collections of Items](Collections-of-Items)

## Specifying Google Drive files

GAM specifies drive files in different ways based on the command.

GAM7 has a consistent way of specifying Google Drive files for all commands.

See: [Drive File Selection](Drive-File-Selection)

## Uploading CSV files from gam print commands to Google Drive

GAM allows no options when you use the todrive option with a gam print command; the file is always uploaded with a fixed name to the root folder of
Google Drive for the Google Admin user named in oauth2.txt.

GAM7 allows you to specify the name, location and user for files uploaded with todrive; you can also save a local copy of the file.

See: [Todrive](Todrive)

## Calendars

GAM can manage the list of calendars a user can view; GAM7 can also create, modify and remove calendars.

GAM can add and delete events; GAM7 can also update, move, show and print events.

GAM can add, update, delete and show calendar ACLs; GAM7 can also get ACLs for a single calendar and print a CSV file of calendar ACLs.

See: [Calendars - Access](Calendars-Access), [Calendars - Events](Calendars-Events)

See: [Users - Calendars - List](Users-Calendars-List)

See: [Users - Calendars](Users-Calendars)

See: [Users - Calendars - Events](Users-Calendars-Events)

See: [Users - Calendars - Transfer](Users-Calendars-Transfer)

## Contacts

GAM7 supports domain shared contacts and user contacts.

See: [Domain Shared Contacts](Contacts)

See: [Users - People - Contacts & Profiles](Users-People-Contacts-Profiles)

## Courses

When updating a course, GAM can only add/delete a single alias; GAM7 can add/delete multiple aliases.

When updating a course's membership, GAM can only add/delete a single student/teacher; GAM7 can
add/delete multiple students/teachers.

When creating/updating courses, GAM7 can copy settings from another course.

See: [Courses](Courses)

## Data Studio

GAM7 supports commands to display Data Studio assets and display/manage Data Studio permissions

See: [Users - Data Studio](Users-DataStudio)

## Drive File Copy and Move

GAM7 supports advanced file/folder copying/moving

See: [Users - Drive - Copy/Move](Users-Drive-Copy-Move)

## Drive File Orphans

GAM7 allows collecting a user's orphaned files.

See: [Users - Drive - Orphans](Users-Drive-Orphans)

## Drive File Ownership

GAM7 allows transferring ownership of selected folders of a source user to a target user.

GAM7 allows claiming ownership of of selected folders to which the user has access.

See: [Users - Drive - Ownership](Users-Drive-Ownership)

## Drive File Revisions

GAM7 can manage drive file revisions.

## Drive File Transfer

GAM7 has more capabilites for transferring the Google Drive of a source user to a target user.

See: [Users - Drive - Transfer](Users-Drive-Transfer)

See: [Users - Drive - Revisions](Users-Drive-Revisions)

## Send email messages

GAM7 can send email messages.

See: [Send Email](Send-Email)

## Forms

GAM7 supports commands to manage and display Google Forms.

See: [Users - Forms](Users-Forms)

## Gmail

GAM7 has commands for displaying Gmail messages.

GAM7 has commands for forwarding Gmail messages.

See: [Users - Gmail - Messages/Threads](Users-Gmail-Messages-Threads)

## Groups

GAM7 allows selecting fields with `info group`. The output is much easier to read.

When creating/updating groups, GAM7 can copy settings from another group.

See: [Groups](Groups)

GAM7 has a more powerful `print group-members` command.

GAM7 has a more powerful ways of specifying changes to group membership.

See: [Groups Membership](Groups-Membership)

GAM7 has commands to display/manage a user's group membership.

See: [Users - Group Membership](Users-Group-Membership)

## Keep

GAM7 supports commands to manage and display Google Keep notes.

See: [Users - Keep](Users-Keep)

## Organizational Units

GAM7 supports updating multiple org units in a single command.

See: [Organizational Units](Organizational-Units)

## Resource Calendars

GAM7 supports managing resource calendar ACLs.

See: [Resource Calendars](Resource-Calendars)

## Shared Drives

GAM7 has more powerful commands for managing Shared Drives.

See: [Shared Drives](Shared-Drives)

See: [Users - Shared Drives](Users-Shared-Drives)

## Spreadsheets

GAM7 can manipulate Google Sheets.

See: [Users - Spreadsheets](Users-Spreadsheets)

## Tasks

GAM7 supports commands to manage and display Google Tasks.

See: [Users - Tasks](Users-Tasks)
