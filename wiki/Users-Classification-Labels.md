# Users - Classification Labels
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Definitions](#definitions)
- [Admin Access](#admin-access)
- [Display Classification Labels](#display-classification-labels)
- [Manage Classification Label Permissions](#manage-classification-label-permissions)
- [Display Classification Label Permissions](#display-classification-label-permissions)
- [Process Drive File Classification Labels](#process-drive-file-classification-labels)

## Notes
To use these commands you must add the 'Drive Labels API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
```
Supported editions for this feature:
```
Frontline Starter and Frontline Standard
Business Standard and Business Plus
Enterprise Standard and Enterprise Plus
Education Standard and Education Plus
Essentials, Enterprise Essentials, and Enterprise Essentials Plus
G Suite Business
```

## API documentation
* [Classification labels admin](https://support.google.com/a/answer/9292382)
* [Labels Overview](https://developers.google.com/drive/api/guides/about-labels)
* [Drive Labels API - Overview](https://developers.google.com/drive/labels/guides/overview)
* [Drive Labels API - Labels](https://developers.google.com/drive/labels/reference/rest/v2/labels)
* [Drive Labels API - Permissions](https://developers.google.com/drive/labels/reference/rest/v2/labels.permissions)
* [Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)
* [`<ClassificationLabelNameEntity>`, `<ClassificationLabelPermissionNameEntity`](Collections-of-Items)
* [`<UserTypeEntity>`](Collections-of-Items)

```
<ClassificationLabelID> ::= <String>
<ClassificationLabelIDList> ::= "<ClassificationLabelID>(,<ClassificationLabelID)*"

<ClassificationLabelName> ::= labels/<ClassificationLabelID>[@latest|@published|@<Number>]
<ClassificationLabelNameList> ::= "<ClassificationLabelName>(,<ClassificationLabelName)*"
<ClassificationLabelNameEntity> ::=
        <ClassificationLabelNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>

<ClassificationLabelPermissionName> ::= labels/<ClassificationLabelID>[@latest|@published|@<Number>]/permissions/(audiences|groups|people)/<String>
<ClassificationLabelPermissionNameList> ::= "<ClassificationLabelPermissionName>(,<ClassificationLabelPermissionName>)*"
<ClassificationLabelPermissionNameEntity> ::=
        <ClassificationLabelPermissionNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>

<ClassificationLabelFieldID> ::= <String>
<ClassificationLabelSelectionID> ::= <String>
<ClassificationLabelSelectionIDList> ::= "<ClassificationLabelSelectionID>(,<ClassificationLabelSelectionID)*"

<BCP47LanguageCode> ::=
        ar-sa| # Arabic Saudi Arabia
        cs-cz| # Czech Czech Republic
        da-dk| # Danish Denmark
        de-de| # German Germany
        el-gr| # Modern Greek Greece
        en-au| # English Australia
        en-gb| # English United Kingdom
        en-ie| # English Ireland
        en-us| # English United States
        en-za| # English South Africa
        es-es| # Spanish Spain
        es-mx| # Spanish Mexico
        fi-fi| # Finnish Finland
        fr-ca| # French Canada
        fr-fr| # French France
        he-il| # Hebrew Israel
        hi-in| # Hindi India
        hu-hu| # Hungarian Hungary
        id-id| # Indonesian Indonesia
        it-it| # Italian Italy
        ja-jp| # Japanese Japan
        ko-kr| # Korean Republic of Korea
        nl-be| # Dutch Belgium
        nl-nl| # Dutch Netherlands
        no-no| # Norwegian Norway
        pl-pl| # Polish Poland
        pt-br| # Portuguese Brazil
        pt-pt| # Portuguese Portugal
        ro-ro| # Romanian Romania
        ru-ru| # Russian Russian Federation
        sk-sk| # Slovak Slovakia
        sv-se| # Swedish Sweden
        th-th| # Thai Thailand
        tr-tr| # Turkish Turkey
        zh-cn| # Chinese China
        zh-hk| # Chinese Hong Kong
        zh-tw  # Chinese Taiwan
```

## Admin Access
A domain administrator with the Drive and Docs administrator privilege can search for Shared Drives or update permissions for Shared Drives
owned by their organization, regardless of the admin's membership in any given Shared Drive.

Three forms of the commands are available:
* `gam action ...` - The administrator named in oauth2.txt is used, domain administrator access implied and labels of type `SHARED` and `ADMIN`can be processed
* `gam <UserTypeEntity> action ... adminaccess` - The user named in `<UserTypeEntty>` is used, adminaccess indicates that labels of type `SHARED` and `ADMIN`can be processed
* `gam <UserTypeEntity> action ...` - The user named in `<UserTypeEntty>` is used, access is limited, onlylabels of type `SHARED` can be processed

## Display Classification Labels

```
gam [<UserTypeEntity>] info classificationlabels <ClassificationLabelNameEntity>
        [[basic|full] [languagecode <BCP47LanguageCode>]
        [formatjson] [adminaccess|asadmin]
```
* `basic` - Display fields: name,id,revisionId,labelType,properties.*; this is the default
* `full` - Display all possible fields
* `languagecode <BCP47LanguageCode>` - The BCP-47 language code to use for evaluating localized Field labels. When not specified, values in the default configured language will be used.
* `adminaccess|asadmin` - Use the user's admin credentials. This will return all Labels within the customer.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam [<UserTypeEntity>] show classificationlabels
        [basic|full] [languagecode <BCP47LanguageCode>]
        [publishedonly [<Boolean>]] [minimumrole applier|editor|organizer|reader]
        [formatjson] [adminaccess|asadmin]
```
* `basic` - Display fields: name,id,revisionId,labelType,properties.*; this is the default
* `full` - Display all possible fields
* `languagecode <BCP47LanguageCode>` - The BCP-47 language code to use for evaluating localized Field labels. When not specified, values in the default configured language will be used.
* `minimumrole applier|editor|organizer|reader` - Specifies the level of access the user must have on the returned Labels. Defaults to READER.
* `adminaccess|asadmin` - Use the user's admin credentials. This will return all Labels within the customer.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam [<UserTypeEntity>] print classificationlabels [todrive <ToDriveAttribute>*]
        [basic|full] [languagecode <BCP47LanguageCode>]
        [publishedonly [<Boolean>]] [minimumrole applier|editor|organizer|reader]
        [formatjson [quotechar <Character>]] [adminaccess|asadmin]
```
* `basic` - Display fields: name,id,revisionId,labelType,properties.*; this is the default
* `full` - Display all possible fields
* `languagecode <BCP47LanguageCode>` - The BCP-47 language code to use for evaluating localized Field labels. When not specified, values in the default configured language will be used.
* `minimumrole applier|editor|organizer|reader` - Specifies the level of access the user must have on the returned Labels. Defaults to READER.
* `adminaccess|asadmin` - Use the user's admin credentials. This will return all Labels within the customer.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage Classification Label Permissions
Create a permission for a Classification Label by specifying the label name and the principal.
```
gam [<UserTypeEntity>] create classificationlabelpermission <ClassificationLabelNameEntity>
        (user <UserItem>) | (group <GroupItem) | (audience <String>)
        role applier|editor|organizer|reader
        [nodetails|formatjson] [adminaccess|asadmin]
```

By default, when a permission is created, GAM outputs details of the permission as indented keywords and values.
* `nodetails` - Suppress the details output.
* `formatjson` - Output the details in JSON format.

Delete a Classification Label permission by specifying the label name and the principal.
```
gam [<UserTypeEntity>] delete classificationlabelpermission <ClassificationLabelNameEntity>
        (user <UserItem>) | (group <GroupItem) | (audience <String>)
        [adminaccess|asadmin]
```

Delete a Classification Label permission by specifying the label permission name.
```
gam [<UserTypeEntity>] remove classificationlabelpermission <ClassificationLabelPermissionNameEntity>
        [adminaccess|asadmin]
```
## Display Classification Label Permissions
Display permissions for a collection of Classification Label permission names.
```
gam [<UserTypeEntity>] show classificationlabelpermissions <ClassificationLabelNameEntity>
        [formatjson] [adminaccess|asadmin]
```

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam [<UserTypeEntity>] print classificationlabelpermissions <ClassificationLabelNameEntity> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]] [adminaccess|asadmin]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Process Drive File Classification Labels
`<ClassificationLabelID>`, `<ClassificationLabelFieldID>` and `<ClassificationLabelSelectionID>` values are obtained from the commands above.
```
gam <UserTypeEntity> process filedrivelabels <DriveFileEntity>
        (addlabel <ClassificationLabelIDList>)*
        (deletelabel <ClassificationLabelIDList>)*
        (addlabelfield <ClassificationLabelID> <ClassificationLabelFieldID>
            (text <String>)|selection <ClassificationLabelSelectionIDList>)|
            (integer <Number>)|(date <Date>)|(user <EmailAddressList>))*
        (deletelabelfield <ClassificationLabelID> <ClassificationLabelFieldID>)*
        [nodetails]
```

By default, details of the process labels are displayed, use `nodetails` to suppress this display.
