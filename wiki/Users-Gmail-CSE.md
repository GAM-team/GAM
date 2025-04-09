# Users - Gmail - Client Side Encryption
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Create Gmail CSE Identity](#create-gmail-cse-identity)
- [Update Gmail CSE Identity](#update-gmail-cse-identity)
- [Delete Gmail CSE Identity](#delete-gmail-cse-identity)
- [Display Gmail CSE Identities](#display-gmail-cse-identities)
- [Create Gmail CSE Key Pair](#create-gmail-cse-key-pair)
- [Action Gmail CSE Key Pairs](#action-gmail-cse-key-pairs)
- [Display Gmail CSE Key Pairs](#display-gmail-cse-key-pairs)

## API documentation
* [CSE Identities](https://developers.google.com/gmail/api/reference/rest/v1/users.settings.cse.identities)
* [CSE KeyPairs](https://developers.google.com/gmail/api/reference/rest/v1/users.settings.cse.keypairs)

## Notes

This is an initial, minimally tested release; proceed with care and report all issues.

Setting up Client Side Encryption is not for the faint of heart; here is a start.
* https://support.google.com/a/answer/10741897?hl=en&ref_topic=10742486&sjid=10342493441460488213-NA

Do I personally understand what's going on here? No, I just added the API calls to GAM.

Two sets of files are required for Gmail CSE, these two variables in `gam.cfg` control where GAM looks for these files.
You must edit `gam.cfg` to set the paths you currently use.
```
gmail_cse_incert_dir
        Directory for the S/MIME certificate files used by Gmail Client Side Encryption.
        Default: Blank
gmail_cse_inkey_dir
        Directory for the Key Access Control List (KACL) wrapped private key data files used by Gmail Client Side Encryption.
        Default: Blank
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<FilePath> ::= <String>
<Password> ::= <String>
<KeyPairID> ::= <String>
```
## Create Gmail CSE Identity
Creates and configures a client-side encryption identity that's authorized to send mail from the user account.
Google publishes the S/MIME certificate to a shared domain-wide directory so that people within a Google Workspace organization can encrypt and send mail to the identity.

```
gam <UserTypeEntity> create cseidentity
        (primarykeypairid <KeyPairID>) | (signingkeypairid <KeyPairID> encryptionkeypairid <KeyPairID>)
        [kpemail <EmailAddress>]
        [formatjson]
```
One of the following is required:
* `primarykeypairid <KeyPairID>` - The configuration of a CSE identity that uses the same key pair for signing and encryption.
* `signingkeypairid <KeyPairID> encryptionkeypairid <KeyPairID>` - The configuration of a CSE identity that uses different key pairs for signing and encryption.

If `kpemail <EmailAddress>` is not specified, the user's primary email address is used for the identity.

By default, Gam displays the identity as an indented list of keys and values; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

## Update Gmail CSE Identity
Associates a different key pair with an existing client-side encryption identity. The updated key pair must validate against Google's S/MIME certificate profiles.
```
gam <UserTypeEntity> update cseidentity
        (primarykeypairid <KeyPairID>) | (signingkeypairid <KeyPairID> encryptionkeypairid <KeyPairID>)
        [kpemail <EmailAddress>]
        [formatjson]
```
One of the following is required:
* `primarykeypairid <KeyPairID>` - The configuration of a CSE identity that uses the same key pair for signing and encryption.
* `signingkeypairid <KeyPairID> encryptionkeypairid <KeyPairID>` - The configuration of a CSE identity that uses different key pairs for signing and encryption.

bIf `kpemail <EmailAddress>` is not specified, the key pair for the user's primary email address is identity updated.

By default, Gam displays the identity as an indented list of keys and values; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

## Delete Gmail CSE Identity
Deletes a client-side encryption identity. The authenticated user can no longer use the identity to send encrypted messages.
You cannot restore the identity after you delete it. Instead, use the `create cseidentity`  to create another identity with the same configuration.

```
gam <UserTypeEntity> delete cseidentity [kpemail <EmailAddress>]
```
If `kpemail <EmailAddress>` is not specified, the identity for the user's primary email address is deleted.

## Display Gmail CSE Identities
### Display a client-side encryption identity configuration.
```
gam <UserTypeEntity> info cseidentity [kpemail <EmailAddress>]
        [formatjson]
```
If `kpemail <EmailAddress>` is not specified, the user's primary email address is used for the identity.


### Display all of the client-side encrypted identities for an authenticated user.
```
gam <UserTypeEntity> show cseidentities
        [formatjson]
```
By default, Gam displays the identity as an indented list of keys and values; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print cseidentities [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Create Gmail CSE Key Pair
Create a CSE Key Pair for the primary address of a user.
```
gam <UserTypeEntity> create csekeypair
        [incertdir <FilePath>] [inkeydir <FilePath>]
        [addidentity [<Boolean>]] [kpemail <EmailAddress>]
        [showpem] [showkaclsdata] [formatjson|returnidonly]
```
* The S/MIME certificate files for the users are in the `incertdir <FilePath>` folder/directory.
* If this option is not specified, the directory is taken from `gam.cfg/gmail_cse_incert_dir`.
* The files must be named `user@domain.com.p7pem`.
* The certificate contains the public key and its certificate chain. The chain must be in PKCS#7 format and use PEM encoding and ASCII armor.

* The Key Access Control List (KACL) wrapped private key data files are in the `inkeydir <FilePath>` folder/directory.
* If this option is not specified, the directory is taken from `gam.cfg/gmail_cse_inkey_dir`.
* The files must be named `user@domain.com.wrap`.
* The files are in JSON format with two keys:
    * `kacls_url` - The URI of the key access control list service that manages the private key.
    * `wrapped_private_key` - Opaque data generated and used by the key access control list service.

By default, the `pem` and `kaclsdata` fields will not be displayed unless the corresponding `showpem` and `showkaclsdata` option is specified.

By default, Gam displays the new key pair as an indented list of keys and values; the following options cause the output to be displayed in alternate forms.
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display just the new `<KeyPairID>`.

If `addidentity` or `addidentity true` is specified, a client-side encryption identity is created with the new key pair.
If `kpemail <EmailAddress>` is not specified, the user's primary email address is used for the identity.

By default, Gam displays the identity as an indented list of keys and values; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.
* `returnidonly` - Display just the new `<KeyPairID>-<EmailAddress>`.


## Action Gmail CSE Key Pairs
### Display pem and kaclsdata fields
By default, the `pem` and `kaclsdata` fields will not be displayed unless the corresponding `showpem` and `showkaclsdata` option is specified.

### Disable
Turns off a client-side encryption key pair. The authenticated user can no longer use the key pair to decrypt incoming CSE message texts or sign outgoing CSE mail.
```
gam <UserTypeEntity> disable csekeypair <KeyPairID>
        [showpem] [showkaclsdata] [formatjson]
```
By default, Gam displays the disabled key pair as an indented list of keys and values; the following option causes the output to be displayed in alternate forms.
* `formatjson` - Display the fields in JSON format.

### Enable
Turn on a client-side encryption key pair that was turned off. The key pair becomes active again for any associated client-side encryption identities.
```
gam <UserTypeEntity> ensable csekeypair <KeyPairID>
        [showpem] [showkaclsdata] [formatjson]
```
By default, Gam displays the enabled key pair as an indented list of keys and values; the following option causes the output to be displayed in alternate forms.
* `formatjson` - Display the fields in JSON format.

### Obliterate
Delete a client-side encryption key pair permanently and immediately. You can only permanently delete key pairs that have been turned off for more than 30 days.
To turn off a key pair, use `disable csekeypair`.
```
gam <UserTypeEntity> obliterate csekeypair <KeyPairID>
```

Gmail can't restore or decrypt any messages that were encrypted by an obliterated key. Authenticated users and Google Workspace administrators lose access to reading the encrypted messages.

## Display Gmail CSE Key Pairs
### Display pem and kaclsdata fields
By default, the `pem` and `kaclsdata` fields will not be displayed unless the corresponding `showpem` and `showkaclsdata` option is specified.

### Display an existing client-side encryption key pair.
```
gam <UserTypeEntity> info csekeypair <KeyPairID>
        [showpem] [showkaclsdata] [formatjson]
```
By default, Gam displays the key pairs as an indented list of keys and values; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.


### Display all client-side encryption key pairs for an authenticated user.
```
gam <UserTypeEntity> show csekeypairs
        [showpem] [showkaclsdata] [formatjson]
```
By default, Gam displays the key pairs as an indented list of keys and values; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print csekeypairs [todrive <ToDriveAttribute>*]
        [showpem] [showkaclsdata] [formatjson [quotechar <Character>]]
```
By default, Gam displays the key pairs as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
