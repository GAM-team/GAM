# Users - People - Contacts & Profiles
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Special quoting for contact groups](#special-quoting-for-contact-groups)
- [Select User Contacts](#select-user-contacts)
- [Create User Contacts](#create-user-contacts)
- [Update User Contacts](#update-user-contacts)
- [Delete User Contacts](#delete-user-contacts)
- [Clear Old Email Addresses From Contacts](#clear-old-email-addresses-from-contacts)
- [Delete Duplicate Email Addresses Within Contacts](#delete-duplicate-email-addresses-within-contacts)
- [Replace Domain Names in Contact Email Addresses](#replace-domain-names-in-contact-email-addresses)
- [Display User Contacts](#display-user-contacts)
- [Manage User Contact Photos](#manage-user-contact-photos)
- [Copy User Other Contacts to My Contacts](#copy-user-other-contacts-to-my-contacts)
- [Move User Other Contacts to My Contacts](#move-user-other-contacts-to-my-contacts)
- [Update User Other Contacts](#update-user-other-contacts)
- [Delete User Other Contacts](#delete-user-other-contacts)
- [Display User Other Contacts](#display-user-other-contacts)
- [Manage User Contact Groups](#manage-user-contact-groups)
- [Display User Contact Groups](#display-user-contact-groups)
- [Display User People Profile](#display-user-people-profile)
- [Copy User Contacts to another User](#copy-user-contacts-to-another-user)

## Notes
As of version `6.08.00`, GAM uses the People API to manage user contacts rather than the Contacts API.

Most commands will work unchanged but Google has completely changed how the data is presented. If you
have scripts that process the output from `print contacts` for example, they will have to be changed.

You might want to keep an older version of GAM available so you can compare the output from the two
versions and make adjustments as necessary.

If you manage contacts in the contact group "Other Contacts", you will need to use an older version,
as the People API has very little support for this.

To use these commands you must add the `People API` to your project and authorize the appropriate scopes:
* `Client Access`
  * `People API (supports readonly)`
  * `People Directory API - read only`.
* `Service Account Access`
  * `OAuth2 API`: https://www.googleapis.com/auth/userinfo.profile
  * `People API (supports readonly)`: https://www.googleapis.com/auth/contacts
  * `People API - Other Contacts - read only`: https://www.googleapis.com/auth/contacts.other.readonly
  * `People Directory API - read only`: https://www.googleapis.com/auth/directory.readonly
```
gam update project
gam oauth create
gam user user@domain.com update serviceaccount
```

## API documentation
* [People API Migration](https://developers.google.com/people)
* [Contacts API Migration](https://developers.google.com/people/contacts-api-migration)
* [People API](https://developers.google.com/people/api/rest)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |
<QueryContact> ::= <String>

<PeopleResourceName> ::= people/<String>
<PeopleResourceNameList> ::= "<PeopleResourceName>(,<PeopleResourceName>)*"
<PeopleResourceNameEntity> ::=
        <PeopleResourceNameNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<PeopleContactGroupName> ::= <String>
<PeopleContactGroupResourceName> ::= (contactgroup/<String>)|<String>
<PeopleContactGroupItem> ::= <PeopleContactGroupResourceName>|<PeopleContactGroupName>
<PeopleContactGroupList> ::= "<PeopleContactGroupItem>(,<PeopleContactGroupItem>)*"
<PeopleContactGroupEntity> ::=
        <PeopleContactGroupList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<PeopleUserContactSelection> ::=
        [(selectcontactgroup <PeopleContactGroupItem>)|
            [query <QueryContact>]]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]
<PeoplePrintShowUserContactSelection> ::=
        [(selectcontactgroup <PeopleContactGroupItem>)|(filtercontactgroup <PeopleContactGroupItem>)|
            ([query <QueryContact>] [selectmaincontacts|selectothercontacts])]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]

<PeopleContactAttribute> ::=
        (additionalname|middlename <String>)|
        (address clear|(work|home|other|<String> ((formatted|unstructured <String>)|(streetaddress <String>)|(pobox <String>)|
            (neighborhood <String>)|(locality <String>)|(region <String>)|(postalcode <String>)|(country <String>))* notprimary|primary))|
        (billinginfo <String>)|
        (biography|biographies <String>|(file <FileName> [charset <Charset>])|(gdoc <UserGoogleDoc>))|
        (birthday <Date>)|
        (calendar clear|(work|home|free-busy|<String> <URL> notprimary|primary))|
        (clientdata <String> <String>)|
        (directoryserver <String>)|
        (email clear|(work|home|other|<String> <EmailAddress> notprimary|primary))|
        (event clear|(anniversary|other|<String> <Date>))|
        (externalid clear|(account|customer|network|organization|<String> <String>))|
        (familyname|lastname <String>)|
        (fileas <String>)|
        (gender female|male)|
        (givenname|firstname <String>)|
        (im clear|(work|home|other|<String> aim|gtalk|icq|jabber|msn|net_meeting|qq|skype|yahoo <String> notprimary|primary))|
        (interests clear|<String>)|
        (initials <String>)|
        (jot clear|(work|home|other|keywords|user> <String>))|
        <JSONData>|
        (language <Language>)|
        (locale clear|<Language>)|
        (location clear|<String>)|
        (maidenname <String>)|
        (mileage <String>)|
        (name <String>)|
        (nickname <String>)|
        (note <String>|(file <FileName> [charset <Charset>])|(gdoc <UserGoogleDoc>))|
        (occupation clear|<String>)|
        (organization clear|(work|other|<String> <String> ((location <String>)|(department <String>)|(title <String>)|(jobdescription <String>)|(symbol <String>))* notprimary|primary))|
        (phone clear|(work|home|other|fax|work_fax|home_fax|other_fax|main|company_main|assistant|mobile|work_mobile|pager|work_pager|car|radio|callback|isdn|telex|tty_tdd|<String> <String> notprimary|primary))|
        (prefix <String>)|
        (priority low|normal|high)
        (relation clear|(spouse|child|mother|father|parent|brother|sister|friend|relative|domestic_partner|manager|assistant|referred_by|partner|<String> <String>))|
        (sensitivity confidential|normal|personal|private)
        (shortname <String>)|
        (skills clear|<String>)|
        (subject <String>)|
        (suffix <String>)|
        (userdefinedfield clear|(<String> <String>))|
        (url|website clear|(app_install_page|blog|ftp|home|home_page|other|profile|reservations|work|<String> <URL> notprimary|primary))

For address, email, phone and url, the type <String> can be empty.
address "" formatted "My Address" primary
email "" user@gmail.com primary
phone "" "510-555-1212" primary
url "" "https://www.domain.com" primary
```
```
<PeopleFieldName> ::=
        addresses|
        ageranges|
        biographies|
        birthdays|
        calendarurls|
        clientdata|
        coverphotos|
        emailaddresses|
        events|
        externalids|
        genders|
        imclients|
        interests|
        locales|
        locations|
        memberships|
        metadata|
        misckeywords|
        names|
        nicknames|
        occupations|
        organizations|
        phonenumbers|
        photos|
        relations|
        sipaddresses|
        skills|
        urls|
        updated|updatetime|
        userdefined
<PeopleFieldNameList> ::= "<PeopleFieldName>(,<PeopleFieldName>)*"
```
```
<PeopleContactGroupAttribute> ::=
        (clientdata <String> <String>)|
        <JSONData>|
        name <String>

<PeopleContactGroupFieldName> ::=
        clientdata|
        grouptype|
        membercount|
        metadata|
        name
<PeopleContactGroupFieldNameList> ::= "<PeopleContactGroupFieldName>(,<PeopleContactGroupFieldName>)*"
```
```
<OtherContactsResourceName> ::= otherContacts/<String>
<OtherContactsResourceNameList> ::= "<OtherContactsResourceName>(,<OtherContactsResourceName>)*"
<OtherContactsResourceNameEntity> ::=
        <OtherContactsResourceNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<OtherContactsSelection> ::=
        [query <QueryContact>]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]

<OtherContactsFieldName> ::=
        emailaddresses|
        metadata|
        names|
        phonenumbers|
        photos
<OtherContactsFieldNameList> ::= "<OtherContactsFieldName>(,<OtherContactsFieldName>)*"
```

## Special quoting for contact groups
As contact group names can contain spaces, some care must be used when entering `<ContactGroupList>` and `<ContactEntity>`.

Suppose you enter the command `gam info contactgroup "Sales Contacts"`

The shell strips the `"` leaving a single argument `Sales Contacts`; as gam is expecting a list, it splits the argument on space leaving two items and then tries to process `Sales` and `Contacts`, not what you want.

You must enter: `gam info contactgroups "'Sales Contacts'"`

The shell strips the `"` leaving a single argument `'Sales Contacts'`; as gam is expecting a list, it splits the argument on space while honoring the `'` leaving one item `Sales Contacts` and correctly processes the item.

For multiple names you must enter: `gam info contactgroup "'Sales Contacts','Tech Contacts'"`

## Select User Contacts
You specify contacts by ID or by selection qualifiers.
### Selections for commands other than `print|show`
```
<PeopleUserContactSelection> ::=
        [(selectcontactgroup <PeopleContactGroupItem>)|
            (query <QueryContact>)]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]
```
Selections processed by People API
* `selectcontactgroup <PeopleContactGroupItem>` - Specify a specific contact group
* `query <QueryContact>` - Fulltext query on contacts data fields. See: https://developers.google.com/contacts/v3/reference#contacts-query-parameters-reference

Selections processed by GAM 
* `emailmatchpattern <REMatchPattern>` - Select contacts that have an email address matching `<REMatchPattern>`
* `emailmatchpattern <REMatchPattern> emailmatchtype work|home|other|<String>` - Select contacts that have an email address matching `<REMatchPattern>` and a specific type
* `emailmatchpattern ".*" emailmatchtype work|home|other|<String>` - Select contacts that have any email address with a specific type

### For `print|show` commands
```
<PeoplePrintShowUserContactSelection> ::=
        [(selectcontactgroup <PeopleContactGroupItem>)|(filtercontactgroup <PeopleContactGroupItem>)|
            ([query <QueryContact>] [selectmaincontacts|selectothercontacts])]
        [emailmatchpattern <REMatchPattern> [emailmatchtype work|home|other|<String>]]
```
Selections processed by People API
* `selectcontactgroup <PeopleContactGroupItem>` - Specify a specific contact group; individual contacts downloaded
* `query <QueryContact>` - Fulltext query on contacts data fields. See: https://developers.google.com/contacts/v3/reference#contacts-query-parameters-reference
* `selectmaincontacts` - Specify "Contacts"
* `selectothercontacts` - Specify "Other Contacts"

Selections processed by GAM 
* `filtercontactgroup <PeopleContactGroupItem>` - Specify a specific contact group; all contacts downloaded, then filtered
* `emailmatchpattern <REMatchPattern>` - Select contacts that have an email address matching `<REMatchPattern>`
* `emailmatchpattern <REMatchPattern> emailmatchtype work|home|other|<String>` - Select contacts that have an email address matching `<REMatchPattern>` and a specific type
* `emailmatchpattern ".*" emailmatchtype work|home|other|<String>` - Select contacts that have any email address with a specific type

When `selectcontactgroup <PeopleContactGroupItem>` is used in these commands, GAM makes an API call
to get the list of contacts in `<PeopleContactGroupItem>` and then makes an API call per contact to get the details; this may exceed quota limits.

When `filtercontactgroup <PeopleContactGroupItem>` is used, GAM makes an API call to get all contacts and
then filters the list to only those in `<PeopleContactGroupItem>`; quota limits should not apply.

## Create User Contacts
```
gam <UserTypeEntity> create contact
        [<PeopleContactAttribute>+]
        (contactgroup <PeopleContactGroupItem>)*
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
```
You may specify zero or more contact groups with `(contactgroup <PeopleContactGroupItem>)*`;
these contact groups define the complete contact group list for the contact.

By default, the user name and contact ID are displayed on stdout.
* `csv [todrive <ToDriveAttribute>*]` - Write user name and contact ID values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output
* `returnidonly` - Display just the contact ID on stdout

To retrieve the contact ID with `returnidonly`:
```
Linux/MacOS
contactId=$(gam user user@domain.com create contact ... returnidonly)
Windows PowerShell
$contactId = & gam user user@domain.com create contact ... returnidonly
```

## Update User Contacts
```
gam <UserTypeEntity> update contacts
        <PeopleResourceNameEntity>|(<PeopleUserContactSelection> endquery)
        [<PeopleContactAttribute>+]
        (contactgroup <PeopleContactGroupItem>)*|((addcontactgroup <PeopleContactGroupItem>)* (removecontactgroup <PeopleContactGroupItem>)*)
```
User contacts may be assigned to Contact Groups or may be unassigned and appear under My Contacts. The People API
allows selection of contacts by Contact Group; in Gam you specify `selectcontactgroup <PeopleContactGroupItem>`. However, the API
does not allow selection of contacts from the Other Contacts section. 

You may specify zero or more contact groups with `(contactgroup <PeopleContactGroupItem>)*`;
these contact groups define the complete contact group list for the contact.

You may specify zero or more contact groups with `(addcontactgroup <PeopleContactGroupItem>)*`;
these contact groups will be added to the current contact group list for the contact.

You may specify zero or more contact groups with `(removecontactgroup <PeopleContactGroupItem>)*`;
these contact groups will be removed from the current contact group list for the contact.

When `contactgroup` is specified, `addcontactgroup` and `removecontactgroup` are ignored.

You can clear all contact groups from a contact with `contactgroup clear`.

## Delete User Contacts

```
gam <UserTypeEntity> delete contacts
        <PeopleResourceNameEntity>|<PeopleUserContactSelection>
```
User contacts may be assigned to Contact Groups or may be unassigned and appear under My Contacts. The People API
allows selection of contacts by Contact Group; in Gam you specify `selectcontactgroup <PeopleContactGroupItem>`. However, the API
does not allow selection of contacts from the Other Contacts section.

## Clear Old Email Addresses From Contacts
```
gam <UserTypeEntity> clear contacts
        <PeopleResourceNameEntity>|<PeopleUserContactSelection>
        [emailclearpattern <REMatchPattern>] [emailcleartype work|home|other|<String>]
        [delete_cleared_contacts_with_no_emails]
```
Typically, you would select contacts by `emailmatchpattern <REMatchPattern>` (and optionally `emailmatchtype work|home|other|<String>`),
then the matching email addresses will be cleared from the user's contact's email list. The contact itself is updated, not deleted.
Email addresses that don't match will be unaffected. If you want to clear all email addresses of a particular type,
use `emailmatchpattern ".*" emailmatchtype work|home|other|<String>`.

You can specify `emailclearpattern <REMatchPattern>` (and optionally `emailcleartype work|home|other|<String>`) if you want to
clear email addresses other than the ones used to match the contacts or if you specify `<PeopleResourceNameEntity>`.

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

## Delete Duplicate Email Addresses Within Contacts
If the same email address appears multiple times within a contact, all but the first will be deleted.
```
gam <UserTypeEntity> dedup contacts
        [<PeopleResourceNameEntity>|<PeopleUserContactSelection>]
        [matchType [<Boolean>]]
```
If neither `<PeopleResourceNameEntity>` or `<PeopleUserContactSelection>` is specified, all contacts are checked for duplicates.

By default, the email type `work|home|other|<String>` is ignored, all duplicates, regardless of type,
will be deleted. If `matchtype` is true, only duplicate email addresses with the same type will be deleted.

## Replace Domain Names in Contact Email Addresses
This command replaces domain names in contact email addresses; this can be useful
when merging/renaming domains; multiple `domain <OldDomainName> <NewDomainName>`
options can be specified.
```
gam <UserTypeEntity> replacedomain contacts
        [<PeopleResourceNameEntity>|<PeopleUserContactSelection>]
        (domain <OldDomainName> <NewDomainName>)+
```
If neither `<PeopleResourceNameEntity>` or `<PeopleUserContactSelection>` is specified, all contact email addresses are updated
as applicable.

If `<PeopleUserContactSelection>` specifies `emailmatchpattern <REMatchPattern>`, only email addresses within the contact that match `<REMatchPattern>`
are updated.

## Display User Contacts
### User Contact Group information
In the following commands, specifying `allfields` or including `memberships` in `fields <PeopleFieldNameList>`
yields contact group information but only gives the contact group ID. Use the `showgroups` option to have GAM
make additional API calls to get the contact group name associated with the ID.

### Display as an indented list of keys and values.
```
gam <UserTypeEntity> info contacts
        <PeopleResourceNameEntity>
        [allfields|(fields <PeopleFieldNameList>)] [showgroups] [showmetadata]
        [formatjson]
```
By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> show contacts
        <PeoplePrintShowUserContactSelection>
        [orderby firstname|lastname|(lastmodified ascending)|(lastnodified descending)
        [countsonly|allfields|(fields <PeopleFieldNameList>)] [showgroups] [showmetadata]
        [formatjson]
```
By default, Gam displays all of a user's people contacts.
* `query <String>` - Display contacts based on the data in their fields
A maximum of 10 contacts will be returned. `orderBy` is not used with `query`.

By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam <UserTypeEntity> print contacts [todrive <ToDriveAttribute>*]
        <PeoplePrintShowUserContactSelection>
        [orderby firstname|lastname|(lastmodified ascending)|(lastnodified descending)
        [countsonly|allfields|(fields <PeopleFieldNameList>)] [showgroups] [showmetadata]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays all of a user's people contacts.
* `query <String>` - Display contacts based on the data in their fields
A maximum of 10 contacts will be returned. `orderBy` is not used with `query`.

By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage User Contact Photos
```
gam <UserTypeEntity> update contactphotos
        <PeopleResourceNameEntity>|<PeopleUserContactSelection>
        [drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]
gam <UserTypeEntity> get contactphotos
        <PeopleResourceNameEntity>|<PeopleUserContactSelection>
        [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
gam <UserTypeEntity> delete contactphotos
        <PeopleResourceNameEntity>|<PeopleUserContactSelection>

```
The default directory is the current working directory, `drivedir` specifies the value of drive_dir from gam.cfg and
`sourcefolder/targetfolder <FilePath>` specifies a user-chosen path.
`<FileNamePattern>` can contain the strings `#email#` and `#contactid#` which will be replaced by the the contact's primary emailaddress or the contact ID.
If not specified, `<FileNamePattern>` defaults to `#contactid#.jpg`.

## Copy User Other Contacts to My Contacts
Copy Other Contacts to My Contacts; now you have the same contact in two places.
```
gam <UserTypeEntity> copy othercontacts
        <OtherContactsResourceNameEntity>|<OtherContactsSelection>
```

## Move User Other Contacts to My Contacts
Move Other Contacts to My Contacts; there is no duplication.
```
gam <UserTypeEntity> move othercontacts
        <OtherContactsResourceNameEntity>|<OtherContactsSelection>
```

### Examples
Move a single Other Contact to My Contacts.
```
gam user user@domain.com move othercontacts otherContacts/c5977555358312178721
User: user@domain.com, Move maximum of 1 Other Contact
  User: user@domain.com, Other Contact: otherContacts/c5977555358312178721, Moved to: My Contacts
```
Move a selection of Other Contacts to My Contacts.
```
gam user user@domain.com move othercontacts emailmatchpattern "test.*"
Getting all Other Contacts for user@domain.com
Got 15 Other Contacts...
User: user@domain.com, Move maximum of 15 Other Contacts
  User: user@domain.com, Other Contact: otherContacts/c2813750813749807666, Moved to: My Contacts
  User: user@domain.com, Other Contact: otherContacts/c7887232007947329156, Moved to: My Contacts
  User: user@domain.com, Other Contact: otherContacts/c523029179688316095, Moved to: My Contacts
  User: user@domain.com, Other Contact: otherContacts/c4889739431064427541, Moved to: My Contacts
  User: user@domain.com, Other Contact: otherContacts/c6318452176100245073, Moved to: My Contacts
```

## Update User Other Contacts
Other contacts are updated and moved to My Contacts and other contact groups if specified.
```
gam <UserTypeEntity> update othercontacts
        <OtherContactsResourceNameEntity>|<OtherContactsSelection>
        [<PeopleContactAttribute>+]
        (contactgroup <ContactGroupItem>)*
```

### Examples
Update a single Other Contact and move to My Contacts and contact group "Test".
```
gam user user@domain.com update othercontacts otherContacts/c5977555358312178721 contactgroup Test
User: user@domain.com, Copy maximum of 1 Other Contact
  User: user@domain.com, Other Contact: otherContacts/c5977555358312178721, Updated/Moved to: My Contacts,Test
```
Update a selection of Other Contacts and move to My Contacts and contact group "Test".
```
gam user user@domain.com update othercontacts emailmatchpattern "test.*" contactgroup Test
Getting all Other Contacts for user@domain.com
Got 15 Other Contacts...
User: user@domain.com, Copy maximum of 15 Other Contacts
  User: user@domain.com, Other Contact: otherContacts/c2813750813749807666, Updated/Moved to: My Contacts,Test
  User: user@domain.com, Other Contact: otherContacts/c7887232007947329156, Updated/Moved to: My Contacts,Test
  User: user@domain.com, Other Contact: otherContacts/c523029179688316095, Updated/Moved to: My Contacts,Test
  User: user@domain.com, Other Contact: otherContacts/c4889739431064427541, Updated/Moved to: My Contacts,Test
  User: user@domain.com, Other Contact: otherContacts/c6318452176100245073, Updated/Moved to: My Contacts,Test
```

## Delete User Other Contacts
Other contacts are deleted by moving them to My Contacts and deleting them from there.
```
gam <UserTypeEntity> delete othercontacts
        <OtherContactsResourceNameEntity>|<OtherContactsSelection>
```

### Examples
Delete a single Other Contact.
```
gam user user@domain.com delete othercontacts otherContacts/c5977555358312178721
User: user@domain.com, Delete maximum of 1 Other Contact
  User: user@domain.com, Other Contact: otherContacts/c5977555358312178721, Deleted
```
Delete a selection of Other Contacts.
```
gam user user@domain.com delete othercontacts emailmatchpattern "test.*"
Getting all Other Contacts for user@domain.com
Got 15 Other Contacts...
User: user@domain.com, Delete maximum of 15 Other Contacts
  User: user@domain.com, Other Contact: otherContacts/c2813750813749807666, Deleted
  User: user@domain.com, Other Contact: otherContacts/c7887232007947329156, Deleted
  User: user@domain.com, Other Contact: otherContacts/c523029179688316095, Deleted
  User: user@domain.com, Other Contact: otherContacts/c4889739431064427541, Deleted
  User: user@domain.com, Other Contact: otherContacts/c6318452176100245073, Deleted
```

## Display User Other Contacts
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> show othercontacts
        [<OtherContactsSelection>]
        [countsonly|allfields|(fields <OtherContactsFieldNameList>)] [showmetadata]
        [formatjson]
```
By default, Gam displays all of a user's Other Contacts; use
`<OtherContactsSelection>` to display a selection of Other Contacts.

By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam <UserTypeEntity> print othercontacts [todrive <ToDriveAttribute>*]
        [<OtherContactsSelection>]
        [countsonly|allfields|(fields <OtherContactsFieldNameList>)] [showmetadata]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays all of a user's Other Contacts; use
`<OtherContactsSelection>` to display a selection of Other Contacts.

By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage User Contact Groups
```
gam <UserTypeEntity> create contactgroup <PeopleContactGroupAttribute>+
        [(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
```
By default, the user name and contactgroup ID are displayed on stdout.
* `csv [todrive <ToDriveAttribute>*]` - Write user name and contactgroup ID values to a CSV file.
  * `addcsvdata <FieldName> <String>` - Add additional columns of data from the command line to the output
* `returnidonly` - Display just the contactgroup ID on stdout

To retrieve the contactgroup ID with `returnidonly`:
```
Linux/MacOS
contactGroupId=$(gam user user@domain.com create contactgroup ... returnidonly)
Windows PowerShell
$contactGroupId = & gam user user@domain.com create contactgroup ... returnidonly
```
```
gam <UserTypeEntity> update contactgroup <PeopleContactGroupItem> <PeopleContactGroupAttribute>+
gam <UserTypeEntity> delete contactgroups <PeopleContactGroupEntity>
```

## Display User Contact Groups
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> info contactgroups <PeopleContactGroupEntity>
        [allfields|(fields <PeopleContactGroupFieldList>)] [showmetadata]
        [formatjson]
gam <UserTypeEntity> show contactgroups
        [allfields|(fields <PeopleContactGroupFieldNameList>)] [showmetadata]
        [formatjson]
```
By default, Gam displays the fields `name,metadata,grouptype,membercount`.
* `allfields|(fields <PeopleContactGroupFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam <UserTypeEntity> print contactgroups [todrive <ToDriveAttribute>*]
        [allfields|(fields <PeopleContactGroupFieldNameList>)] [showmetadata]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the fields `name,metadata,grouptype,membercount`.
* `allfields|(fields <PeopleContactGroupFieldNameList>)` - Select fields to display

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display User People Profile
### Display as an indented list of keys and values.
```
gam <UserTypeEntity> show peopleprofile
        [allfields|(fields <PeopleFieldNameList>]) [showmetadata]
        [formatjson]
```
By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam <UserTypeEntity> print peopleprofile [todrive <ToDriveAttribute>*]
        [allfields|(fields <PeopleFieldNameList>)] [showmetadata]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the fields `names,emailaddresses,phonenumbers`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Copy User Contacts to another User

To copy one user's contacts to another user perform the following steps.
```
# Copy contact groups
gam redirect csv ./ContactGroups.csv user sourceuser@domain.com print contactgroups formatjson
gam redirect stdout ./CopyContactGroups.txt multiprocess redirect stderr stdout csv ContactGroups.csv gam user targetuser@domain.com create contactgroup json "~JSON"

# Copy contacts
gam redirect csv ./Contacts.csv user sourceuser@domain.com print contacts selectmaincontacts allfields showgroups formatjson
gam redirect stdout ./CopyContacts.txt multiprocess redirect stderr stdout csv Contacts.csv gam user targetuser@domain.com create contact json "~JSON"
```
