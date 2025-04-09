# Domain People - Contacts & Profiles
- [API documentation](#api-documentation)
- [Collections of Users](Collections-of-Users)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Domain Contacts](#display-domain-contacts)
- [Display Domain Profiles](#display-domain-profiles)

## API documentation
* [Contacts API Migration](https://developers.google.com/people/contacts-api-migration)
* [People API Migration](https://developers.google.com/people)
* [People API](https://developers.google.com/people/api/rest)
* [People API - List Directory People](https://developers.google.com/people/api/rest/v1/people/listDirectoryPeople)
* [People API - Search Directory People](https://developers.google.com/people/api/rest/v1/people/searchDirectoryPeople)

## Notes
To use these features you must add the `People API` to your project and authorize the appropriate scopes:
* `Client Access` - `People Directory API - read only`
* `Service Account Access`
  * `People Directory API - read only`: https://www.googleapis.com/auth/directory.readonly
  * `OAuth2 API`: https://www.googleapis.com/auth/userinfo.profile
```
gam update project
gam oauth create
gam user user@domain.com update serviceaccount
```

## Definitions
```
<PeopleResourceName> ::= people/<String>
<PeopleResourceNameList> ::= "<PeopleResourceName>(,<PeopleResourceName>)*"
<PeopleResourceNameEntity> ::=
        <PeopleResourceNameNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<PeopleSourceName> ::=
        contact|contacts|
        profile|profiles

<PeopleMergeSourceName> ::=
        contact|contacts

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
        userdefined
<PeopleFieldNameList> ::= "<PeopleFieldName>(,<PeopleFieldName>)*"
```

## Display Domain Contacts
### Display as an indented list of keys and values.
```
gam info domaincontacts <PeopleResourceNameEntity>
        [allfields|(fields <PeopleFieldNameList>)]
        [formatjson]
```
By default, Gam displays the fields `names,emailaddresses`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam show domaincontacts
        [query <String>]
        [mergesources <PeopleMergeSourceName>]
        [allfields|(fields <PeopleFieldNameList>)]
        [formatjson]
```
By default, Gam displays all domain contacts.
* `query <String>` - Display contacts based on the data in their fields.

Google's explanation of `mergesources`: Additional data to merge into the directory sources
if they are connected through verified join keys such as email addresses or phone numbers.

By default, Gam displays the fields `names,emailaddresses`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam print domaincontacts [todrive <ToDriveAttribute>*]
        [query <String>]
        [mergesources <PeopleMergeSourceName>]
        [allfields|(fields <PeopleFieldNameList>)]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays all domain contacts.
* `query <String>` - Display contacts based on the data in their fields.

Google's explanation of `mergesources`: Additional data to merge into the directory sources
if they are connected through verified join keys such as email addresses or phone numbers.

By default, Gam displays the fields `names,emailaddresses`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Domain Profiles
### Display as an indented list of keys and values.
```
gam info domainprofiles|people|peopleprofiles <PeopleResourceNameEntity>
        [allfields|(fields <PeopleFieldNameList>)]
        [formatjson]
```
By default, Gam displays the fields `names,emailaddresses`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam show domainprofiles|people|peopleprofiles
        [query <String>]
        [mergesources <PeopleMergeSourceName>]
        [allfields|(fields <PeopleFieldNameList>)]
        [formatjson]
```
By default, Gam displays all domain profiles.
* `query <String>` - Display profiles based on the data in their fields.

Google's explanation of `mergesources`: Additional data to merge into the directory sources
if they are connected through verified join keys such as email addresses or phone numbers.

By default, Gam displays the fields `names,emailaddresses`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

### Display as a CSV file.
```
gam print domainprofiles|people|peopleprofiles [todrive <ToDriveAttribute>*]
        [query <String>]
        [mergesources <PeopleMergeSourceName>]
        [allfields|(fields <PeopleFieldNameList>)]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays all domain profiles.
* `query <String>` - Display profiles based on the data in their fields.

Google's explanation of `mergesources`: Additional data to merge into the directory sources
if they are connected through verified join keys such as email addresses or phone numbers.

By default, Gam displays the fields `names,emailaddresses`.
* `allfields|(fields <PeopleFieldNameList>)` - Select fields to display

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
