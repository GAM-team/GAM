- [Managing CloudPrint Printers](#managing-cloudprint-printers)
  - [Updating A Printer](#updating-a-printer)
  - [Getting Printer Info](#getting-printer-info)
  - [Deleting A Printer](#deleting-a-printer)
  - [Reporting Printers](#reporting-printers)
- [Sharing CloudPrint Printers](#sharing-cloudprint-printers)
  - [Sharing A Printer](#sharing-a-printer)
  - [Unsharing A Printer](#unsharing-a-printer)
  - [Showing Printer ACLs](#showing-printer-acls)
- [Managing CloudPrint Print Jobs](#managing-cloudprint-print-jobs)
  - [Submitting A Print Job](#submitting-a-print-job)
  - [Cancelling A Print Job](#cancelling-a-print-job)
  - [Deleting A Print Job](#deleting-a-print-job)
  - [Reporting Print Jobs](#reporting-print-jobs)

# Managing CloudPrint Printers
## Updating A Printer
### Syntax
```
gam update printer <id> [quotaEnabled <true|false>] [dailyQuota <number>] [public <true|false> [name <name>] [proxy <proxy>] [description <description>]
```
Updates the given printer. The optional parameter quotaEnabled enables or disables a daily quota for users using the printer. The optional parameter dailyQuota sets the number of pages users can print a day when quotaEnabled is true. The optional parameter public sets the printer to be accessible to anyone who knows the printer's URL when true. The optional parameters name and description adjust the name and description of the printer. The optional parameter proxy adjusts the proxy id for the printer (dangerous).

### Example
This example makes the printer public and sets a 5 pages a day quota.
```
gam update printer 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 public true quotaEnabled true dailyQuota 5
```
----

## Getting Printer Info
### Syntax
```
gam info printer <id> [everything]
```
Gets detailed information about the given CloudPrint printer. The optional everything argument includes even more printer detail.

### Example
This example prints details about the given printer.
```
gam info printer  __google__docs
status: 
isTosAccepted: False
updateTime: 2013-06-03 15:22:04
displayName: Save to Google Drive
description: Save your document as a PDF in Google Drive
name: Save to Google Docs
tags: save docs pdf google __google__drive_enabled
defaultDisplayName: Save to Google Drive
accessTime: 2011-09-15 20:14:01
id: __google__docs
ownerName: Cloud Print
capsHash: 
ownerId: cloudprinting@gmail.com
type: DRIVE
createTime: 2011-07-22 17:00:03
proxy: google-wide
```
----

## Deleting A Printer
### Syntax
```
gam delete printer <id>
```
Deletes the given printer. Be aware that depending on your printer / print proxy, the printer may be recreated soon after it's deleted. You should make sure your printer or print proxy is no longer registering the printer either.

### Example
This example deletes the printer that has ID 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53
```
gam delete printer 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53
```
----

## Reporting Printers
### Syntax
```
gam print printers [query <query>] [type <type>] [status <status>] [extrafields <connectionStatus|semanticState|uiState|queuedJobsCount>] [todrive]
```
CSV output of printers owned or accessible by the user GAM is running as. The optional parameter query limits results to printers that have a title or tag matching the search value. The optional parameter type limits results to printers of the given type. The optional parameter status limits results to printers with the given status. The optional parameter extrafields includes the given extra CSV fields in the result but may significantly slow the performance of the print command. The optional parameter todrive creates a Google Drive Spreadsheet of the results rather than outputting CSV to the console.

### Examples
This example prints all printers accessible by the user.
```
gam print printers
```
this example prints all printers with a name or tag like "HP".
```
gam print printers query HP
```
----

# Sharing CloudPrint Printers
## Sharing A Printer
### Syntax
```
gam printer <id> add USER|MANAGER <group or user email>
```
Share the given printer with the given Google user or group. A USER is able to print to the printer. A MANAGER is able to print to the printer as well as share the printer with additional users/groups. If the printer owner is not an owner of the Google Group, an owner of the group will need to manually accept the printer on the group's behalf.

Note, to make a printer public, use the update printer command above.

### Examples
This example shares the printer with the group students@acme.edu.
```
gam printer 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 add USER students@acme.edu
```
this example gives helpdesk@acme.edu manager access to the printer.
```
gam printer 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 add MANAGER helpdesk@acme.edu
```
----

## Unsharing CloudPrint Printers
### Syntax
```
gam printer <id> remove <group or user email>
```
Remove access to the given printer for the given user or group.

### Example
This example revokes student access to the printer.
```
gam printer 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 remove students@acme.edu
```
----

## Showing Printer ACLs
### Syntax
```
gam printer <id> showacl
```
Shows the current ACLs of the given printer. If the printer is shared publicly, then a URL will be returned by which any user can access the printer.

### Example
This example prints the ACLs for the printer.
```
gam printer 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 showacl
```
----

# Managing CloudPrint Print Jobs
## Submitting A Print Job
### Syntax
```
gam printjob <printer id> submit <file or url>
```
Submits a file or URL to be sent to the given CloudPrint printer. If the value begins with http:// or https:// it is assumed to be a web URL and the page is retrieved for printing, otherwise it's assumed to be a local file. Generally PDF, JPG and GIF images print successfully but other formats like Microsoft Office may also work (with somewhat limited conversion success).

Please be aware that this command is primarily meant for testing and troubleshooting of CloudPrint. GAM does not currently support setting print options like color/bw, copies, pages, etc.

### Examples
This example prints the current homepage for Google.
```
gam printjob 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 submit http://www.google.com
```
this example prints a PDF file.
```
gam printjob 86bee4bb-c43e-8fd4-f06e-e7b8564a1c53 submit c:\docs\findings.pdf
```
----

## Cancelling A Print Job
### Syntax
```
gam printjob <id> cancel
```
Cancels the given print job. Note that the job remains visible in the CloudPrint UI with a cancelled status but the printer should not try to print the job.

Note: While cancelled print jobs will not be printed by the CloudPrint printer, the print job data may remain on Google's servers for up to 30 days before expiring.

### Examples
This example cancels a print job.
```
gam printjob 21fc3546-8fbc-f185-acea-2b28e3ffaba3 cancel
```
This complex example retrieves all print jobs that are either owned by the GAM admin or are sent to printers owned by the GAM admin and have remained in a QUEUED status for more than hour. It then cancels all of the jobs.

This example could be run on a regular basis to make sure that print jobs older than an hour are cancelled while a printer or printer proxy is down / backed up.
```
gam print printjobs status QUEUED older_than 1h | gam csv - gam printjob ~id cancel
```
----

## Deleting A Print Job
### Syntax
```
gam printjob <id> delete
```
Deletes the given print job. The print job will no longer be printed (if it hasn't been already) and no data or metadata for the print job should remain.

### Example
This example deletes the print job.
```
gam printjob 21fc3546-8fbc-f185-acea-2b28e3ffaba3 delete
```
----

## Reporting Print Jobs
### Syntax
```
gam print printjobs [older_than <number><m|h|d>] [newer_than <number><m|h|d>] [query <query>] [status <status>] [printer <printer id>]  [owner <user email>] [limit <Number>] [todrive]
```
Provides a CSV output of all print jobs. The optional arguments `older_than` and `newer_than` limit results to print jobs created in the given time. The optional `query` argument limits results to jobs whose title or tags match the given query. The optional `status` argument limits the results to jobs whose status is provided. The optional `printer` argument limits results to jobs sent to the given printer id. The optional `owner` argument limits results to jobs sent by the given user. The optional `limit <Number>` argument limits the number of jobs output to `<Number>`; the default value for `<Number>` is 25, set `<Number>` to 0 for no limit. The optional `todrive` argument creates a Google Drive Spreadsheet of the results rather than sending CSV output to the console.

### Examples
This example prints all print jobs owned by the GAM admin or sent to a printer owned by the GAM admin.
```
gam print printjobs
```
this example creates a Google Drive Spreadsheet of all print jobs with status DONE.
```
gam print printjobs status DONE todrive
```
this complex example deletes print jobs still in a QUEUED status after 1 day.
```
gam print printjobs status QUEUED older_than 1d | gam csv - gam printjob ~id delete
```
----