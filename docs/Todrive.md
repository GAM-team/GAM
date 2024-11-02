# Todrive
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Config file options](#config-file-options)
- [Command line options](#command-line-options)
- [Option details](#option-details)
  - [Upload user](#upload-user)
  - [Create new file](#create-new-file)
  - [File name, file description and sheet name](#file-name-file-description-and-sheet-name)
  - [Spreadsheet settings](#spreadsheet-settings)
  - [Open browser and send email](#open-browser-and-send-email)
  - [Local copy](#local-copy)
  - [Update existing file with a new sheet](#update-existing-file-with-a-new-sheet)
  - [Add a new sheet to an existing file](#add-a-new-sheet-to-an-existing-file)
  - [Update an existing sheet within an existing file](#update-an-existing-sheet-within-an-existing-file)
  - [Handle CSV files with no data rows](#handle-csv-files-with-no-data-rows)
- [Redirect CSV](#redirect-csv)
- [Limited Service Account Access](#limited-service-account-access)
- [No Service Account Access](#no-service-account-access)
* [Authorization](Authorization)

## Introduction
Gam print commands allow the results to be uploaded to Google Drive instead of being saved locally.
By default, Gam titles the uploaded file: "Domain Name - Data Type"; Data Type describes the data being uploaded, e.g. Groups, Orgs, Users. It is uploaded to the root folder of the admin user named in `oauth2.txt`.

You can modify the default todrive behavior with options in `gam.cfg` or on the command line.

## Definitions
```
<DriveFileID> ::= <String>
<DriveFolderID> ::= <String>
<TimeZone> ::= <String>
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

<Locale> ::=
        ''|    #Not defined
        ar-eg| #Arabic, Egypt
        az-az| #Azerbaijani, Azerbaijan
        be-by| #Belarusian, Belarus
        bg-bg| #Bulgarian, Bulgaria
        bn-in| #Bengali, India
        ca-es| #Catalan, Spain
        cs-cz| #Czech, Czech Republic
        cy-gb| #Welsh, United Kingdom
        da-dk| #Danish, Denmark
        de-ch| #German, Switzerland
        de-de| #German, Germany
        el-gr| #Greek, Greece
        en-au| #English, Australia
        en-ca| #English, Canada
        en-gb| #English, United Kingdom
        en-ie| #English, Ireland
        en-us| #English, U.S.A.
        es-ar| #Spanish, Argentina
        es-bo| #Spanish, Bolivia
        es-cl| #Spanish, Chile
        es-co| #Spanish, Colombia
        es-ec| #Spanish, Ecuador
        es-es| #Spanish, Spain
        es-mx| #Spanish, Mexico
        es-py| #Spanish, Paraguay
        es-uy| #Spanish, Uruguay
        es-ve| #Spanish, Venezuela
        fi-fi| #Finnish, Finland
        fil-ph| #Filipino, Philippines
        fr-ca| #French, Canada
        fr-fr| #French, France
        gu-in| #Gujarati, India
        hi-in| #Hindi, India
        hr-hr| #Croatian, Croatia
        hu-hu| #Hungarian, Hungary
        hy-am| #Armenian, Armenia
        in-id| #Indonesian, Indonesia
        it-it| #Italian, Italy
        iw-il| #Hebrew, Israel
        ja-jp| #Japanese, Japan
        ka-ge| #Georgian, Georgia
        kk-kz| #Kazakh, Kazakhstan
        kn-in| #Kannada, India
        ko-kr| #Korean, Korea
        lt-lt| #Lithuanian, Lithuania
        lv-lv| #Latvian, Latvia
        ml-in| #Malayalam, India
        mn-mn| #Mongolian, Mongolia
        mr-in| #Marathi, India
        my-mn| #Burmese, Myanmar
        nl-nl| #Dutch, Netherlands
        nn-no| #Nynorsk, Norway
        no-no| #Bokmal, Norway
        pa-in| #Punjabi, India
        pl-pl| #Polish, Poland
        pt-br| #Portuguese, Brazil
        pt-pt| #Portuguese, Portugal
        ro-ro| #Romanian, Romania
        ru-ru| #Russian, Russia
        sk-sk| #Slovak, Slovakia
        sl-si| #Slovenian, Slovenia
        sr-rs| #Serbian, Serbia
        sv-se| #Swedish, Sweden
        ta-in| #Tamil, India
        te-in| #Telugu, India
        th-th| #Thai, Thailand
        tr-tr| #Turkish, Turkey
        uk-ua| #Ukrainian, Ukraine
        vi-vn| #Vietnamese, Vietnam
        zh-cn| #Simplified Chinese, China
        zh-hk| #Traditional Chinese, Hong Kong SAR China
        zh-tw  #Traditional Chinese, Taiwan
```
## Config file options
You can specify many `todrive` options in `gam.cfg`.
```
todrive_clearfilter
        Enable/disable clearing the spreadsheet basic filter when uploading data to an existing sheet in an existing file.
        Default: False
todrive_clientaccess
        Enable/disable use of client access rather than service account access when uploading files with todrive
        Default: False
todrive_conversion
        Enable/disable conversion of CSV files to Google Sheets when todrive is specified
        Default: True
todrive_localcopy
        Enable/disable saving a local copy of CSV files when todrive is specified
        Default: False
todrive_locale
        The Spreadsheet settings Locale value.
        See <Locale>
        Default: ''
todrive_nobrowser
        Enable/disable opening a browser when todrive is specified
        Default: False
todrive_noemail
        Enable/disable sending an email when todrive is specified
        Default: True
todrive_no_escape_char
        When writing a CSV file to Google Drive, should `\` be ignored as an escape character.
        Default: True
todrive_parent
        Parent folder for CSV files when todrive is specified;
        can be id:<DriveFolderID> or <DriveFolderName>
        Default: root
todrive_sheet_timestamp
        Enable/disable adding a timestamp to the sheet (tab) title of CSV files when todrive is specified
        Default: False
todrive_sheet_timeformat
        Format of the timestamp added to the sheet (tab) title of CSV files
        See: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        Default: '' which selects an ISO format timestamp
        Example: %Y-%m-%dT%H:%M:%S will display as 2020-07-06T17:48:54
todrive_timestamp
        Enable/disable adding a timestamp to the title of CSV files when todrive is specified
        Default: False
todrive_timeformat
        Format of the timestamp added to the title of CSV files
        See: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        Default: '' which selects an ISO format timestamp
        Example: %Y-%m-%dT%H:%M:%S will display as 2020-07-06T17:48:54
todrive_timezone
        The Spreadsheet settings Timezone value.
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        Default: ''
todrive_upload_nodata
        Enable/disable uploading CSV files with no data rows
        Default: True
todrive_user
        Email address of user to receive CSV files when todrive is specified
        Default: '' which becomes admin user in admin_email or address from oauth2.txt
```

## Command line options
Anywhere you can specify `todrive`, there are additional subarguments following the `todrive` argument that let you title the file, add a description, specify the sheet name,
direct the uploaded file to a particular user and location and add a timestamp to the file title.

```
<ToDriveAttribute> ::=
        (tdaddsheet [<Boolean>])|
        (tdalert <EmailAddress>)*|
        (tdbackupsheet (id:<Number>)|<String>)|
        (tdcellnumberformat text|number)|
        (tdcellwrap clip|overflow|wrap)|
        (tdclearfilter [<Boolean>])|
        (tdcopysheet (id:<Number>)|<String>)|
        (tddescription <String>)|
        (tdfileid <DriveFileID>)|
        (tdfrom <EmailAddress>)|
        (tdlocalcopy [<Boolean>])|
        (tdlocale <Locale>)|
        (tdnobrowser [<Boolean>])|
        (tdnoemail [<Boolean>])|
        (tdnoescapechar [<Boolean>])|
        (tdnotify [<Boolean>])|
        (tdparent (id:<DriveFolderID>)|<DriveFolderName>)|
        (tdretaintitle [<Boolean>])|
        (tdreturnidonly [<Boolean>])|
        (tdshare <EmailAddress> commenter|reader|writer)*|
        (tdsheet (id:<Number>)|<String>)|
        (tdsheettimestamp [<Boolean>] [tdsheettimeformat <String>])
        (tdsheettitle <String>)|
        (tdsubject <String>)|
        ([tdsheetdaysoffset <Number>] [tdsheethoursoffset <Number>])|
        (tdtimestamp [<Boolean>] [tdtimeformat <String>]
            ([tddaysoffset <Number>] [tdhoursoffset <Number>])|
        (tdtimezone <TimeZone>)|
        (tdtitle <String>)|
        (tdupdatesheet [<Boolean>])|
        (tduploadnodata [<Boolean>])|
        (tduser <EmailAddress>)
```

## Option details
By default, a new Google spreadsheet will be created.
Gam titles the uploaded file: "Domain Name - Data Type"; Data Type describes the data being uploaded, e.g. Groups, Orgs, Users.
It is uploaded to the root folder of the admin user named in `oauth2.txt`.

## Upload user
* `tduser` - The user to receive the uploaded file; if not specified, the `todrive_user` value from gam.cfg is used; that value defaults to the user named in oauth2.txt.

## Create new file
If `tdfileid <DriveFileID>` is not specified, a new file is created.
* `tdparent` - An existing/writable parent folder for the uploaded file; if not specified, the `todrive_parent` value from gam.cfg is used; that value defaults to the root folder.
* `tdshare <EmailAddress> commenter|reader|writer` - Share the new file with `<EmailAddress>` with the specified role. `<EmailAddress>` must be valid within your Google Workspace. You can specify multiple shares.

## File name, file description and sheet name
* `tdtitle` - The title for the uploaded file, if not specified, the Gam default title is used.
* `tddescription` - The description for the uploaded file, if not specified, the command line that created the file is used.
* `tdsheettitle <String>` - The sheet name in the uploaded file if it is uploaded as a Google Sheet, if not specified, the `tdtitle` is used.
* `tdsheettimestamp` - Should a timestamp (of the time the file is uploaded to Google) be added to the sheet (tab) title of the uploaded file; if not specified, the `todrive_sheet_timestamp` value from gam.cfg is used, that value defaults to False.
* `tdsheettimeformat` - Format of the timestamp added to the sheet (tab) title of the uploaded file; if not specified, the `todrive_sheet_timeformat` value from gam.cfg is used, that value defaults to '' which selects an ISO format timestamp.
* `tdsheetdaysoffset` and `tdsheethoursoffset` - Values that subtract time from the sheet (tab) timestamp. If neither value is specified, the `tddaysoffset` and `tdhoursoffset` values are used. To use a file timestamp offset, but not a sheet (tab) timestamp offset, specify `tdsheetdaysoffset 0`. A possible use for these values is as documentation to reflect the end of the time period that the uploaded report covers.
* `tdtimestamp` - Should a timestamp (of the time the file is uploaded to Google) be added to the title of the uploaded file; if not specified, the `todrive_timestamp` value from gam.cfg is used, that value defaults to False.
* `tdtimeformat` - Format of the timestamp added to the title of the uploaded file; if not specified, the `todrive_timeformat` value from gam.cfg is used, that value defaults to '' which selects an ISO format timestamp.
  * See: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
* `tddaysoffset` and `tdhoursoffset` - Values that subtract time from the timestamp, they default to 0. A possible use for these values is as documentation to reflect the end of the time period that the uploaded report covers.
* `tdsubject <String>` - Use `<String>` as the subject in all emails sent. In `<String>`, `#file#` will, be replaced by the file title and `#sheet#` will be replaced by the sheet/tab title. By default, the subject is the file title.

## Spreadsheet settings
* `tdlocale <Locale>` - The Spreadsheet settings Locale value.
* `tdtimezone <TimeZone>` - The Spreadsheet settings Timezone value.
* `tdcellwrap clip|overflow|wrap` - The Spreadsheet cell wrapping strategy.
* `tdcellnumberformat text|number` - The Spreadsheet number format.

## Report action, capture file ID
* `tdreturnidonly` - If False, a message is written to stdout with the uploaded file URL; if True, only the uploaded file ID is written to stdout

The ID can be captured and used in subsequent commands, `tdfileid <DriveFileID>` that will update the same file.

## Open browser and send email
* `tdnobrowser` - If False, a browser is opened to view the file uploaded to Google Drive; if not specified, the `todrive_nobrowser` value from gam.cfg is used. If True, no browser is opened.
* `tdnoemail` - If False, an email is sent to `tduser` informing them of name and URL of the uploaded file; if not specified, the `todrive_noemail` value from gam.cfg is used. If True, no email is sent to `tduser`.
* `tdnotify` - If True, an email is sent to all `tdshare <EmailAddress>` and `tdalert <EmailAddress>` users informing them of name and URL of the uploaded/updated file. If False, no emails are sent.
* `tdfrom <EmailAddress>` - Emails will be sent with `<EmailAddress>` as the from address. By default, the from address is the Google Workspace Admin in `gam oauth info`.

## Escape character
* `tdnoescapechar <Boolean>` - Should `\` be ignored as an escape character; if not specified, the value of `todrive_no_escape_char` from `gam.cfg` will be used

## Local copy
* `tdlocalcopy` - Should a local copy of the CSV file be saved in addition to the file uploaded to Google Drive; if not specified, the `todrive_localcopy` value from gam.cfg is used.

## Update existing file with a new sheet
* `tdfileid <DriveFileID>` - An existing/writable file for the uploaded file.
* `tdretaintitle`or `tdretaintitle true` - Do not update the existing file name.
* `tdsheettitle <String>` - A new sheet with name `<String>` will be created and assigned a new sheet ID. All other sheets will be deleted.

## Add a new sheet to an existing file
* `tdfileid <DriveFileID>` - An existing/writable file for the uploaded file.
* `tdretaintitle`or `tdretaintitle true` - Do not update the existing file name.
* `tdsheet <String>` - The title of the new sheet; if not specified, this will be the same value as `tdtitle`.
* `tdaddsheet` - In conjunction with `tdfileid <DriveFileID>` and `tdsheet <String>`, a new sheet will be added to an existing/writeable file. All other sheets are unaffected.

## Update an existing sheet within an existing file
* `tdfileid <DriveFileID>` - An existing/writable file for the uploaded file.
* `tdretaintitle`or `tdretaintitle true` - Do not update the existing file name.
* `tdsheet (id:<Number>)|<String>` - An existing sheet with ID `<Number>` or name `<String>` will be updated. All other sheets are unaffected.
* `tdupdatesheet` - In conjunction with `tdfileid <DriveFileID>` and `tdsheet id:<Number>`, an existing sheet in an existing/writeable file is updated.
* `tdsheettitle` - In conjunction with `tdfileid <DriveFileID>` and `tdsheet id:<Number>` and `tdupdatesheet`, an existing sheet in an existing/writeable file is updated and renamed.
* `tdupdatesheet` - In conjunction with `tdfileid <DriveFileID>` and `tdsheet <String>`, an existing sheet in an existing/writeable file is updated; it will be created if necessary.
* `tdbackupsheet (id:<Number>)|<String>` - An existing sheet will be updated with the contents of `tdsheet (id:<Number>)|<String>)` before that sheet is updated.
* `tdcopysheet (id:<Number>|<String>` - An existing sheet will be updated with the contents of `tdsheet (id:<Number>)|<String>)` after that sheet is updated.
* `tdclearfilter [<Boolean>]` - Should the spreadsheet basic filter be cleared; if not specified, the `todrive_clearfilter` value from gam.cfg is used, that value defaults to False. When False, the current/default behavior, the data suppressed by an existing filter is not replaced by the uploaded data. This might be desirable if you wanted to compare the previous and current data, but in general you probably want a value of True so that the uploaded data completely replaces the existing data.

## Handle CSV files with no data rows
* `tduploadnodata` - Enable/disable uploading CSV files with no data rows; if not specified, the `todrive_upload_nodata` value from gam.cfg is used; that value defaults to true

## Redirect CSV
You can specify `todrive` options in conjunction with `redirect csv`.
```
redirect csv <FileName> [multiprocess] [append] [noheader] [charset <Charset>]
             [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
             [todrive <ToDriveAttribute>*]
```
If you are doing `redirect csv <FileName> multiprocess`, it is more efficient to specify `todrive <ToDriveAttribute>*` as part of
the redirect as verification of the `todrive` settings, which can invole several API calls, is done once rather than in each of the subprocesses.

`columndelimiter <Character>` and `quotechar <Character>` will not generally be used with `todrive` as
Google Sheets only recognizes `,` as the column delimiter and `"` as the quote character.

`noescapechar true` will generally be used with `todrive` as Google Sheets does not recognize `\\` as an escaped `\`.

## Examples
Generate a list of user IDs and names, title the file "User IDs and Names", upload it to the "GAM Reports" folder of usermgr@domain.com, add a timestamp to the title.
```
gam print users fields id,name todrive tdtitle "User IDs and Names" tdtimestamp true tduser usermgr@domain.com tdparent "GAM Reports"
```

Generate a list of CrOS devices and update an existing sheet in a Google spreadsheet. The sheet ID is preserved so other appplications can access the data using the file ID and sheet ID.
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

Suppose you have a spreadsheet with sheets `Monday` ... `Friday`, `Backup Monday` ... `Backup Friday` and `Latest`.
Each day you run a report to update the current day sheet (`Tuesday`), you want to backup the data first (`Backup Tuesday`) and
you want the updated data copied to `Latest` so you don't have to remember what the day of the week is.
```
gam redirect csv - todrive tdfileid <DriveFileID> tdupdatesheet tdsheet Tuesday tdbackupsheet "Backup Tuesday" tdcopysheet "Latest" ...
```
## Limited Service Account Access
If you want to limit a user's service account access but still allow `todrive',
issue the following command and authorize the additional service account APIs:
```
gam user user@domain.com update serviceaccount`

Authorize these APIs:

Drive API - todrive
Gmail API - Send Messages - including todrive
Sheets API - todrive
```

## No Service Account Access
By default, `todrive` uses service account access to upload files, set sheet names and send email notifications.

If it is not possible to allow the user any service account access (this is not common),
perform the following command so that the user can upload files with `todrive` using client access.
```
gam config todrive_clientaccess true save
```
Issue the following command and authorize the additional client access APIs:
```
gam oauth create

Authorize these APIs:
Drive API - todrive_clientaccess
Gmail API - todrive_clientaccess
Sheets API - todrive_clientaccess
```
When `todrive_clientaccess` is true, `todrive_user\tduser` is ignored, all actions are performed as the user specified in `oauth2.txt`.

