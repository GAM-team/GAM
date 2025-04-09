# User Contacts
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Special quoting for contact groups](#special-quoting-for-contact-groups)
- [Create user contacts](#create-user-contacts)
- [Select user contacts](#select-user-contacts)
- [Update user contacts](#update-user-contacts)
- [Delete user contacts](#delete-user-contacts)
- [Clear old email addresses from contacts](#clear-old-email-addresses-from-contacts)
- [Delete duplicate email addresses from contacts](#delete-duplicate-email-addresses-from-contacts)
- [Manage user contact photos](#manage-user-contact-photos)
- [Display user contacts](#display-user-contacts)
- [Manage user contact groups](#manage-user-contact-groups)
- [Display user contact groups](#display-user-contact-groups)

## Notes
As of version `6.08.00`, GAM uses the People API to manage user contacts rather than the Contacts API.

Most commands will work unchanged but Google has completely changed how the data is presented. If you
have scripts that process the output from `print contacts` for example, they will have to be changed.

You might want to keep an older version of GAM available so you can compare the output from the two
versions and make adjustments as necessary.

If you manage contacts in the contact group "Other Contacts", you will need to use an older version,
as the People API has very little support for this.

As of version `6.14.04`, There is now support for managing "Other Contacts".

[Users - People - Contacts & Profiles](Users-People-Contacts-Profiles)

## API documentation
* https://developers.google.com/admin-sdk/domain-shared-contacts/

## Query documentation
* https://developers.google.com/google-apps/contacts/v3/reference#contacts-query-parameters-reference

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

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
         (gcsdoc <StorageBucketObjectName>)
```
```
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

<ContactID> ::= <String>
<ContactIDList> ::= "<ContactID>(,<ContactID>)*"
<ContactEntity> ::=
        <ContactIDList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>
<ContactGroupID> ::= id:<String>
<ContactGroupName> ::= <String>
<ContactGroupItem> ::= <ContactGroupID>|<ContactGroupName>
<ContactGroupList> ::= "<ContactGroupItem>(,<ContactGroupItem>)*"
<ContactGroupEntity> ::=
        <ContactGroupList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>
<UserContactSelection> ::=
        [query <QueryContact>]
        [(selectcontactgroup <ContactGroupItem>)|selectothercontacts]
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
        (contactgroup clear)|
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
        contactgroup|
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

<ContactGroupAttribute> ::=
        (name <String>)
```
## Special quoting for contact groups
As contact group names can contain spaces, some care must be used when entering `<ContactGroupList>` and `<ContactEntity>`.

Suppose you enter the command `gam info contactgroup "Sales Contacts"`

The shell strips the `"` leaving a single argument `Sales Contacts`; as gam is expecting a list, it splits the argument on space leaving two items and then tries to process `Sales` and `Contacts`, not what you want.

You must enter: `gam info contactgroups "'Sales Contacts'"`

The shell strips the `"` leaving a single argument `'Sales Contacts'`; as gam is expecting a list, it splits the argument on space while honoring the `'` leaving one item `Sales Contacts` and correctly processes the item.

For multiple names you must enter: `gam info contactgroup "'Sales Contacts','Tech Contacts'"`

## Create user contacts
```
gam <UserTypeEntity> create contact <ContactAttribute>+
        (contactgroup <ContactGroupItem>)*
```
You may specify zero or more contact groups with `(contactgroup <ContactGroupItem>)*`;
these contact groups define the complete contact group list for the contact.

## Select user contacts
You specify contacts by ID or by selection qualifiers.
```
<ContactID> ::= <String>
<ContactIDList> ::= "<ContactID>(,<ContactID>)*"
<ContactEntity> ::=
        <ContactIDList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>
<ContactGroupID> ::= id:<String>
<ContactGroupName> ::= <String>
<ContactGroupItem> ::= <ContactGroupID>|<ContactGroupName>
<ContactGroupList> ::= "<ContactGroupItem>(,<ContactGroupItem>)*"
<ContactGroupEntity> ::=
        <ContactGroupList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>
<UserContactSelection> ::=
        [query <QueryContact>]
        [(selectcontactgroup <ContactGroupItem>)|selectothercontacts]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]
        [updated_min <Date>]
```
Selection qualifiers may be combined.
* `query <QueryContact>` - Fulltext query on contacts data fields. See: https://developers.google.com/contacts/v3/reference#contacts-query-parameters-reference
* `selectcontactgroup <ContactGroupItem>` - Specify a specific contact group
* `selectothercontacts` - Specify the "Other Contacts" group
* `emailmatchpattern <REMatchPattern>` - Select contacts that have an email address matching `<REMatchPattern>`
* `emailmatchpattern <REMatchPattern> emailmatchtype work|home|other|<String>` - Select contacts that have an email address matching `<REMatchPattern>` and a specific type
* `emailmatchpattern ".*" emailmatchtype work|home|other|<String>` - Select contacts that have any email address with a specific type
* `updated_min <Date>` - Swelewct contacts updated since `<Date>`

## Update user contacts
```
gam <UserTypeEntity> update contacts <ContactEntity>|(<UserContactSelection> endquery) <ContactAttribute>+
        (contactgroup <ContactGroupItem>)*|((addcontactgroup <ContactGroupItem>)* (removecontactgroup <ContactGroupItem>)*)
```
User contacts may be assigned to Contact Groups or may be unassigned and appear under Other Contacts. The Contacts API
allows selection of contacts by Contact Group; in Gam you specify `selectcontactgroup <ContactGroupItem>`. However, the API
does not allow selection of contacts from the Other Contacts section. If you specify `selectothercontacts`, then GAM will select only the contacts from "Other Contacts".

You may specify zero or more contact groups with `(contactgroup <ContactGroupItem>)*`;
these contact groups define the complete contact group list for the contact.

You may specify zero or more contact groups with `(addcontactgroup <ContactGroupItem>)*`;
these contact groups will be added to the current contact group list for the contact.

You may specify zero or more contact groups with `(removecontactgroup <ContactGroupItem>)*`;
these contact groups will be removed from the current contact group list for the contact.

When `contactgroup` is specified, `addcontactgroup` and `removecontactgroup` are ignored.

You can clear all contact groups from a contact with `contactgroup clear`.

## Delete user contacts
```
gam <UserTypeEntity> delete contacts <ContactEntity>|<UserContactSelection>
```
User contacts may be assigned to Contact Groups or may be unassigned and appear under Other Contacts. The Contacts API
allows selection of contacts by Contact Group; in Gam you specify `selectcontactgroup <ContactGroupItem>`. However, the API
does not allow selection of contacts from the Other Contacts section. If you specify `selectothercontacts`, then GAM will select only the contacts from "Other Contacts".

## Clear old email addresses from contacts
```
gam <UserTypeEntity> clear contacts <ContactEntity>|<UserContactSelection>
        [emailclearpattern <REMatchPattern> [emailcleartype work|home|other|<String>]]
        [delete_cleared_contacts_with_no_emails]
```
Typically, you would select contacts by `emailmatchpattern <REMatchPattern>` (and optionally `emailmatchtype work|home|other|<String>`),
then the matching email addresses will be cleared from the user's contact's email list. The contact itself is updated, not deleted.
Email addresses that don't match will be unaffected. If you want to clear all email addresses of a particular type,
use `emailmatchpattern ".*" emailmatchtype work|home|other|<String>`.

You can specify `emailclearpattern <REMatchPattern>` (and optionally `emailcleartype work|home|other|<String>`) if you want to
clear email addresses other than the ones used to match the contacts or if you specify `<ContactEntity>`.

A contact may contain no email addresses after matching email addresses are cleared. If you do not want to keep contacts with no
email addresses after clearing, use the `delete_cleared_contacts_with_no_emails` option and they will be deleted.
Contacts with no email addresses before clearing will not be affected.

### Example
For example, you want to eliminate any contact email addresses that use your company's old domain name.
First, do `show contacts emailmatchpattern "<REMatchPattern>"` to verify that you're getting the right contacts.
Then do `clear contacts emailmatchpattern "<REMatchPattern>"` to clear the email addresses.
```
gam user user@domain.com show contacts emailmatchpattern ".*@olddomain.com" fields email
gam user user@domain.com clear contacts emailmatchpattern ".*@olddomain.com"
```

## Delete duplicate email addresses from contacts
If the same email address appears multiple times within a contact, all but the first will be deleted.
```
gam <UserTypeEntity> dedup contacts [<ContactEntity>|<UserContactSelection>] [matchType [<Boolean>]]
```
If neither `<ContactEntity>` or `<UserContactSelection>` is specified, all contacts are checked for duplicates.

By default, the email type `work|home|other|<String>` is ignored, all duplicates, regardless of type,
will be deleted. If `matchtype` is true, only duplicate email addresses with the same type will be deleted.

## Manage user contact photos
```
gam <UserTypeEntity> update contactphotos <ContactEntity>|<UserContactSelection>
        [drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]
gam <UserTypeEntity> get contactphotos <ContactEntity>|<UserContactSelection>
         [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
gam <UserTypeEntity> delete contactphotos <ContactEntity>|<UserContactSelection>

```
The default directory is the current working directory, `drivedir` specifies the value of drive_dir from gam.cfg and
`sourcefolder/targetfolder <FilePath>` specifies a user-chosen path.
`<FileNamePattern>` can contain the strings `#email#` and `#contactid#` which will be replaced by the the contact's primary emailaddress or the contact ID.
If not specified, `<FileNamePattern>` defaults to `#contactid#.jpg`.

## Display user contacts
```
gam <UserTypeEntity> info contacts <ContactEntity>
        [basic|full|countsonly] [showgroups]
        [fields <ContactFieldNameList>] [formatjson]
gam <UserTypeEntity> show contacts <UserContactSelection>
        [basic|full|countsonly] [showgroups] [showdeleted]
        [orderby <ContactOrderByFieldName> [ascending|descending]]
        [fields <ContactFieldNameList>] [formatjson]
```
If `countsonly` is specified, no contact fields are displayed, just the number of contacts.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print contacts [todrive <ToDriveAttribute>*] <UserContactSelection>
        [basic|full|countsonly] [showgroups|showgroupnameslist] [showdeleted]
        [orderby <ContactOrderByFieldName> [ascending|descending]]
        [fields <ContactFieldNameList>] [formatjson [quotechar <Character>]]
```
If `countsonly` is specified, no contact fields are displayed, just the number of contacts.

If `showgroups` is specified, contact group information, if any, will be displayed for each contact.

If `showgroupnameslist` and `formatjson` are both specified, the key `ContactGroupsList` with a list of contact group names
will be added to the JSON output.
This key and its values can be used when creating contacts with the `json` option to set contact groups.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage user contact groups
```
gam <UserTypeEntity> create contactgroup <ContactGroupAttribute>+
gam <UserTypeEntity> update contactgroup <ContactGroupItem> <ContactGroupAttribute>+
gam <UserTypeEntity> delete contactgroups <ContactGroupEntity>
```
## Display user contact groups
```
gam <UserTypeEntity> info contactgroups <ContactGroupEntity>
        [formatjson]
gam <UserTypeEntity> show contactgroups [updated_min <Date>]
        [basic|full] [showdeleted]
        [orderby <ContactOrderByFieldName> [ascending|descending]]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print contactgroups [todrive <ToDriveAttribute>*] [updated_min <Date>]
        [basic|full] [showdeleted]
        [orderby <ContactOrderByFieldName> [ascending|descending]]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Example
Display a user's contacts from all of her contact groups.
```
gam user user@domain.com print contactgroups | gam redirect stderr - multiprocess redirect csv ./UserContacts.csv multiprocess csv - gam user "~User" print contacts selectcontactgroup "~ContactGroupID"
```
Details:
* `gam user user@domain.com print contactgroups` - Display contact groups as CSV on stdout
* `gam redirect stderr - multiprocess` - When processing CSV input, organize Getting/Got messages
* `redirect csv ./UserContacts.csv multiprocess` - Intelligently combine CSV output from all contact groups
* `csv - gam user "~User" print contacts selectcontactgroup "~ContactGroupID"` - Read contact groups CSV from stdin and process
