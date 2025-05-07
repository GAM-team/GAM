# Domain Shared Contacts
- [API documentation](#api-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Create domain shared contacts](#create-domain-shared-contacts)
- [Select domain shared contacts](#select-domain-shared-contacts)
- [Update domain shared contacts](#update-domain-shared-contacts)
- [Delete domain shared contacts](#delete-domain-shared-contacts)
- [Clear old email addresses from contacts](#clear-old-email-addresses-from-contacts)
- [Delete duplicate email addresses from contacts](#delete-duplicate-email-addresses-from-contacts)
- [Manage domain contact photos](#manage-domain-contact-photos)
- [Display domain shared contacts](#display-domain-shared-contacts)
- [Display global address list](#display-global-address-list)

## API documentation
* [Domain Shared Contacts API](https://developers.google.com/admin-sdk/domain-shared-contacts)

## Definitions
* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
```
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>

<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)

<NoteContent> ::=
        ((<String>)|
         (file <FileName> [charset <Charset>])|
         (gdoc <UserGoogleDoc>)|
         (gcsdoc <StorageBucketObjectName>))

<Date> ::=
        <Year>-<Month>-<Day> |
        (+|-)<Number>(d|w|y) |
        never|
        today
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<QueryContact> ::= <String>
        https://developers.google.com/google-apps/contacts/v3/reference#contacts-query-parameters-reference

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<ContactID> ::= <String>
<ContactIDList> ::= "<ContactID>(,<ContactID>)*"
<ContactEntity> ::=
        <ContactIDList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<ContactSelection> ::=
        [query <QueryContact>]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]
        [updated_min <Date>]
```
```
<ContactBasicAttribute> ::=
        (additionalname|middlename <String>)|
        (billinginfo <String>)|
        (birthday <Date>)|
        (directoryserver <String>)|
        (familyname|lastname <String>)|
        (gender female|male)|
        (givenname|firstname <String>)|
        (initials <String>)|
        (language <Language>)|
        (location <String>)|
        (maidenname <String>)|
        (mileage <String>)|
        (name <String>)|
        (nickname <String>)|
        (note <NoteContent>)|
        (occupation <String>)|
        (prefix <String>)|
        (priority low|normal|high)
        (sensitivity confidential|normal|personal|private)
        (shortname <String>)|
        (subject <String>)|
        (suffix <String>)
```
```
<ContactMultiAttribute> ::=
        (address work|home|other|<String>
                (formatted|unstructured <String>)|(streetaddress <String>)|
                (pobox <String>)|(neighborhood <String>)|(locality <String>)|
                (region <String>)|(postalcode <String>)|(country <String>)*
                notprimary|primary)|
        (calendar work|home|free-busy|<String> <URL>
                notprimary|primary)|
        (email work|home|other|<String> <EmailAddress>
                notprimary|primary)|
        (event anniversary|other|<String> <Date>)|
        (externalid account|customer|network|organization|<String> <String>)|
        (hobby <String>)|
        (im work|home|other|<String>
                aim|gtalk|icq|jabber|msn|net_meeting|qq|skype|yahoo <String>
                notprimary|primary)|
        (jot work|home|other|keywords|user> <String>)|
        (organization work|other|<String> <String>
                (location <String>)|(department <String>)|(title <String>)|
                (jobdescription <String>)|(symbol <String>)*
                notprimary|primary)|
        (phone work|home|other|fax|work_fax|home_fax|other_fax|main|company_main|
                assistant|mobile|work_mobile|pager|work_pager|car|radio|callback|
                isdn|telex|tty_tdd|<String> <String>
                notprimary|primary)|
        (relation spouse|child|mother|father|parent|brother|sister|friend|relative|
                domestic_partner|manager|assistant|referred_by|partner|<String> <String>)|
        (userdefinedfield <String> <String>)|
        (website home_page|blog|profile|work|home|other|ftp|reservations|
                app_install_page|<String> <URL> notprimary|primary)

<ContactClearAttribute> ::=
        (address clear)|
        (calendar clear)|
        (email clear)|
        (event clear)|
        (externalid clear)|
        (hobby clear)|
        (im clear)|
        (jot clear)|
        (organization clear)|
        (phone clear)|
        (relation clear)|
        (userdefinedfield clear)|
        (website clear)
```
```
<ContactAttribute> ::=
        <JSONData>|
        <ContactBasicAttribute>|
        <ContactMultiAttribute>|
        <ContactClearAttribute>
```
```
<ContactFieldName> ::=
        additionalname|middlename|
        address|
        billinginfo|
        birthday|
        calendar|
        directoryserver|
        email|
        event|
        externalid|
        familyname|lastname|
        gender|
        givenname|firstname|
        hobby|
        im|
        initials|
        jot|
        language|
        location|
        maidenname|
        mileage|
        name|
        nickname|
        note|
        occupation|
        organization|
        phone|
        prefix|
        priority|
        relation|
        sensitivity|
        shortname|
        subject|
        suffix|
        updated|
        userdefinedfield|
        website
<ContactFieldNameList> ::= "<ContactFieldName>(,<ContactFieldName>)*"

<ContactOrderByFieldName> ::=
        lastmodified
```
## Create domain shared contacts
```
gam create contact <ContactAttribute>+
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
```
By default, the domain name and contact ID are displayed on stdout.
* `csv [todrive <ToDriveAttribute>*]` - Write domain name and contact ID values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output
* `returnidonly` - Display just the contact ID on stdout

To retrieve the contact ID with `returnidonly`:
```
Linux/MacOS
contactId=$(gam create contact ... returnidonly)
Windows PowerShell
$contactId = & gam create contact ... returnidonly
```

## Select domain shared contacts
You specify contacts by ID or by selection qualifiers.
```
<ContactID> ::= <String>
<ContactIDList> ::= "<ContactID>(,<ContactID>)*"
<ContactEntity> ::=
        <ContactIDList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<ContactSelection> ::=
        [query <QueryContact>]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]
        [updated_min <Date>]
```
Selection qualifiers may be combined.
* `query <QueryContact>` - Fulltext query on contacts data fields. See: https://developers.google.com/contacts/v3/reference#contacts-query-parameters-reference
* `emailmatchpattern <REMatchPattern>` - Select contacts that have an email address matching `<REMatchPattern>`
* `emailmatchpattern <REMatchPattern> emailmatchtype work|home|other|<String>` - Select contacts that have an email address matching `<REMatchPattern>` and a specific type
* `emailmatchpattern ".*" emailmatchtype work|home|other|<String>` - Select contacts that have any email address with a specific type
* `updated_min <Date>` - Select contacts updated since `<Date>`

## Update domain shared contacts
```
gam update contacts <ContactEntity>|<ContactSelection> <ContactAttribute>+
```
## Delete domain shared contacts
```
gam delete contacts <ContactEntity>|<ContactSelection>
```
## Clear old email addresses from contacts
```
gam clear contacts <ContactEntity>|<ContactSelection>
        [emailclearpattern <REMatchPattern> [emailcleartype work|home|other|<String>]]
        [delete_cleared_contacts_with_no_emails]
```
Typically, you would select contacts by `emailmatchpattern <REMatchPattern>` (and optionally `emailmatchtype work|home|other|<String>`),
then the matching email addresses will be cleared from the domiain contact's email list. The contact itself is updated, not deleted.
Email addresses that don't match will be unaffected. If you want to clear all email addresses of a particular type,
use `emailmatchpattern ".*" emailmatchtype work|home|other|<String>`.

You can specify `emailclearpattern <REMatchPattern>` (and optionally `emailcleartype work|home|other|<String>`) if you want to
clear email addresses other than the ones used to match the contacts or if you specify `<ContactEntity>`.

A contact may contain no email addresses after matching email addresses are cleared. If you do not want to keep contacts with no
email addresses after clearing, use the `delete_cleared_contacts_with_no_emails` option and they will be deleted.
Contacts with no email addresses before clearing will not be affected.

## Delete duplicate email addresses from contacts
If the same email address appears multiple times within a contact, all but the first will be deleted.
```
gam dedup contacts [<ContactEntity>|<ContactSelection>] [matchType [<Boolean>]]
```
If neither `<ContactEntity>` or `<ContactSelection>` is specified, all contacts are checked for duplicates.

By default, the email type `work|home|other|<String>` is ignored, all duplicates, regardless of type,
will be deleted. If `matchtype` is true, only duplicate email addresses with the same type will be deleted.

## Manage domain contact photos
Due to an API change by Google, only the `get contactphotos` command works; I've reported this
to Google but they've done nothing to make `update|delete contactphotos` work.
```
gam get contactphotos <ContactEntity>|<ContactSelection>
        [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
gam update contactphotos <ContactEntity>|<ContactSelection>
        [drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]
gam delete contactphotos <ContactEntity>|<ContactSelection>
```
The default directory is the current working directory, `drivedir` specifies the value of drive_dir from gam.cfg and
`sourcefolder/targetfolder <FilePath>` specifies a user-chosen path.
`<FileNamePattern>` can contain the strings `#email#` and `#contactid#` which will be replaced by the the contact's primary emailaddress or the contact ID.
If not specified, `<FileNamePattern>` defaults to `#contactid#.jpg`.

## Display domain shared contacts
```
gam info contacts <ContactEntity>
        [basic|full]
        [fields <ContactFieldNameList>] [formatjson]
gam show contacts [<ContactSelection>]
        [basic|full|countsonly] [showdeleted]
        [orderby <ContactOrderByFieldName> [ascending|descending]]
        [fields <ContactFieldNameList>] [formatjson]
```
If `<ContactSelection>` is not specified, all contacts are displayed.

If `countsonly` is specified, no contact fields are displayed, just the number of contacts.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print contacts [todrive <ToDriveAttribute>*] [<ContactSelection>]
        [basic|full|countsonly] [showdeleted]
        [orderby <ContactOrderByFieldName> [ascending|descending]]
        [fields <ContactFieldNameList>] [formatjson [quotechar <Character>]]
```
If `<ContactSelection>` is not specified, all contacts are displayed.

If `countsonly` is specified, no contact fields are displayed, just the number of contacts.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display global address list
As of mid-October 2024, Google deprecated the API that retrieved the Global Address List.

These commands are a work-around.
```
gam config csv_output_row_filter "includeInGlobalAddressList:boolean:true" redirect csv ./UserGAL.csv print users fields name,gal
gam config csv_output_row_filter "includeInGlobalAddressList:boolean:true" batch_size 25 redirect csv ./GroupGAL.csv print groups fields name,gal
```
