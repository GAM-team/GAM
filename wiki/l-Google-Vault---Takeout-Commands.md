- [Vault Matters](#vault-matters)
  - [Creating Matters](#creating-matters)
  - [Updating Matters](#updating-matters)
  - [Getting Info About A Matter](#getting-info-about-a-matter)
  - [Deleting Matters](#deleting-matters)
  - [Printing Matters](#printing-matters)
- [Vault Holds](#vault-holds)
  - [Creating Holds](#creating-holds)
  - [Updating Holds](#updating-holds)
  - [Deleting Holds](#deleting-holds)
  - [Getting Info About A Hold](#getting-info-about-a-hold)
  - [Printing Holds](#printing-holds)
- [Vault Exports](#vault-exports)
  - [Creating Exports](#creating-exports)
  - [Getting Info About An Export](#getting-info-about-an-export)
  - [Downloading An Export](#downloading-an-export)
  - [Copying An Export](#copying-an-export)
- [Vault Counts](#vault-counts)
  - [Get Item Counts](#get-item-counts)
- [Takeout](#takeout)
  - [Copying a Bucket](#copying-a-bucket)
  - [Downloading a Bucket](#downloading-a-bucket)

# Vault Matters
## Creating Matters
### Syntax
```
gam create vaultmatter [name <name>] [description <description>] [collaborators <emails>]
```
Creates a [Google Vault Matter](https://support.google.com/vault/answer/2462419). The optional argument name specifies a name for the matter, if no name is specified the matter will be named "New Matter - YYYY-MM-DD hh:mm:ss". The optional argument description specifies additional details about the matter. The optional argument collaborators allows other users to manage the matter. Collaborator email addresses should be separated by commas.

### Example
This example creates a new matter regarding rgeller's sandwich
```
gam create vaultmatter name "My Sandwich" description "Concerning the 9/3/17 investigation of rgeller's sandwich"
```
----

## Updating Matters
### Syntax
```
gam update vaultmatter <nameOrId> [name <name>] [description <description>] [addcollaborators <emails>] [removecollaborators <emails>] [action close|reopen|delete|undelete]
```
Updates the given matter. nameOrId should be the matter's name or unique ID prefixed with "uid:". The optional arguments name and description specify a new name and/or description for the matter. The optional arguments addcollaborators and removecollaborators specify comma separated lists of users to add/remove from the matter management. The optional argument action specifies an action to take on the matter (close, reopen, delete, undelete).

### Example
This example updates the sandwich matter.
```
gam update vaultmatter "My Sandwich" addcollaborators "cbing@acme.com,joeyt@acme.com"
```
----

## Getting Info About a Matter
### Syntax
```
gam info vaultmatter <nameOrId>
```
Retrieves information about the vaultmatter specified by nameOrId. If the matter unique ID is specified it should be prefixed by "uid:".

### Example
This example shows details about the "My Sandwich" matter.
```
gam info matter "My Sandwich"
matterId: 3ce96012-4598-4bc6-96c5-603a47420965
 matterPermissions: 
   role: OWNER
   email: rgeller@acme.com
   accountId: 101937355872607653089
 state: OPEN
 name: My Sandwich
 description: Concerning the 9/3/17 investigation of rgeller's sandwich
```
----

## Deleting Matters
### Syntax
See [Updating Matters](#updating-matters) and [Google's help article](https://support.google.com/vault/answer/2462419). Matters must be closed before they can be deleted.

### Example
This example closes a matter and then deletes it. Note that you may prefer to just keep matters closed rather than deleting them.
```
gam update matter "My Sandwich" action close
gam update matter "My Sandwich" action delete
```
----

## Printing Matters
### Syntax
```
gam print vaultmatters [todrive] [basic]
```
Outputs a CSV list of Vault Matters. The optional argument todrive specifies that a Google Spreadsheet should be created instead of outputting the CSV data. The optional argument basic specifies that less details (like collaborators) should be included in the output.

### Example
This example creates a Google Spreadsheet with basic information about all matters
```
gam print vaultmatters todrive basic
```
----

# Vault Holds
## Creating Holds
### Syntax
```
gam create vaulthold <matter nameOrId> [name <name>] [corpus mail|drive|groups] [query <query>] [accounts <emails>] [orgunit <orgunit>] [starttime YYYY-MM-DD] [endtime YYYY-MM-DD]
```
Creates a [Vault Hold](https://support.google.com/vault/answer/2473591). The required argument matter specifies the name or ID (prefixed with "uid:") of the matter with which the hold will be associated. The argument name specifies a name for the Vault Hold. The required argument corpus specifies the corpus of data for which the hold will apply and can be one of mail, drive or groups. The optional argument query specifies a query that will determine which data is held. If corpus type is drive, the only valid query is the string '{"includeTeamDriveFiles": true}'. If corpus type is gmail or groups, query should be a [valid search string](https://support.google.com/vault/answer/2474474). The optional arguments accounts and orgunit are mutually exclusive (you can't create a hold that covers both specific accounts and an orgunit). Accounts should be separated by commas. The optional arguments starttime and endtime specify the start/end date of the held data.

### Example
This example creates a hold of all Student Drive data
```
gam create vaulthold matter "My Sandwich" name "Hold All Student Drive Files" corpus drive query '{"includeTeamDriveFiles": true}' orgunit "/Students"
```
----

## Updating Holds
### Syntax
```
gam update hold <HoldNameOrId> <matter <MatterNameOrId>> [query <query>] [orgunit <orgunit>] [addaccounts <emails>] [removeaccounts <emails>] [starttime YYYY-MM-DD] [endtime YYYY-MM-DD]
```
Updates the specified Hold. The required argument matter specifies the matter which the hold is associated with. The optional argument query updates the query terms of the hold. The optional arguments orgunit, addaccounts and removeaccounts specify updates to the hold's orgunit or accounts. Once a matter is created, it cannot be changed from orgunit to accounts but you can change the orgunit or accounts being held. The optional arguments starttime and endtime specify new dates for the hold.

### Example
This example updates the hold for all student drive data to only cover drive data between the given dates.
```
gam update vaulthold "Hold All Student Drive Files" matter "My Sandwich" starttime 2017-01-01 endtime 2017-08-13
```
----

## Deleting Holds
### Syntax
```
gam delete vaulthold <HoldNameOrId> matter <MatterNameOrId>
```
Deletes the given hold. The required argument matter specifies the matter which the hold is associated with.

### Example
This example deletes the hold on student drive data
```
gam delete vaulthold "Hold All Student Drive Files" matter "My Sandwich"
```
----

## Getting Info About A Hold
### Syntax
```
gam info vaulthold <HoldNameOrId> matter <MatterNameOrId>
```
Prints information about a given hold. The required argument matter specifies the matter which the hold is associated with.

### Example
This example displays information about a hold
```
gam.py info hold uid:3w261t744tsa0u matter uid:fd2860ad-4790-4d6f-9d15-a7cbea11dfaf

 updateTime: 2017-06-28T19:02:37.665Z
 name: Broken Arrow
 accounts: 
   holdTime: 2017-06-28T19:02:39.051Z
   email: me@u.jaylee.us
   accountId: 101937355872607653089
 query: 
  mailQuery: 
   endTime: 2014-05-12T00:00:00Z
   terms: subject:BrokenArrow
   startTime: 2012-08-01T00:00:00Z
 corpus: MAIL
 holdId: 3w261t744tsa0u
```
----

## Printing Holds
### Syntax
```
gam print vaultholds [matters <matters>] [todrive]
```
Outputs CSV information about holds. By default, GAM will retrieve the holds for all open matters. The optional argument matters specifies a comma seperated list of matters for which holds should be retrieved. The optional argument todrive creates a Google Spreadsheet of the data rather than CSV output.

### Example
This example creates a spreadsheet of all hold data
```
gam print vaultholds todrive
```
# Vault Exports
## Creating Exports
### Syntax
```
gam create export [matter <matter>] [name <name>] [corpus <drive|mail|groups|hangouts_chat>]
[scope <all_data|held_data|unprocessed_data>]
[accounts <emails> | orgunit <orgunit> | teamdrives <teamdrives> | rooms <rooms> | everyone]
[terms <terms>] [start <date>] [end <date>] [timezone <timezone>] [format mbox|pst]
[excludedrafts true|false] [driveversiondate <date>] [includeteamdrives] [includerooms]
[includeaccessinfo true|false]
```
Create a new Google Vault export request. The required parameter matter specifies the matter name or ID the export should be associated with. The optional parameter name specifies a name for the export, if unspecified, the export name will be of the format `GAM <corpus> <datetime>`. The required parameter corpus specifies the body of data the export should be performed against and should be one of drive, mail, groups or hangouts_chat. The optional parameter scope specified the type of data to include in the export results and should be one of all_data, held_data or unprocessed_data. By default, scope is all_data. It's required to specify one (and only one) of the accounts, orgunit, teamdrives, rooms or everyone parameters to further narrow the export results. accounts is a comma separated list of email addresses (users or groups depending on the corpus). The orgunit parameter specifies the Org Unit where all users in that Org Unit should be included in export results. The rooms argument specifies chat rooms to include in export results. Everyone specifies that all users in your G Suite account should be included in export results. The optional terms parameter specifies the [search operators](https://support.google.com/vault/answer/2474474) to further scope your export results. The optional start, end and timezone parameters specify date range and timezone information to scope your export results. The optional format parameter specifies the export format of mail, group mail and chat messages and should be mbox or pst. The efault is mbox. The optional excludedrafts, driveversiondate, includeteamdrives, includerooms and includeaccessinfo parameters further scope your export results.

### Examples
This example exports all mail for 3 troublemaker users to mbox files
```
gam create export matter 0376cde3-772b-4c1b-b3d9-e82ac9d614f9 corpus mail accounts moe@acme.com,larry@acme.com,curly@acme.com
```
This example exports Drive files for students if the file contains homework in the title
```
gam create export matter 0376cde3-772b-4c1b-b3d9-e82ac9d614f9 corpus drive orgunit /Students terms title:homework includeaccessinfo
```
----

## Getting Info About An Export
### Syntax
```
gam info export <matter> <export>
```
prints info about an existing export. matter and export specify the matter/export name or ID to retrieve info for.

### Example
This example shows information about an existing export
```
gam info export 0376cde3-772b-4c1b-b3d9-e82ac9d614f9 exportly-fff0461a-ff07-41c7-9e19-2037784eb007
```
----
## Downloading An Export
### Syntax
```
gam download export <MatterItem> <ExportItem> [noverify] [noextract] [targetfolder <FilePath>]
```
Downloads the export file results for a given export. The downloaded files will be verified against Google's checksum value to confirm they are not corrupt and then .zip files will be extracted. Note that export status must be COMPLETED before you can download.

### Example
This example downloads an export
```
gam download export id:0376cde3-772b-4c1b-b3d9-e82ac9d614f9 id:exportly-fff0461a-ff07-41c7-9e19-2037784eb007
```
### Example2
This example downloads an export to specific path using "targetfolder"
```
gam download export id:0376cde3-772b-4c1b-b3d9-e82ac9d614f9 id:exportly-fff0461a-ff07-41c7-9e19-2037784eb007 targetfolder <path>
```
----
## Copying an Export
### Syntax
```
gam copy vaultexport <MatterItem> <ExportItem> [target_bucket <bucket>] [target_prefix <prefix>]
```
Copies the exported Vault data to a Google Cloud Storage (GCS) bucket you own or have rights to write objects. The GCS bucket where Google initially exports data is owned by Google and your exports are purged after 15 days. Copying the data to your bucket allows you to retain it for longer and without the need to download the data to your local machine / network. The required argument `target_bucket` specifies a GCS bucket where the data will be copied. The admin account using GAM must have `storage.objects.create`, `storage.objects.get` and `storage.objects.delete` permissions on the target bucket. If the target bucket is of the exact same [storage class](https://cloud.google.com/storage/docs/storage-classes) and [location](https://cloud.google.com/storage/docs/locations) as the source bucket then the copy will be extremely fast and scales by number of files, not their size. In the case of Vault exports, class is always `STANDARD` and location is `EU` multi-region if Europe was chosen for the export or `US` multi-region in the case that United States was explicitly chosen or no choice was made. Your bucket must use the same multi-region exactly to get the best copy performance, choosing `US-EAST4` for example will result in a significantly slower copy. Inter-continental bucket copies are subject to network performance (can you say transcontinental fiber congestion?), can be slow during busy periods and may not complete before your source bucket objects expire. Consider first copying to a bucket you own of the same storage class and location, then you have plenty of time to move to your location bucket. The optional `target_prefix` argument specifies a prefix that will be pre-pended to the target objects and can be a folder path.

**IMPORTANT** The GAM project does not need billing enabled to use this command but it may result in additional billing charges for the target bucket's GCP project based on the amount of storage used in the copy as well as egress/ingress bandwidth. Make sure you are aware of these costs before running this command. The [GCP Cost Calculator](https://cloud.google.com/products/calculator) may help here.

### Example
This example will copy the exported files to my_us_bucket.
```
gam copy export id:0376cde3-772b-4c1b-b3d9-e82ac9d614f9 id:exportly-fff0461a-ff07-41c7-9e19-2037784eb007 target_bucket my_us_bucket
```
This example will place all copied files in a GCS-style folder.
```
gam copy export "HR Matter 144" "djones@acme.com export" target_bucket my_us_bucket target_prefix "djones/"
```
----
# Vault Counts
## Get Item Counts
### Syntax
```
gam print vaultcount matter <MatterNameOrId> [corpus mail|groups] [accounts <emails> | orgunit <orgunit> | everyone] [scope <all_data|held_data|unprocessed_data>] [todrive]
```
Generates a CSV with item counts retained in Vault for the given users or groups. The required argument matter specifies the matter name or ID (prefix with id:) where the count should be performed. The required argument corpus specifies whether Gmail mailbox data or Google Groups archives are queried. You need to specify one argument of accounts, orgunit or everyone to determine which users/groups to query. The scope argument specifies the data to be queried (all_data recommended).

This command can be useful for discovering legacy former employee accounts which no longer have any mail data retained by Vault.

### Example
This example will create a Google Sheet with retained mail item counts in Vault for all users. VFE / archived / suspended users with no items can be considered for purge to free up licenses.
```
gam print vaultcount matter 0376cde3-772b-4c1b-b3d9-e82ac9d614f9 corpus mail everyone scope all_data todrive
```
----

# Takeout
GAM 6.40 and newer support copying and downloading Google Cloud Storage (GCS) buckets generated by [organization-wide Takeout](https://support.google.com/a/answer/100458?hl=en). Once the Takeout completes you need to copy the name of the GCS bucket and provide it to GAM.

## Copying a Bucket
### Syntax
```
gam copy storagebucket [source_bucket <bucket>] [target_bucket <bucket>] [source_prefix <prefix>] [target_prefix <prefix>]
```
Copies objects from one bucket to another. The GCS bucket where Google initially exports Takeout data is owned by Google and your exports are purged after 60 days. Copying the data to your bucket allows you to retain it for longer and without the need to download the data to your local machine / network. The required arguments `target_bucket` and `source_bucket` specify the GCS buckets where the data will be copied from/to. The admin account using GAM must have `storage.objects.create`, `storage.objects.get` and `storage.objects.delete` permissions on the target bucket. If the target bucket is of the exact same [storage class](https://cloud.google.com/storage/docs/storage-classes) and [location](https://cloud.google.com/storage/docs/locations) as the source bucket then the copy will be extremely fast and scales by number of files, not their size. In the case of Google Takeout, class is always `STANDARD` and location is `US` multi-region. Your bucket must use the same multi-region exactly to get the best copy performance, choosing `US-EAST4` for example will result in a significantly slower copy. Inter-continental bucket copies are subject to network performance (can you say TRANSCONTINENTAL FIBER?), can be slow during busy periods and may not complete before your source bucket objects expire. Consider first copying to a bucket you own of the same storage class and location, then you have plenty of time to move to your location bucket. The optional argument `source_prefix` filters copied objects to those matching the prefix and can be a folder path. The optional argument `target_prefix` pre-pends a prefix to objects copied to the target bucket and can be a folder path.

**IMPORTANT** The GAM project does not need billing enabled to use this command but it may result in additional billing charges for the target bucket's GCP project based on the amount of storage used in the copy as well as egress/ingress bandwidth. Make sure you are aware of these costs before running this command. The [GCP Cost Calculator](https://cloud.google.com/products/calculator) may help here.

## Example
This example copies the Google Takeout generated bucket files to another bucket and places them in a folder.
```
gam copy storagebucket source_bucket takeout-export-6454fb47-98f6-4b06-9128-2cfaea7d14dc target_bucket my_us_bucket target_prefix acme.com_takeout_20230206/
```
----

## Downloading a Bucket
### Syntax
```
gam download storagebucket [bucket]
```
Downloads all objects in the storage bucket locally.

### Example
This example downloads a Google Takeout bucket
```
gam download storagebucket takeout-export-6454fb47-98f6-4b06-9128-2cfaea7d14dc
```
----