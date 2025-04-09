# Users - Gmail - S/MIME
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Create Gmail S/MIME configuration](#create-gmail-smime-configuration)
- [Update Gmail S/MIME configuration](#update-gmail-smime-configuration)
- [Delete Gmail S/MIME configuration](#delete-gmail-smime-configuration)
- [Display Gmail S/MIME configurations](#display-gmail-smime-configurations)

## API documentation
* [Gmail API - S-MIME](https://developers.google.com/gmail/api/v1/reference/users.settings.sendAs.smimeInfo)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<FileName> ::= <String>
<Password> ::= <String>
<S/MIMEID> ::= <String>
```
## Create Gmail S/MIME configuration
Create an S/MIME configuration for a sendas address of a user.
```
gam <UserTypeEntity> create|add smime file <FileName> [password <Password>]
        [sendas|sendasemail <EmailAddress>] [default]
```
`<FileName>` is in PKCS#12 format and contains a single private/public key pair and certificate chain. 
If the PKCS#12 data is encrypted, `password <Password>`  should be set appropriately.

If `sendas|sendasemail <EmailAddress>` is not specified, the user's primary email address is used as the sendas address.

Use `default` to indicate that this configuration is the default for the sendas address.

## Update Gmail S/MIME configuration
Update an S/MIME configuration to be the default for a sendas address of a user.
```
gam <UserTypeEntity> update smime default
        [id <S/MIMEID>] [sendas|sendasemail <EmailAddress>]
```
If `sendas|sendasemail <EmailAddress>` is not specified, the user's primary email address is used as the sendas address.

If `id <S/MIMEID>` is specified, that configuration is updated. Otherwise, the configurations for the sendas address are obtained
and if there is only one, it is made the default. If there are none or more than one configurations, a warning is issued.

## Delete Gmail S/MIME configuration
Delete an S/MIME configuration from a sendas address of a user.
```
gam <UserTypeEntity> delete smime
        [id <S/MIMEID>] [sendas|sendasemail <EmailAddress>]
```
If `sendas|sendasemail <EmailAddress>` is not specified, the user's primary email address is used as the sendas address.

If `id <S/MIMEID>` is specified, that configuration is deleted. Otherwise, the configurations for the sendas address are obtained
and if there is only one, it is deleted. If there are none or more than one configurations, a warning is issued.

## Display Gmail S/MIME configurations
```
gam <UserTypeEntity> show smimes
        [primary|default|(sendas|sendasemail <EmailAddress>)]
```
Gam displays the information as an indented list of keys and values.
```
gam <UserTypeEntity> print smimes [todrive <ToDriveAttribute>*]
        [primary|default|(sendas|sendasemail <EmailAddress>)]
```
Gam displays the information in CSV form.

By default, the S/MIME configurations for all of the user's sendas addresses  are displayed.
* `primary` - Display the  configuration for the user's primary email address
* `default` - Display the configuration for the user's default email address
* `sendas|sendasemail <EmailAddress>` - Display the configuration for the specific sendas address
