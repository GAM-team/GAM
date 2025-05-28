# Vault - Takeout
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Vault Matters](#vault-matters)
  - [Create Vault Matters](#create-vault-matters)
  - [Manage Vault Matters](#manage-vault-matters)
  - [Display Vault Matters](#display-vault-matters)
  - [Display Vault Counts](#display-vault-counts)
- [Vault Exports](#vault-exports)
  - [Create Vault Exports](#create-vault-exports)
  - [Delete Vault Exports](#delete-vault-exports)
  - [Download Vault Exports](#download-vault-exports)
  - [Copy Vault Exports](#copy-vault-exports)
  - [Display Vault Exports](#display-vault-exports)
- [Vault Holds](#vault-holds)
  - [Create Vault Holds](#create-vault-holds)
  - [Update Vault Holds](#update-vault-holds)
  - [Delete Vault Holds](#delete-vault-holds)
  - [Display Vault Holds](#display-vault-holds)
  - [Display Vault Holds Affecting a User](#display-vault-holds-affecting-a-user)
- [Vault Saved Queries](#vault-saved-queries)
  - [Display Vault Saved Queries](#display-vault-saved-queries)
- [Takeout](#takeout)
  - [Copy a Takeout Bucket](#copy-a-takeoutbucket)
  - [Download a Takeout Bucket](#download-a-takeout-bucket)

## API documentation
* [Vault API](https://developers.google.com/vault/reference/rest)
* [Vault API - Holds CorpusQuery](https://developers.google.com/vault/reference/rest/v1/matters.holds#CorpusQuery)
* [Vault API - Drive Export Access](https://support.google.com/vault/answer/6099459#metadata)
* [Vault API - Gmail Export Format](https://support.google.com/vault/answer/4388708#new_gmail_export&zippy=%2Cfebruary-new-gmail-export-system-available)

## Query documentation
* https://support.google.com/vault/answer/2474474

## Definitions
[Collections of Items](Collections-of-Items)
```
<AttendeeStatus> ::= accepted|declined|needsaction|tentative
<EmailItem> ::= <EmailAddress>|<UniqueID>|<String>
<EmailItemList> ::= "<EmailItem>(,<EmailItem>)*"
<EmailAddressList> ::= "<EmailAddess>(,<EmailAddress>)*"
<EmailAddressEntity> ::= <EmailAddressList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<TimeZone> ::= <String>
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
<UniqueID> ::= id:<String>

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<ChatSpace> ::= spaces/<String> | space/<String> | <String>
<ChatSpaceList> ::= "<ChatSpace>(,<ChatSpace>)*"
<ExportItem> ::= <UniqueID>|<String>
<ExportStatus> ::= completed|failed|inprogrsss
<ExportStatusList> ::= "<ExportStatus>(,<ExportStatus>)*"
<HoldItem> ::= <UniqueID>|<String>
<MatterItem> ::= <UniqueID>|<String>
<MatterState> ::= open|closed|deleted
<MatterStateList> ::= "<MatterState>(,<MatterState>)*"
<SharedDriveID> ::= <String>
<SharedDriveIDList> ::= "<SharedDriveID>(,<SharedDriveID>)*"
<URL> ::= <String>
<URLList> ::= "<URL>(,<URL>)*"

<QueryVaultCorpus> ::= <String>
        See: https://developers.google.com/vault/reference/rest/v1/matters.holds#CorpusQuery

<VaultMatterFieldName> ::=
        description|
        matterid|
        matterpermissions|
        name|
        state
<VaultMatterFieldNameList> ::= "<VaultMatterFieldName>(,<VaultMatterFieldName>)*"

<VaultExportFieldName> ::=
        cloudstoragesink|
        createtime|
        exportoptions|
        id|
        matterid|
        name|
        query|
        requester|
        requester.displayname|
        requester.email|
        stats|
        stats.exportedArtifactCount|
        stats.sizeinbytes|
        stats.totalartifactcount|
        status
<VaultExportFieldNameList> ::= "<VaultExportFieldName>(,<VaultExportFieldName>)*"

<VaultHoldFieldName> ::=
        accounts|
        accounts.acountid|
        accounts.email|
        accounts.firstname|
        accounts.holdtime|
        accounts.lastname|
        corpus|
        holdid|
        name|
        orgunit|
        orgunit.holdtime|
        orgunit.orgunitid|
        query|
        updatetime
<VaultHoldFieldNameList> ::= "<VaultHoldFieldName>(,<VaultHoldFieldName>)*"

<VaultQueryFieldName> ::=
        createtime |
        displayname |
        matterid |
        name |
        query |
        queryid |
        savedqueryid
<VaultQueryFieldNameList> ::= "<VaultQueryFieldName>(,<VaultQueryFieldName>)*"

```
You specify matters, exports and holds by ID (`<UniqueID>`) or name (`<String>`). The API requires an ID, so if you specify a name,
GAM has to make additional API calls to convert the name to an ID.

## Vault Matters
## Create Vault Matters
Create a Google Vault matter.
```
gam create vaultmatter|matter [name <String>] [description <string>]
        [collaborator|collaborators <EmailItemList>] [sendemails <Boolean>] [ccme <Boolean>]
        [showdetails|returnidonly]
```
Specify the name of the matter:
* `name <String>` - The matter will be named `<String>`
* `default` - The matter will be named `GAM Matter - <Time>`

Use the `showdetails` option to have the full details of the matter displayed.

Use the `returnidonly` option to have only the matter ID displayed.

## Manage Vault Matters
```
gam update vaultmatter|matter <MatterItem> [name <String>] [description <string>]
        [addcollaborator|addcollaborators <EmailItemList>] [removecollaborator|removecollaborators <EmailItemList>]
gam close vaultmatter|matter <MatterItem>
gam reopen vaultmatter|matter <MatterItem>
gam delete vaultmatter|matter <MatterItem>
gam undelete vaultmatter|matter <MatterItem>
```
Vault Matters can be in one of three states: `OPEN`, `CLOSED` and `DELETED`. The valid operations in each state are:
* `OPEN` - `update` and `close`
* `CLOSED` - `reopen` and `delete`
* `DELETED` - `undelete`

## Display Vault Matters
```
gam info vaultmatter|matter <MatterItem>
        [basic|full|(fields <VaultMatterFieldNameList>)]
        [formatjson]
gam show vaultmatters|matters [matterstate <MatterStateList>]
        [basic|full|(fields <VaultMatterFieldNameList>)]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print vaultmatters|matters [todrive <ToDriveAttributes>*] [matterstate <MatterStateList>]
        [basic|full|(fields <VaultMatterFieldNameList>)]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

For `show` and `print`, all matters are displayed by default; use `matterstate <MatterStateList>` to display matters filtered by state.

Select fields to display:
* `basic` - Display `matterId`, `name`, `description` and `state` fields.
* `full` - Display `matterpermissions` in addition to `basic` fields; this is the default.
* `fields <VaultMatterFieldNameList>` - Display selected fields; `matterId` and `name` are always displayed

## Display Vault Counts
Display item counts retained in Vault for the given users or groups.
* The required argument `matter` specifies the matter name or ID (prefix with id:) where the count should be performed.
* The required argument `corpus` specifies whether Gmail mailbox data or Google Groups archives are queried.
* You need to specify one argument of accounts, orgunit or everyone to determine which users/groups to query.
* The `scope` argument specifies the data to be queried, `all_data` is  the default and is recommended.

The command may take some time to complete; GAM makes repeated API calls until the operation is complete. By default,
GAM waits 15 seconds between API calls; use the `wait <Integer>` option to specify a different wait period.

This command can be useful for discovering legacy former employee accounts which no longer have any mail data retained by Vault.
```
gam print vaultcounts [todrive <ToDriveAttributes>*]
        matter <MatterItem> corpus mail|groups
        (accounts <EmailAddressEntity>) | (orgunit|org|ou <OrgUnitPath>) | everyone
        [(shareddrives|teamdrives (<TeamDriveIDList>|(select <FileSelector>|<CSVFileSelector>))) |
            (rooms (<ChatSpaceList>|(select <FileSelector>|<CSVFileSelector>))) |
            (sitesurl (<URLList>||(select <FileSelector>|<CSVFileSelector>)))]
        [scope <all_data|held_data|unprocessed_data>]
        [terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>] [timezone <TimeZone>]
        [excludedrafts <Boolean>]
        [wait <Integer>]
```
Specify the search method, this is optional:
* `accounts <EmailAddressEntity>` - Search all accounts specified in `<EmailAddressEntity>`
* `orgunit|org|ou <OrgUnitPath>` - Search all accounts in the OU `<OrgUnitPath>`
* `everyone` - Search for all accounts in the organization
* `shareddrives|teamdrives <SharedDriveIDList>` - Search for all accounts in the Shared Drives specified in `<SharedDriveIDList>`
* `shareddrives|teamdrives select <FileSelector>|<CSVFileSelector>` - Search for all accounts in the Shared Drives specified in `<FileSelector>|<CSVFileSelector>`
* `rooms <ChatSpaceList>` - Search in the Room specified in the chat rooms specified in `<ChatSpaceList>`
* `rooms <ChatSpaceList>` - Search in the Room specified in the chat rooms specified in `<FileSelector>|<CSVFileSelector>`
* `sitesurl <URLList>` - Search the published site URLs of new Google Sites in `<URLList>`
* `sitesurl <URLList>` - Search the published site URLs of new Google Sites specified in `<FileSelector>|<CSVFileSelector>`

Check the status of a previous count operation with the name from a previous command.
```
gam print vaultcounts [todrive <ToDriveAttributes>*]
        matter <MatterItem> operation <String> [wait <Integer>]
```

## Vault Exports
## Create Vault Exports
Create a Google Vault export request.
```
gam create vaultexport|export matter <MatterItem> [name <String>] corpus calendar|drive|gemini|groups|hangouts_chat|mail|voice
        (accounts <EmailAddressEntity>) | (orgunit|org|ou <OrgUnitPath>) | everyone
        (shareddrives|teamdrives (<TeamDriveIDList>|(select <FileSelector>|<CSVFileSelector>))) |
            (rooms (<ChatSpaceList>|(select <FileSelector>|<CSVFileSelector>))) |
            (sitesurl (<URLList>||(select <FileSelector>|<CSVFileSelector>)))
        [scope all_data|held_data|unprocessed_data]
        [terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>] [timezone <TimeZone>]
        [locationquery <StringList>] [peoplequery <StringList>] [minuswords <StringList>]
        [responsestatuses <AttendeeStatus>(,<AttendeeStatus>)*] [calendarversiondate <Date>|<Time>]
        [(includeshareddrives <Boolean>)|(shareddrivesoption included|included_if_account_is_not_a_member|not_included)]
        [driveversiondate <Date>|<Time>] [includeaccessinfo <Boolean>]
        [driveclientsideencryption any|encrypted|unencrypted]
        [includerooms <Boolean>]
        [excludedrafts <Boolean>] [mailclientsideencryption any|encrypted|unencrypted]
        [showconfidentialmodecontent <Boolean>] [usenewexport <Boolean>] [exportlinkeddrivefiles <Boolean>]
        [covereddata calllogs|textmessages|voicemails]
        [format ics|mbox|pst|xml]
        [region any|europe|us] [showdetails|returnidonly]
```
<MatterItem> specifies the matter name or ID the export should be associated with.

Specify the name of the export:
* `name <String>` - The export will be named `<String>`
* `default` - The export will be named `GAM <corpus> Export - <Time>`

Specify the corpus of data, this option is required:
* `calendar`
* `drive`
* `gemini`
* `groups`
* `mail`
* `hangouts_chat`
* `voice`

Specify the search method, this option is required:
* `accounts <EmailAddressEntity>` - Search all accounts specified in `<EmailAddressEntity>`
* `orgunit|org|ou <OrgUnitPath>` - Search all accounts in the OU `<OrgUnitPath>`
* `everyone` - Search for all accounts in the organization
* `shareddrives|teamdrives <SharedDriveIDList>` - Search for all accounts in the Shared Drives specified in `<SharedDriveIDList>`
* `shareddrives|teamdrives select <FileSelector>|<CSVFileSelector>` - Search for all accounts in the Shared Drives specified in `<FileSelector>|<CSVFileSelector>`
* `rooms <ChatSpaceList>` - Search in the Room specified in the chat rooms specified in `<ChatSpaceList>`
* `rooms <ChatSpaceList>` - Search in the Room specified in the chat rooms specified in `<FileSelector>|<CSVFileSelector>`
* `sitesurl <URLList>` - Search the published site URLs of new Google Sites in `<URLList>`
* `sitesurl <URLList>` - Search the published site URLs of new Google Sites specified in `<FileSelector>|<CSVFileSelector>`

Specify the scope of data to include in the export:
* `all_data` - All available data; this is the default
* `held_data` - Data on Hold
* `unprocessed_data` - Data not processed

You can specify search terms to limit the scope of data:
* `terms <String>` - [Vault search](https://support.google.com/vault/answer/2474474)

Specify time limits on the scope of data:
* `start|starttime <Date>|<Time>` - The start time range for the search query. These timestamps are in GMT and rounded down to the start of the given date.
* `end|endtime <Date>|<Time>` - The end time range for the search query. These timestamps are in GMT and rounded down to the start of the given date.
* `timezone <TimeZone>` - The time zone name. It should be an IANA TZ name, such as "America/Los_Angeles"

For `corpus calendar`, you can specify advanced search options:
* `locationquery <StringList>`
  * Matches only those events whose location contains all of the words in the given set.
  * If the string contains quoted phrases, this method only matches those events whose location contain the exact phrase.
  * Entries in the set are considered in "and".
  * Word splitting example: ["New Zealand"] vs ["New","Zealand"] "New Zealand": matched by both "New and better Zealand": only matched by the latter.
* `peoplequery <StringList>`
  * Matches only those events whose attendees contain all of the words in the given set.
  * Entries in the set are considered in "and".
* `minuswords <StringList>`
  * Matches only those events that do not contain any of the words in the given set in title, description, location, or attendees.
  * Entries in the set are considered in "or".
* `responsestatuses <AttendeeStatus>(,<AttendeeStatus>)*
  * Matches only events for which the custodian gave one of these responses. If the set is empty, there will be no filtering on responses.
* `calendarversiondate <Date>|<Time>`
  * Search the current version of the Calendar event, but export the contents of the last version saved before 12:00 AM UTC on the specified date.
  * Enter the date in UTC.

For `corpus calendar`, you can specify the format of the exported data:
* `format ics` - Export in ICS format, this is the default
* `format pst` - Export in PST format

For `corpus drive`, you can specify advanced search options:
* `driveversiondate <Date>|<Time>` - Search the versions of the Drive file as of the reference date. These timestamps are in GMT and rounded down to the given date.
* `includeshareddrives False` - Mapped to `sharedrivesoption included_if_account_is_not_a_member`
* `includeshareddrives True` - Mapped to `sharedrivesoption included`
* `sharedrivesoption included` - Resources in shared drives are included in the search
* `sharedrivesoption included_if_account_is_not_a_member` - Resources in shared drives where account is not a member are included in the search, this is the default
* `sharedrivesoption not_included` - Resources in shared drives are not included in the search
* `driveclientsideencryption any` - Include both client-side encrypted and unencrypted content in search, this is the default.
* `driveclientsideencryption encrypted` - Include client-side encrypted content only in search.
* `driveclientsideencryption unencrypted` - Include client-side unencrypted content only in search.

For `corpus drive`, you can specify whether to include access information for users with [indirect access](https://support.google.com/vault/answer/6099459#metadata) to the files:
* `includeaccessinfo False` - Do not include access information for users with indirect access, this is the default
* `includeaccessinfo True` - Include access information for users with indirect access

For `corpus hangouts_chat` you can specify advanced search options:
* `includerooms False` - Do not include rooms, this is the default
* `includerooms True` - Include rooms

For `corpus mail`, you can specify advanced search options:
* `excludedrafts False` - Do not exclude drafts, this is the default
* `excludedrafts True` - Exclude drafts
* `mailclientsideencryption any` - Include both client-side encrypted and unencrypted content in search, this is the default.
* `mailclientsideencryption encrypted` - Include client-side encrypted content only in search.
* `mailclientsideencryption unencrypted` - Include client-side unencrypted content only in search.

For `corpus mail`, you can specify whether to export confidential mode content:
* `showconfidentialmodecontent false` - Do not export confidential mode content
* `showconfidentialmodecontent true` - Export confidential mode content

For `corpus mail`, you can specify whether to use the new export system:
* `usenewexport false` - Do not use the new export system
* `usenewexport true` - Use the new export system

For `corpus mail`, you can specify whether to enable exporting linked Drive files:
* `exportlinkeddrivefiles false` - Do not export linked Drive files
* `exportlinkeddrivefiles true` - Export linked Drive files

See: https://support.google.com/vault/answer/4388708#new_gmail_export&zippy=%2Cfebruary-new-gmail-export-system-available

For `corpus calendar`, you can specify the format of the exported data:
* `format ics - Export in ICS format, this is the default
* `format pst` - Export in PST format

For `corpus drive`, you can not specify the format of the exported data,

For `corpus gemini`, `format xml` is the only format of the exported data,

For `corpus groups`, `corpus hangouts_chat`, `corpus mail` and `corpus voice`, you can specify the format of the exported data:
* `format mbox` - Export in MBOX format, this is the default
* `format pst` - Export in PST format

For `corpus voice` you can specify thet data covered by the export:
* `covereddata calllogs` - Call logs
* `covereddata textmessages` - Voice text messages
* `covereddata voicemail` - Voicemail

Use the `region any|europe|us` option to specify the export location; it requires Google Workspace Enterprise or Google Workspace Business licenses.

Use the `showdetails` option to have the full details of the export displayed.

Use the `returnidonly` option to have only the export ID displayed.

### Example
This Example exports deleted Emails for the user user@domain.com
```
gam create vaultexport matter id:148d7a6a-9d94-4b39-b96f-c04d39c6a462 name test-export corpus mail accounts user@domain.com terms "label:^deleted" usenewexport false region europe showdetails
```


## Delete Vault Exports
```
gam delete vaultexport|export <ExportItem> matter <MatterItem>
gam delete vaultexport|export <MatterItem> <ExportItem>
```
## Download Vault Exports
```
gam download vaultexport|export <ExportItem> matter <MatterItem>
        [targetfolder <FilePath>] [targetname <FileName>] [noverify] [noextract] [ziptostdout]
        [bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
        [downloadattempts <Integer>] [retryinterval <Integer>]
gam download vaultexport|export <MatterItem> <ExportItem>
        [targetfolder <FilePath>] [targetname <FileName>] [noverify] [noextract] [ziptostdout]
        [bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
        [downloadattempts <Integer>] [retryinterval <Integer>]
```
By default, GAM makes only one download attempt.
If multiple attempts are specified with `downloadattempts <Integer>`, GAM waits `retryinterval <Integer>`
seconds between attempts; the default retry interval is 30 seconds.

By default, all export files are downloaded; use the `bucketmatchpattern` and
`objectmatchpattern` options to selectively download files. See example below.

By default, the export files will be downloaded to the directory specified by `drive_dir` in gam.cfg.
* `targetfolder <FilePath>` - The export files will be downloaded to `<FilePath>`

By default, the export files have long names made up of the matter name, export name and date.
* `targetname <FileName>` - Specify a name for the top level files: `.zip`, `.xml`, `.csv`.

The extensions of the top level files will be appended to `<FileName>`.

Alternatively, `<FileName>` can contain the strings `#objectname#`, `#filename#`
and `#extension#` which will be replaced by the values from the original object names to construct a complete top level name.
For example, `targetname "#filename#.#extension#"` strips the long matter name from the original name.

**In versions prior to 6.07.14, If `<FileName>` does not contain `#filename#` and there are multiple top level files with the same extension, only the
last file with a given extension will be saved as the earlier files will be overwritten.**

This is fixed in 6.07.14: the files will be named `FileName-N.ext` where `N` is `1,2,3,...`.

Zip files extracted from the top level Zip file will still have their long names.

* `noverify` - Do not verify MD5 hash on downloaded file
* `noextract` - Do not extract files from downloaded Zip file

The Zip file can be written to stdout to allow the following command structure:
```
gam download vaultexport <MatterItem> <ExportItem> ziptostdout | some program that consumes the Zip file
```
This will only be successful if there is one main Zip file in the export.

### Example
This example will download a specific export locally using the default Google Vault filenames
```
gam download export id:148d7a6a-9d94-4b39-b96f-c04d39c6a462 id:exportly-96a352af-333a-4230-9822-49a679ceaca3 targetname "#filename#.#extension#" noextract downloadattempts 3
```


### Process vault export files
Given the following matter, exports and Cloud Storage sink objects (files):

```
Vault
  +--my_matter
      +--user1@domain.com-drive_export
      |   +--drive_object_1.zip (10G)
      |   +--drive_object_2.zip (10G)
      |   +--...
      |   +--drive_object_n.xml (5G)
      +--user1@domain.com-gmail_export
      |   +--gmail_object_1.zip (10G)
      |   +--gmail_object_2.zip (10G)
      |   +--...
      |   +--gmail_object_n.xml (3G)
      +--user1@domain.com-chat_export
      |   +--chat_object_1.zip (10G)
      |   +--chat_object_2.zip (10G)
      |   +--...
      |   +--chat_object_n.xml (4G)
      +--user2@domain.com-gmail_export
          +--gmail_object_1.zip (10G)
          +--gmail_object_2.zip (10G)
          +--...
          +--gmail_object_n.xml (3G)
```
The following bash shell script will download and upload one by one all the Cloud Storage objects (files) from all exports for a given user, say **user1@domain.com**:
```
#!/bin/bash
# Obtain just the objects belonging to user1@domain.com and create a file without headers
gam config csv_output_row_filter cloudStorageSink.files.objectName:regex:user1@domain.com \
redirect csv ./user1@domain.com-vault-files.csv noheader \
print vaultexports matters "my_matter" oneitemperrow

# Iterate the CSV file just generated line by line
while read LINE
do
    # Extract export name from line, field 4.
    # Eg. user1@domain.com-gmail_export
    EXPORT=$(echo ${LINE} | cut -d, -f4)

    # Extract object name from line, field 7.
    # Eg. xxxxx/exportly-yyyyy/user1@domain.com-gmail_object_1.zip
    OBJECT=$(echo ${LINE} | cut -d, -f7)

    # Local filename: replace all "/" by "-" to avoid directory issues locally
    # Eg. xx/yy/user1@domain.com-gmail_object_1.zip -> xx-yy-user1@domain.com-gmail_object_1.zip
    LOCALFILE=${OBJECT////-}

    # Destination filename: strip Cloud Storage path and keep filename
    # Eg. xx/yy/user1@domain.com-gmail_object_1.zip -> user1@domain.com-gmail_object_1.zip
    FILENAME=${OBJECT##*/}

    # Download Cloud Storage object (file) and store locally with long ugly name
    # Eg. xxxxx-exportly-yyyyy-user1@domain.com-gmail_object_1.zip)
    gam download vaultexport ${EXPORT} matter "my_matter" \
    targetfolder . targetname "#objectname#" \
    noextract objectmatchpattern ${OBJECT}

    # Upload ugly named local file to "My Drive" with a clean name
    # Eg. user1@domain.com-drive_object_1.zip
    gam user admin@domain.com add drivefile localfile ${LOCALFILE} \
    parentname "My Drive" drivefilename ${FILENAME}

    # Remove local file with ugly name
    rm ${LOCALFILE}

# user1@domain.com-vault-files.csv is the file generated in the first step
done < user1@domain.com-vault-files.csv
```
Why would you want to download files one by one when GAM can download all Cloud Storage objects in one go? Because all of the files combined **might** take up a lot of space (think Terabytes in case of a Drive export of many years) whereas individually, each file will be in a much more manageable ~10 Gigabyte range.

## Copy Vault Exports
Many thanks to Jay for this command and documentation.
```
gam copy vaultexport|export <ExportItem> matter <MatterItem>
        [targetbucket <String>] [targetprefix <String>]
        [bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
        [copyattempts <Integer>] [retryinterval <Integer>]
gam copy vaultexport|export <MatterItem> <ExportItem>
        [targetbucket <String>] [targetprefix <String>]
        [bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
        [copyattempts <Integer>] [retryinterval <Integer>]
```
Copies the exported Vault data to a Google Cloud Storage (GCS) bucket you own or have rights to write objects. The GCS bucket where Google initially exports data is owned by Google
and your exports are purged after 15 days. Copying the data to your bucket allows you to retain it for longer and without the need to download the data to your local machine / network.
The required argument `targetbucket` specifies a GCS bucket where the data will be copied. The admin account using GAM must have `storage.objects.create`, `storage.objects.get` and `storage.objects.delete`
permissions on the target bucket. If the target bucket is of the exact same [storage class](https://cloud.google.com/storage/docs/storage-classes) and [location](https://cloud.google.com/storage/docs/locations)
as the source bucket then the copy will be extremely fast and scales by number of files, not their size. In the case of Vault exports, class is always `STANDARD` and location is `EU` multi-region if Europe was chosen
for the export or `US` multi-region in the case that United States was explicitly chosen or no choice was made. Your bucket must use the same multi-region exactly to get the best copy performance,
choosing `US-EAST4` for example will result in a significantly slower copy. Inter-continental bucket copies are subject to network performance (can you say TRANSCONTINENTAL FIBER?), can be slow during busy periods
and may not complete before your source bucket objects expire. Consider first copying to a bucket you own of the same storage class and location, then you have plenty of time to move to your location bucket.
The optional `targetprefix` argument specifies a prefix that will be pre-pended to the target objects and can be a folder path.

**IMPORTANT** The GAM project does not need billing enabled to use this command but it may result in additional billing charges for the target bucket's GCP project based on the amount of storage used in the copy
as well as egress/ingress bandwidth. Make sure you are aware of these costs before running this command. The [GCP Cost Calculator](https://cloud.google.com/products/calculator) may help here.

### Example
This example will copy the exported files to my_us_bucket.
```
gam copy export id:0376cde3-772b-4c1b-b3d9-e82ac9d614f9 id:exportly-fff0461a-ff07-41c7-9e19-2037784eb007 targetbucket my_us_bucket
```
This example will place all copied files in a GCS-style folder.
```
gam copy export "HR Matter 144" "djones@acme.com export" targetbucket my_us_bucket target_prefix "djones/"
```

## Display Vault Exports
```
gam info vaultexport|export <ExportItem> matter <MatterItem>
        [fields <VaultExportFieldNameList>] [shownames]
        [formatjson]
gam info vaultexport|export <MatterItem> <ExportItem>
        [fields <VaultExportFieldNameList>] [shownames]
        [formatjson]
gam show vaultexports|exports
        [matters <MatterItemList>] [exportstatus <ExportStatusList>]
        [fields <VaultExportFieldNameList>] [shownames]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print vaultexports|exports [todrive <ToDriveAttributes>*]
        [matters <MatterItemList>] [exportstatus <ExportStatusList>]
        [fields <VaultExportFieldNameList>] [shownames]
        [formatjson [quotechar <Character>]]
        [oneitemperrow]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

For `show` and `print`, exports for all matters are displayed by default; use `matter|matters <MatterItemList>` to display exports for a specific set of matters.

For `show` and `print`, all exports are displayed by default; use `exportstatus <ExportStatusList>` to display exports filtered by status.

For `print`, by default all cloudStorageSink files are displayed on a single row;
use `oneitemperrow` to have each file displayed on a separate row.

Select fields to display:
* By default all fields are displayed
* `fields <VaultExportFieldNameList>` - Display selected fields; `id` and `name` are always displayed

The `shownames` argument controls whether account and org unit names are displayed; additional API calls are required to get the names.

## Vault Holds
## Create Vault Holds
```
gam create vaulthold|hold matter <MatterItem> [name <String>] corpus calendar|drive|mail|groups|hangouts_chat|voice
        [(accounts|groups|users <EmailItemList>) | (orgunit|org|ou <OrgUnit>)]
        [query <QueryVaultCorpus>]
        [terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [includerooms <Boolean>]
        [covereddata calllogs|textmessages|voicemails]
        [includeshareddrives <Boolean>]
        [showdetails|returnidonly]
```
Specify the name of the hold:
* `name <String>` - The hold will be named `<String>`
* `default` - The hold will be named `GAM <corpus> Hold - <Time>`

Specify the corpus of data, this option is required:
* `calendar`
* `drive`
* `mail`
* `groups`
* `hangouts_chat`
* `voice`

Specify the search method, this option is required:
* `accounts|groups|users <EmailAddressEntity>` - Search all accounts specified in `<EmailAddressEntity>`
* `orgunit|org|ou <OrgUnitPath>` - Search all accounts in the OU `<OrgUnitPath>`

The `query <QueryVaultCorpus>` option can still be used but it is much simpler to use the following options.

For `corpus drive`, you can specify advanced search options:
* `includeshareddrives False` - Files in shared drives are not included in the hold, this is the default
* `includeshareddrives True` - Files in shared drives are included in the hold

For `corpus mail`, you can specify search terms to limit the search.
* `terms <String>` - [Vault search](https://support.google.com/vault/answer/2474474)

For `corpus mail`, you can specify time limits on the search:
* `start|starttime <Date>|<Time>` - The start time range for the search query. These timestamps are in GMT and rounded down to the start of the given date.
* `end|endtime <Date>|<Time>` - The end time range for the search query. These timestamps are in GMT and rounded down to the start of the given date.

For `corpus hangouts_chat` you can specify advanced search options:
* `includerooms False` - Do not include rooms, this is the default
* `includerooms True` - Include rooms

For `corpus voice` you can specify the data covered by the hold:
* `covereddata calllogs` - Call logs
* `covereddata textmessages` - Voice text messages
* `covereddata voicemail` - Voicemail

Use the `showdetails` option to have the full details of the hold displayed.

Use the `returnidonly` option to have only the hold ID displayed.

## Update Vault Holds
```
gam update vaulthold|hold <HoldItem> matter <MatterItem>
        [([addaccounts|addgroups|addusers <EmailItemList>] [removeaccounts|removegroups|removeusers <EmailItemList>]) | (orgunit|ou <OrgUnit>)]
        [query <QueryVaultCorpus>]
        [terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [includerooms <Boolean>]
        [covereddata calllogs|textmessages|voicemails]
        [includeshareddrives <Boolean>]
        [showdetails]
```
For a hold with `corpus drive`, you can specify advanced search options:
* `includeshareddrives False` - Files in shared drives are not included in the hold, this is the default
* `includeshareddrives True` - Files in shared drives are included in the hold

For a hold with `corpus mail`, you can specify search terms to limit the search.
* `terms <String>` - [Vault search](https://support.google.com/vault/answer/2474474)

For a hold with `corpus mail`, you can specify time limits on the search:
* `start|starttime <Date>|<Time>` - The start time range for the search query. These timestamps are in GMT and rounded down to the start of the given date.
* `end|endtime <Date>|<Time>` - The end time range for the search query. These timestamps are in GMT and rounded down to the start of the given date.

For a hold with `corpus hangouts_chat` you can specify advanced search options:
* `includerooms False` - Do not include rooms, this is the default
* `includerooms True` - Include rooms

For a hold with `corpus voice` you can specify the data covered by the hold:
* `covereddata calllogs` - Call logs
* `covereddata textmessages` - Voice text messages
* `covereddata voicemail` - Voicemail

Use the `showdetails` option to have the full details of the hold displayed.

## Delete Vault Holds
```
gam delete vaulthold|hold <HoldItem> matter <MatterItem>
gam delete vaulthold|hold <MatterItem> <HoldItem>
```
Vault holds can only be managed in `OPEN` matters.

The types of email addresses in `<EmailItemList>` is determined by the value of `corpus`:
* `drive` or `mail` - user email addresses
* `group` - group email addresses

## Display Vault Holds
```
gam info vaulthold|hold <HoldItem> matter <MatterItem>
        [fields <VaultHoldFieldNameList>] [shownames]
        [formatjson]
gam info vaulthold|hold <MatterItem> <HoldItem>
        [fields <VaultHoldFieldNameList>] [shownames]
        [formatjson]
gam show vaultholds|holds [matters <MatterItemList>]
        [fields <VaultHoldFieldNameList>] [shownames]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print vaultholds|holds [todrive <ToDriveAttributes>*] [matters <MatterItemList>]
        [fields <VaultHoldFieldNameList>] [shownames]
        [formatjson [quotechar <Character>]]
        [oneitemperrow]
```
By default, all accounts for a hold are displayed on a single row;
use `oneitemperrow` to have each account displayed on a separate row.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

Vault holds can only be displayed in `OPEN` matters.

For `show` and `print`, holds for all matters are displayed by default; use `matter|matters <MatterItemList>` to display holds for a specific set of matters.

Select fields to display:
* By default all fields are displayed
* `fields <VaultHoldFieldNameList>` - Display selected fields; `holdId` and `name` are always displayed

The `shownames` argument controls whether account and org unit names are displayed; additional API calls are required to get the names.

## Display Vault Holds Affecting a User
Display vault holds that directly reference a user's account or an Organizational Unit of which the user is a member.
```
gam <UserTypeEntity> print vaultholds|holds [todrive <ToDriveAttributes>*]
gam <UserTypeEntity> show vaultholds|holds
```

## Vault Saved Queries
## Display Vault Saved Queries
```
gam info vaultquery <QueryItem> matter <MatterItem>
        [fields <VaultQueryFieldNameList>] [shownames]
        [formatjson]
gam info vaultquery <MatterItem> <QueryItem>
        [fields <VaultQueryFieldNameList>] [shownames]
        [formatjson]
gam show vaultqueries [matters <MatterItemList>]
        [fields <VaultQueryFieldNameList>] [shownames]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print vaultqueries [todrive <ToDriveAttribute>*] [matters <MatterItemList>]
        [fields <VaultQueryFieldNameList>] [shownames]
        [formatjson [quotechar <Character>]]

```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

Vault saved queries can only be displayed in `OPEN` matters.

For `show` and `print`, saved queries for all matters are displayed by default; use `matter|matters <MatterItemList>` to display saved queries for a specific set of matters.

Select fields to display:
* By default all fields are displayed
* `fields <VaultFieldNameList>` - Display selected fields; `matterId`, `matterName`, `savedQueryId` and `displayName` are always displayed

The `shownames` argument controls whether org unit and shared drive names are displayed in queries; additional API calls are required to get the names.

# Takeout
Many thanks to Jay for these commands and documentation.

GAM 6.42.00 and newer support copying and downloading Google Cloud Storage (GCS) buckets generated by [organization-wide Takeout](https://support.google.com/a/answer/100458?hl=en).
Once the Takeout completes you need to copy the name of the GCS bucket and provide it to GAM.

## Copy a Takeout Bucket
Copies objects from one takeout bucket to another.
```
gam copy storagebucket sourcebucket <String> targetbucket <String>
        [sourceprefix <String>] [targetprefix <String>]
```
The GCS bucket where Google initially exports Takeout data is owned by Google and your exports are purged after 30 days. Copying the data to your bucket allows you to retain it for longer and without the need to
download the data to your local machine / network. The required arguments `sourcebucket` and `targetbucket` specify the GCS buckets where the data will be copied from/to. The admin account using GAM must have
`storage.objects.create`, `storage.objects.get` and `storage.objects.delete` permissions on the target bucket. If the target bucket is of the exact same [storage class](https://cloud.google.com/storage/docs/storage-classes)
and [location](https://cloud.google.com/storage/docs/locations) as the source bucket then the copy will be extremely fast and scales by number of files, not their size. In the case of Google Takeout, class is always `STANDARD`
and location is `US` multi-region. Your bucket must use the same multi-region exactly to get the best copy performance, choosing `US-EAST4` for example will result in a significantly slower copy. Inter-continental bucket copies
are subject to network performance (can you say TRANSCONTINENTAL FIBER?), can be slow during busy periods and may not complete before your source bucket objects expire. Consider first copying to a bucket you own of
the same storage class and location, then you have plenty of time to move to your location bucket. The optional argument `sourceprefix` filters copied objects to those matching the prefix and can be a folder path.
The optional argument `targetprefix` pre-pends a prefix to objects copied to the target bucket and can be a folder path.

**IMPORTANT** The GAM project does not need billing enabled to use this command but it may result in additional billing charges for the target bucket's GCP project based on the amount of storage used in the copy
as well as egress/ingress bandwidth. Make sure you are aware of these costs before running this command. The [GCP Cost Calculator](https://cloud.google.com/products/calculator) may help here.

## Example
This example copies the Google Takeout generated bucket files to another bucket and places them in a folder.
```
gam copy storagebucket sourcebucket takeout-export-6454fb47-98f6-4b06-9128-2cfaea7d14dc targetbucket my_us_bucket targetprefix acme.com_takeout_20230206/
```

## Download a Takeout Bucket
Downloads all objects in a takeout storage bucket.
```
gam download storagebucket <String>
        [targetfolder <FilePath>]
```
By default, the takeout files will be downloaded to the directory specified by `drive_dir` in gam.cfg.
* `targetfolder <FilePath>` - The takeout files will be downloaded to `<FilePath>`

### Example
This example downloads a Google Takeout bucket
```
gam download storagebucket takeout-export-6454fb47-98f6-4b06-9128-2cfaea7d14dc
```
