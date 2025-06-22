# Users - Gmail - Send As/Signature/Vacation
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage sendas](#manage-sendas)
- [Display sendas](#display-sendas)
- [Manage signature](#manage-signature)
- [Display signature](#display-signature)
  - [Display users without a primary email address signature](#display-users-without-a-primary-email-address-signature)
- [Manage vacation](#manage-vacation)
- [Display vacation](#display-vacation)
- [User attribute `replace <Tag> <UserReplacement>` processing](Tag-Replace)
- [Standardize user signatures](#standardize-user-signatures)

## API documentation
* [Gmail API - SendAs/Signature](https://developers.google.com/gmail/api/reference/rest/v1/users.settings.sendAs)
* [Gmail API - Vacation](https://developers.google.com/gmail/api/v1/reference/users.settings/updateVacation)
* [Treat as an Alias](https://support.google.com/a/answer/1710338)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
* [Command data from Google Docs/Sheets/Storage](Command-Data-From-Google-Docs-Sheets-Storage)
```
<FalseValues>= false|off|no|disabled|0
<TrueValues> ::= true|on|yes|enabled|1
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<EmailAddressList> ::= "<EmailAddress>(,<EmailAddress>)*"
<EmailAddressEntity> ::=
        <EmailAddressList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Users
<Charset> ::= ascii|mbcs|utf-8|utf-8-sig|utf-16|<String>
<Password> ::= <String>
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>
<SMTPHostName> ::= <String>
<Tag> ::= <String>
<UserName> ::= <String>
<UserReplacement> ::=
        (field:<UserReplacementFieldName>)|(schema:<SchemaName>.<FieldName>)|<String>

<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>

<UserGoogleDoc> ::=
        <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>|(<SharedDriveEntity> <SharedDriveFileNameEntity>)

<SendAsContent> ::=
        (sig|signature|htmlsig <String>)|
        (file|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)

<SignatureContent> ::=
        (<String>)|
        (file|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)

<VacationMessageContent> ::=
        (message|textmessage|htmlmessage <String>)|
        (file|textfile|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
```
## Manage sendas
```
gam <UserTypeEntity> [create|add] sendas <EmailAddress> [name] <String>
        [<SendAsContent>
            (replace <Tag> <UserReplacement>)*
            (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
        [html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
        [smtpmsa.host <SMTPHostName> smtpmsa.port 25|465|587
         smtpmsa.username <UserName> smtpmsa.password <Password>
         [smtpmsa.securitymode none|ssl|starttls]]
gam <UserTypeEntity> update sendas <EmailAddress> [name <String>]
        [<SendAsContent>
            (replace <Tag> <UserReplacement>)*
            (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
        [html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
gam <UserTypeEntity> delete sendas <EmailAddressEntity>
```
With `create|add`, the `<String>` following `<EmailAddress>` and optionally `name`, is the display name
of the sendas address.

`<SendAsContent>` is the signature, there are four ways to specify it:
* `sig|signature|htmlsig <String>` - Use `<String>` as the signature
* `file|htmlfile <FileName> [charset <Charset>]` - Read the signature from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the signature from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the signature from the Google Cloud Storage file `<StorageBucketObjectName>`

The `default` option sets `<EmailAddress>` as the default sendas address for the user.

For `treatasalias`, see: https://support.google.com/a/answer/1710338

You can allow users to send mail through an external SMTP server when configuring a sendas address hosted outside your email domains. You must enable
this capability in Admin Console/Apps/Google Workspace/Gmail/Advanced settings/End User Access/Allow per-user outbound gateways.

Example:
Paul shall send emails from the marketing email address with the name Paul from Example" and replies shall go back to them.  
``` gam user paul add sendas marketing@example.com "Paul from Example" replyto paul```

## Display sendas
### Display the sendas information as an indented list of keys and values.
```
gam <UserTypeEntity> info sendas <EmailAddressEntity> [compact|format|html]
gam <UserTypeEntity> show sendas [compact|format|html]
        [primary|default] [verifyonly]
```

These are the output formatting options:
* `compact` - Escape carriage returns as \r and newlines as \n in original HTML; this format produces output that can be used as input to GAM
* `format` - Strip HTML keywords leaving basic printable information
* `html` - Show original HTML; this is the default option; the output is human readable but cannot be used as input to GAM

By default, all sendas addresses are shown, use these options to limit the display:
* `primary` - Display the primary email address
* `default` - Display the default sendas address

Use the `verifyonly` option to display `True` or `False` in the signature field based on whether the signature is non-blank.

To capture a signature for use as input to GAM, do the following.
```
gam redirect stdout ./signature.html user user@domain.com show sendas compact
```
Edit signature.html and remove the following data leaving just the HTML.
```
SendAs Address: <user@domain.com>
  IsPrimary: True
  Default: True
  Signature:
```

### Display the sendas information in CSV form.
```
gam <UserTypeEntity> print sendas [compact]
        [primary|default] [verifyonly] [todrive <ToDriveAttribute>*]
```

These are the output formatting options:
* `compact` - Strip carriage returns and newlines in original HTML; this makes these values easier to process in the CSV file
and can be used as input to GAM.

By default, all sendas addresses are shown, use these options to limit the display:
* `primary` - Display the primary email address
* `default` - Display the default sendas address

Use the `verifyonly` option to display `True` or `False` in the signature field based on whether the signature is non-blank.

## Manage signature
```
gam <UserTypeEntity> signature|sig
        <SignatureContent>
        (replace <Tag> <UserReplacement>)*
        (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*
        [html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
        [name <String>]
        [primary]
```
`<SignatureContent>` is the signature, there are four ways to specify it:
* `<String>` - Use `<String>` as the signature
* `file|htmlfile <FileName> [charset <Charset>]` - Read the signature from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the signature from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the signature from the Google Cloud Storage file `<StorageBucketObjectName>`

The `default` option sets `<EmailAddress>` as the default sendas address for the user.

For `treatasalias`, see: https://support.google.com/a/answer/1710338

When `<UserTypeEntity>` specifies an alias, the `primary` option causes the primary
email address signature rather than the alias signature to be set.

`[name <String>]` sets the display name for non-primary sendas addresses, not the name of the signature, as that isn't possible via the API. 

If you have a current default signature, the API will update that, but if you delete it, it seems that the API will not over-write any of the other signatures, but instead add a new signature called `My signature`. If you rename that signature, the API will keep on updating that same signature, and not touch the other signatures.

## Display signature
### Display the signature as an indented list of keys and values.
```
gam <UserTypeEntity> show signature|sig [compact|format|html]
        [primary|default] [verifyonly]
```

These are the output formatting options:
* `compact` - Escape carriage returns as \r and newlines as \n in original HTML; this format produces output that can be used as input to GAM
* `format` - Strip HTML keywords leaving basic printable information
* `html` - Show original HTML; this is the default option; the output is human readable but cannot be used an input to GAM

By default, the signature for `<UserTypeEntity>` is displayed, use these options to alter the display:
* `primary` - Display the primary email address signature
* `default` - Display the default sendas address signature

Use the `verifyonly` option to display `True` or `False` in the signature field based on whether the signature is non-blank.

To capture a signature for use as input to GAM, do the following.
```
gam redirect stdout ./signature.html user user@domain.com show signature compact
```
Edit signature.html and remove the following data leaving just the HTML.
```
SendAs Address: <user@domain.com>
  IsPrimary: True
  Default: True
  Signature:
```

### Display the signature in CSV form.
```
gam <UserTypeEntity> print signature [compact]
            [primary|default] [verifyonly] [todrive <ToDriveAttribute>*]
```

These are the output formatting options:
* `compact` - Strip carriage returns and newlines in original HTML; this makes these values easier to process in the CSV file
and can be used as input to GAM.

By default, the signature for `<UserTypeEntity>` is displayed, use these options to alter the display:
* `primary` - Display the primary email address signature
* `default` - Display the default sendas address signature

Use the `verifyonly` option to display `True` or `False` in the signature field based on whether the signature is non-blank.

## Display users without a primary email address signature
The command line is wrapped for readability.
```
gam config csv_output_row_filter "signature:boolean:false"
    csv_output_header_filter "User,displayName,signature"
    auto_batch_min 1 num_threads 10
    redirect csv ./NoPrimarySignature.csv multiprocess
    all users print signature primary verifyonly
```
* `config csv_output_row_filter "signature:boolean:false"` - Output rows that indicate no signature
* `csv_output_header_filter "User,displayName,signature"` - Output basic headers
* `auto_batch_min 1 num_threads 10` - Turn on parallel processing
* `redirect csv ./NoPrimarySignature.csv multiprocess` - Intelligently combine output from all processes
* `all users` - Process all non-suspended users
* `print signature primary verifyonly` - Display state of primary email address signature

## Manage vacation
```
gam <UserTypeEntity> vacation [<Boolean>] [subject <String>]
        [<VacationMessageContent>
            (replace <Tag> <UserReplacement>)*
            (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
        [html [<Boolean>]] [contactsonly [<Boolean>]] [domainonly [<Boolean>]]
        [start|startdate <Date>|Started] [end|enddate <Date>|NotSpecified]
```
The initial `<Boolean>` can be omitted to allow updates to other fields without affecting the current responder state.

`<VacationMessageContent>` is the vacation message, there are four ways to specify it:
* `message|textmessage|htmlmessage <String>` - Use `<String>` as the vacation message
* `file|htmlfile <FileName> [charset <Charset>]` - Read the vacation message from `<FileName>`
* `gdoc|ghtml <UserGoogleDoc>` - Read the vacation message from `<UserGoogleDoc>`
* `gcsdoc|gcshtml <StorageBucketObjectName>` - Read the vacation message from the Google Cloud Storage file `<StorageBucketObjectName>`

It's highly recommended to set (overwrite) start and end date. Otherwise it may not work for users who used vacation messages previously and where the end date is already expired.

Example: 
```gam user@domain.com vacation ON subject "[Out of Office]" file autoreply.eml start 2000-01-01 end 2999-01-01```

## Display vacation
```
gam <UserTypeEntity> show vacation [compact|format|html] [enabledonly]
```
Gam displays the information as an indented list of keys and values.

These are the output formatting options:
* `compact` - Escape carriage returns as \r and newlines as \n in original HTML; this format produces output that can be used as input to GAM
* `format` - Strip HTML keywords leaving basic printable information
* `html` - Show original HTML; this is the default option; the output is human readable but cannot be used an input to GAM

* `enabledonly` - Do not display users with vacation autoreply disabled.
```
gam <UserTypeEntity> print vacation [compact] [enabledonly] [todrive <ToDriveAttribute>*]
```
Gam displays the information in CSV form.

* `compact` - Strip carriage returns and newlines in original HTML; this makes these values easier to process in the CSV file
and can be used as input to GAM.
* `enabledonly` - Do not display users with vacation autoreply disabled.

## Standardize user signatures
You can standardize user signatures by creating a signature template and a CSV file with data for each user.

You can create a signature template by defining the signature in the Gmail Settings GUI of a test user.
You must use the default signature `My signature`.
Use text like `{FirstName}` and `{Email}` in the locations where the actual values will go.

Once you're created the template signature, do the following:
```
$ gam user testuser@domain.com show signature compact > SimpleSig.html
$ more SimpleSig.html
SendAs Address: <testuser@domain.com>
  IsPrimary: True
  Default: True
  Signature: <div dir="ltr">--<div>Name: {FirstName} {LastName}<div>Phone: {Phone}</div><div>Email: {Email}</div></div><div><br></div><div>Company Name</div><div>Company Address</div><div><br></div></div>\n
```
Edit SimpleSig.html and delete all text from `SendAs ` through `Signature: `.
The result should be:
```
<div dir="ltr">--<div>Name: {FirstName} {LastName}<div>Phone: {Phone}</div><div>Email: {Email}</div></div><div><br></div><div>Company Name</div><div>Company Address</div><div><br></div></div>\n
```

This is a sample Users.csv file.
```
email,first,last,phone
bsmith@domain.com,Bob,Smith,510-555-1212 x 123
mjones@domain.com,Mary,Jones,510-555-1212 x 456
```

This command will update the user's signatures.
```
gam csv Users.csv gam user "~email" signature htmlfile SimpleSig.html replace FirstName "~first"  replace LastName "~last" replace Phone "~phone" replace Email "~email"
```