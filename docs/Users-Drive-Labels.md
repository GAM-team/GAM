# Users - Drive - Labels
- [API documentation](#api-documentation)
- [Query documentation](Users-Drive-Query)
- [Notes](#notes)
- [Definitions](#definitions)
- [Introduction](#introduction)
- [Display Drive Labels](#display-drive-labels)
- [Process File Drive Labels](#process-file-drive-labels)

## API documentation
* https://support.google.com/a/answer/9292382
* https://developers.google.com/drive/labels/guides/overview
* https://developers.google.com/drive/labels/guides/authorize
* https://developers.google.com/drive/labels/reference/rest/v2beta/labels
* https://developers.google.com/drive/api/guides/about-labels
* https://developers.google.com/drive/api/v3/reference/files

## Notes
To use these commands you must add the 'Drive Labels API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com check serviceaccount
```
Supported editions for this feature: Business Standard and Business Plus; Enterprise; Education Standard and Education Plus; G Suite Business; Essentials.

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DriveLabelID> ::= <String>
<DriveLabelIDList> ::= "<DriveLabelID>(,<DriveLabelID)*"

<DriveLabelName> ::= labels/<DriveLabelID>[@latest|@published|@<Number>]
<DriveLabelNameList> ::= "<DriveLabelName>(,<DriveLabelName)*"
<DriveLabelNameEntity> ::=
        <DriveLabelNameList> | <FileSelector> | <CSVFileSelector> | <CSVDataSelector>

<DriveLabelFieldID> ::= <String>
<DriveLabelSelectionID> ::= <String>
<DriveLabelSelectionIDList> ::= "<DriveLabelSelectionID>(,<DriveLabelSelectionID)*"

<DriveLabelLanguageCode> ::=
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

## Introduction
A domain administrator with the Drive and Docs administrator privilege can search for Shared Drives or update permissions for Shared Drives
owned by their organization, regardless of the admin's membership in any given Shared Drive.

Three forms of the commands are available:
* `gam action ...` - The administrator named in oauth2.txt is used, domain administrator access implied and labels of type `SHARED` and `ADMIN`can be written
* `gam <UserTypeEntity> action ... adminaccess` - The user named in `<UserTypeEntty>` is used, adminaccess indicates that labels of type `SHARED` and `ADMIN`can be written
* `gam <UserTypeEntity> action ...` - The user named in `<UserTypeEntty>` is used, access is limited, onlylabels of type `SHARED` can be written

## Display Drive Labels

```
gam [<UserTypeEntity>] info drivelabels <DriveLabelNameEntity>
        [[basic|full] [languagecode <DriveLabelLanguageCode>]
        [formatjson] [adminaccess|asadmin]
```
* `basic` - Display fields: name,id,revisionId,labelType,properties.*; this is the default
* `full` - Display all possible fields
* `languagecode <DriveLabelLanguageCode>` - The BCP-47 language code to use for evaluating localized Field labels. When not specified, values in the default configured language will be used.
* `adminaccess|asadmin` - Use the user's admin credentials. This will return all Labels within the customer.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam [<UserTypeEntity>] show drivelabels
        [basic|full] [languagecode <DriveLabelLanguageCode>]
        [publishedonly [<Boolean>]] [minimumrole applier|editor|organizer|reader]
        [formatjson] [adminaccess|asadmin]
```
* `basic` - Display fields: name,id,revisionId,labelType,properties.*; this is the default
* `full` - Display all possible fields
* `languagecode <DriveLabelLanguageCode>` - The BCP-47 language code to use for evaluating localized Field labels. When not specified, values in the default configured language will be used.
* `minimumrole applier|editor|organizer|reader` - Specifies the level of access the user must have on the returned Labels. Defaults to READER.
* `adminaccess|asadmin` - Use the user's admin credentials. This will return all Labels within the customer.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam [<UserTypeEntity>] print drivelabels [todrive <ToDriveAttribute>*]
        [basic|full] [languagecode <DriveLabelLanguageCode>]
        [publishedonly [<Boolean>]] [minimumrole applier|editor|organizer|reader]
        [formatjson [quotechar <Character>]] [adminaccess|asadmin]
```
* `basic` - Display fields: name,id,revisionId,labelType,properties.*; this is the default
* `full` - Display all possible fields
* `languagecode <DriveLabelLanguageCode>` - The BCP-47 language code to use for evaluating localized Field labels. When not specified, values in the default configured language will be used.
* `minimumrole applier|editor|organizer|reader` - Specifies the level of access the user must have on the returned Labels. Defaults to READER.
* `adminaccess|asadmin` - Use the user's admin credentials. This will return all Labels within the customer.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Process File Drive Labels
`<DriveLabelID>`, `<DriveLabelFieldID>` and `<DriveLabelSelectionID>` values are obtained from the commands above.
```
gam <UserTypeEntity> process filedrivelabels <DriveFileEntity>
        (addlabel <DriveLabelIDList>)*
        (deletelabel <DriveLabelIDList>)*
        (addlabelfield <DriveLabelID> <DriveLabelFieldID>
            (text <String>)|selection <DriveLabelSelectionIDList>)|
            (integer <Number>)|(date <Date>)|(user <EmailAddressList>))*
        (deletelabelfield <DriveLabelID> <DriveLabelFieldID>)*
        [nodetails]
```

By default, details of the process labels are displayed, use `nodetails` to suppress this display.

