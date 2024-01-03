# Tag Replace
- [Python Regular Expressions](Python-Regular-Expressions) Sub function
- [Definitions](#definitions)
- [Introduction](#introduction)
- [Simple `replace <Tag> <String>` processing](#simple-replace-tag-string-processing)
- [User attribute `replace <Tag> <UserReplacement>` processing](#user-attribute-replace-tag-userreplacement-processing)
- [Example](#example)

## Definitions
```
<AddressSubfieldName> ::=
        country|
        countrycode|
        customtype|
        extendedaddress|
        formatted|
        locality|
        pobox|
        postalcode|
        primary|
        region|
        streetaddress|
        type
<EmailSubfieldName> ::=
        domain|
        primaryemail|
        username
<ExternalIdSubfieldName> ::=
        customtype|
        type|
        value
<GenderSubfieldName> ::=
        addressmeas|
        customgender|
        type
<IMSubfieldName> ::=
        customtype|
        type|
        value
<KeywordSubfieldName> ::=
        customtype|
        type|
        value
<LocationSubfieldName> ::=
        area|
        buildingid|
        buildingname|
        customtype|
        deskcode|
        floorname|
        floorsection|
        type
<NameSubfieldName> ::=
        familyname|
        fullname|
        givenname
<OrganizationSubfieldName> ::=
        costcenter|
        customtype|
        department|
        description|
        domain|
        fulltimeequivalent|
        location|
        name|
        primary|
        symbol|
        title|
        type
<OtherEmailSubfieldName> ::=
        address|
        customtype|
        primary|
        type
<PhoneSubfieldName> ::=
        customtype|
        primary|
        type|
        value
<PosixSubfieldName> ::=
        accountid|
        gecos|
        gid|
        homedirectory|
        operatingsystemtype|
        primary|
        shell|
        systemid|
        uid|
        username
<RelationSubfieldName> ::=
        customtype|
        type|
        value
<SSHkeysSubfieldName> ::=
        expirationtimeusec|
        fingerprint|
        key
<WebsiteSubfieldName> ::=
        customtype|
        primary|
        type|
        value
<UserReplacementFieldSubfield> ::=
        address.<AddressSubfieldName>|
        email.<EmailSubfieldName>|
        externalid.<ExternalIdSubfieldName>|
        gender.<GenderSubfieldName>|
        im.<IMSubfieldName>|
        keyword.<KeywordSubfieldName>|
        location.<LocationSubfieldName>|
        name.<NameSubfieldName>|
        organization.<OrganizationSubfieldName>|
        otheremail.<OtherEmailSubfieldName>|
        phone.<PhoneSubfieldName>|
        posix.<PosixSubfieldName>|
        relation.<RelationSubfieldName>|
        sshkeys.<SSHkeysSubfieldName>|
        website.<WebsiteSubfieldName>|
<UserReplacementFieldSubfieldMatchSubfield> ::=
        address.<AddressSubfieldName>.<AddressSubfieldName>.<String>|
        externalid.<ExternalIdSubfieldName>.<ExternalIdSubfieldName>.<String>|
        im.<IMSubfieldName>.<IMSubfieldName>.<String>|
        keyword.<KeywordSubfieldName>.<KeywordSubfieldName>.<String>|
        location.<LocationSubfieldName>.<LocationSubfieldName>.<String>|
        organization.<OrganizationSubfieldName>.<OrganizationSubfieldName>.<String>|
        otheremail.<OtherEmailSubfieldName>.<OtherEmailSubfieldName>.<String>|
        phone.<PhoneSubfieldName>.<PhoneSubfieldName>.<String>|
        posix.<PosixSubfieldName>.<PosixSubfieldName>.<String>|
        relation.<RelationSubfieldName>.<RelationSubfieldName>.<String>|
        sshkeys.<SSHkeysSubfieldName>.<SSHkeysSubfieldName>.<String>|
        website.<WebsiteSubfieldName>.<WebsiteSubfieldName>.<String>
<UserReplacementField> ::=
        photourl
<Tag> ::= <String>
<UserReplacement> ::=
        (field:<UserReplacementField>)|
        (field:<UserReplacementFieldSubfield>)|
        (field:<UserReplacementFieldSubfieldMatchSubfield>)|
        (schema:<SchemaName>.<FieldName>)|
        <String>
```
## Introduction
Several commands use template files for messages and signatures; Gam has the ability to replace tags in the template with data from the command line or from user attributes.

## Simple `replace <Tag> <String>` processing
This command allows simple text replacement in the message.
```
gam sendemail <EmailAddressEntity> [from <UserItem>] [replyto <EmailAddress>]
        [cc <EmailAddressEntity>] [bcc <EmailAddressEntity>] [singlemessage [<Boolean>]]
        [subject <String>] [message <String>|(file <FileName> [charset <Charset>])]
        (replace <Tag> <String>)* [html [<Boolean>]] (attach <FileName>)*
```
* Every instance of `{Tag}` in the message will be replaced by `<String>`.
* Instances of the form `{RT}...{Tag1}...{Tag2}...{/RT}` will be eliminated if there are no `<String>` values for all `TagN` or if the `<String>` values are all empty strings.
* Instances of the form `{RTL}...{RT}...{Tag1}...{/RT}{RT}...{Tag2}...{/RT}{/RTL}` will be eliminated if none of the embedded `{RT}...{Tag}...{/RT}` have values.

You can control the case of the letters in `replace <Tag> <String>`:
  * `{PC}...{Tag1}...{Tag2}...{/PC}` - For all sequences of letters between `{PC}` and `{/PC}`, the first letter is converted to uppercase, subsequent letters to lowercase.
  * `{UC}...{Tag1}...{Tag2}...{/UC}` - All letters between `{UC}` and `{/UC}` will be converted to uppercase
  * `{LC}...{Tag1}...{Tag2}...{/LC}` - All letters between `{LC}` and `{/LC}` will be converted to lowercase

## User attribute `replace <Tag> <UserReplacement>` processing
These commands allow simple text replacement in the message/signature as well as substitution of select user attributes.
```
gam create user <EmailAddress> <UserAttribute>*
        [notify <EmailAddress>] [subject <String>]
            [message <String>|(file <FileName> [charset <Charset>])] [html [<Boolean>]]
            (replace <Tag> <UserReplacement>)*
gam update user <UserItem> <UserAttribute>
        [updateprimaryemail <RegularExpression> <EmailReplacement>]
        [updateoufromgroup <FileName> [charset <Charset>]
            [columndelimiter <Character>] [noescapechar <Boolean>] [quotechar <Character>]
            [fields <FieldNameList>] [keyfield <FieldName>] [datafield <FieldName>]]
        [clearschema <SchemaName>] [clearschema <SchemaName>.<FieldName>]
        [createifnotfound] [notify <EmailAddress>] [subject <String>]
            [message <String>|(file <FileName> [charset <Charset>])] [html [<Boolean>]]
            (replace <Tag> <UserReplacement>)*

gam <UserTypeEntity> draft message (<SMTPDateHeader> <Time>)*
        (<SMTPHeader> <String>)* (header <String> <String>)*
        (addlabel <LabelName>)* [labels <LabelNameList>]
        (textmessage|message <String>)|(textfile|file <FileName> [charset <Charset>])
        (htmlmessage <String>)|(htmlfile <FileName> [charset <Charset>])
        (replace <Tag> <UserReplacement>)* (attach <FileName> [charset <Charset>])*
gam <UserTypeEntity> import message (<SMTPDateHeader> <Time>)*
        (<SMTPHeader> <String>)*
        (header <String> <String>)*
        (addlabel <LabelName>)*
        (textmessage <String>)|(textfile <FileName> [charset <Charset>])
        (htmlmessage <String>)|(htmlfile <FileName> [charset <Charset>])
        (replace <Tag> <UserReplacement>)* (attach <FileName>)*
        [deleted [<Boolean>]] [nevermarkspam [<Boolean>]]
        [processforcalendar [<Boolean>]]
gam <UserTypeEntity> insert message
        (<SMTPDateHeader> <Time>)*
        (<SMTPHeader> <String>)*
        (header <String> <String>)*
        (addlabel <LabelName>)*
        (textmessage <String>)|(textfile <FileName> [charset <Charset>])
        (htmlmessage <String>)|(htmlfile <FileName> [charset <Charset>])
        (replace <Tag> <UserReplacement>)* (attach <FileName>)*
        [deleted [<Boolean>]]

gam <UserTypeEntity> [create|add] sendas <EmailAddress> <String>
        [signature|sig <String>|(file <FileName> [charset <Charset>])
        (replace <Tag> <UserReplacement>)*]
        [html [<Boolean>]] [replyto <EmailAddress>]
        [default] [treatasalias <Boolean>]

gam <UserTypeEntity> update sendas <EmailAddress>
        [name <String>] [signature|sig <String>|(file <FileName> [charset <Charset>])
        (replace <Tag> <UserReplacement>)*]
        [html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]

gam <UserTypeEntity> signature|sig <String>|(file <FileName> [charset <Charset>])
        (replace <Tag> <UserReplacement>)*
        [html [<Boolean>]] [name <String>] [replyto <EmailAddress>]
        [default] [primary] [treatasalias <Boolean>]

gam <UserTypeEntity> vacation <TrueValues> subject <String>
        [message <String>|(file <FileName> [charset <Charset>])]
        (replace <Tag> <UserReplacement>)*
        [html [<Boolean>]] [contactsonly [<Boolean>]] [domainonly [<Boolean>]]
        [startdate <Date>|Started] [enddate <Date>|NotSpecified]
```
* Every instance of `{Tag}` in the message/signature will be replaced by `<UserReplacement>`.
* Instances of the form `{RT}...{Tag1}...{Tag2}...{/RT}` will be eliminated if there are no `<UserReplacement>` values for all `TagN` or if the `<UserReplacement>` values are all empty strings.
* Instances of the form `{RTL}...{RT}...{Tag1}...{/RT}{RT}...{Tag2}...{/RT}{/RTL}` will be eliminated if none of the embedded `{RT}...{Tag}...{/RT}` have values.

You can control the case of the letters in `replace <Tag> <UserReplacement>`:
  * `{PC}...{Tag1}...{Tag2}...{/PC}` - For all sequences of letters between `{PC}` and `{/PC}`, the first letter is converted to uppercase, subsequent letters to lowercase.
  * `{UC}...{Tag1}...{Tag2}...{/UC}` - All letters between `{UC}` and `{/UC}` will be converted to uppercase
  * `{LC}...{Tag1}...{Tag2}...{/LC}` - All letters between `{LC}` and `{/LC}` will be converted to lowercase

`<UserReplacement>` specifies the data that replaces `{Tag}` in the message/signature.
* `field:<UserReplacementFieldSubfield>` - A subfield value from a user attribute
    * For attributes `address`, `organization`, `otheremails` and `phone`, the attribute instance marked `primary` will be used. If there is no attribute instance marked `primary`, the first attribute instance will be used.
    * For attribute `location`, the first attribute instance will be used.
    * If `<UserReplacementFieldSubfield>` is empty or does not exist, an empty string will be used
* `field:<UserReplacementFieldSubfieldMatchSubfield>` - A subfield value from a user attribute where a second subfield value is used to select the attribute
    * Select based on type: `phone.value.type.work`
    * Select primary instance: `otheremails.address.primary.true`
* `schema:<SchemaName>.<FieldName>` - A custom schema value from the user's profile.
* `<String>` - A literal string in which the following substitutions will be made:
    * `#email#` and `#user#` will be replaced by the user's primary email address
    * `#username#` will be replaced by the local part of the user's primary email address

## Example
The file SigTemplate.txt contains:
```
<div dir='ltr' style='color:rgb(0,0,0);font-family:Helvetica;font-size:12px'>
<p>Name: {first} {last}<br />
{RT}Address: {address}<br />{/RT}
{RT}Department: {department}, Title: {title}<br />{/RT}
{RT}Location: Building: {building}, Floor: {floor}, Section: {section}, Desk: {desk}<br />{/RT}
{RTL}{RT}Office: {officephone} {/RT}{RT}Mobile: {mobilephone}{/RT}<br />{/RTL}
Email: {email}</p>
</div>
```
This command will update the signatures of the specified users.
* The `replace` arguments can appear in any order.
```
gam <UserTypeEntity> signature file SigTemplate.txt html
        replace first field:name.givenname replace last field:name.familyname
        replace officephone field:phone.value.type.work replace mobilephone field:phone.value.type.mobile
        replace email field:email.primaryemail
        replace address field:address.formatted
        replace department field:organization.department replace title field:organization.title
        replace building field:location.buildingname replace floor field:location.floorname
        replace section field:location.floorsection replace desk field:location.deskcode
```
