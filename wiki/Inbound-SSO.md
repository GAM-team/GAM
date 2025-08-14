# Inbound SSO
- [Setup SSO](https://support.google.com/a/answer/12032922)
- [Admin Console](https://admin.google.com/ac/security/sso)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Setup SSO](#setupsso)
- [Manage profiles](#manage-profiles)
- [Display profiles](#display-profiles)
- [Manage credentials](#manage-credentials)
- [Display credentials](#display-credentials)
- [Manage assignments](#manage-assignments)
- [Display assignments](#display-assignments)

## API documentation
* [Cloud Identity API - Inbound SAML SSO Profiles](https://cloud.google.com/identity/docs/reference/rest/v1beta1/inboundSamlSsoProfiles)
* [Cloud Identity API - Inbound SAML SSO Profiles idp Credentials](https://cloud.google.com/identity/docs/reference/rest/v1beta1/inboundSamlSsoProfiles.idpCredentials)
* [Cloud Identity API - Inbound OIDC SSO Profiles](https://cloud.google.com/identity/docs/reference/rest/v1beta1/inboundOidcSsoProfiles)
* [Cloud Identity API - Inbound SSO Assignments](https://cloud.google.com/identity/docs/reference/rest/v1beta1/inboundSsoAssignments)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<FileName> ::= <String>
<OrgUnitPath> ::= /|(/<String>)+

<SSOProfileDisplayName> ::= <String>
<SSOProfileName> ::= id:inboundSamlSsoProfiles/<String>
<SSOProfileItem> ::= <SSOProfileDisplayName>|<SSOProfileName>
<SSOProfileItemList> ::= "<SSOProfileItem>(,<SSOProfileItem>)*"

<SSOCredentialsName> ::= [id:]inboundSamlSsoProfiles/<String>/idpCredentials/<String>

<SSOAssignmentName> ::= [id:]inboundSsoAssignments/<String>
<SSOAssignmentSelector> ::=
        <SSOAssignmentName> |
        groups/<String> |
        group:<EmailAddress> |
        orgunits/<String> |
        orgunit:<OrgUnitPath>
```
## Manage profiles
```
gam create inboundssoprofile [saml|oidc] [name <SSOProfileDisplayName>]
        [entityid <String>] [loginurl <URL>] [logouturl <URL>] [changepasswordurl <URL>]
        [returnnameonly]
gam update inboundssoprofile [saml|oidc] <SSOProfileItem>
        [entityid <String>] [loginurl <URL>] [logouturl <URL>] [changepasswordurl <URL>]
        [returnnameonly]
```
Select type of profile:
* `saml` - SAML profile; this is the default
* `oidc` - OIDC profile

By default, all fields of the created|updated profile are displayed;
use the `returnnameonly` option to have GAM display just the profile name of the created|updated profile.
This will be useful in scripts that create|update a profile and then want to perform subsequent GAM commands that
reference the profile.

If `returnnameonly` is specified, `inProgress` is returned if the API does not return a complete result.

```
gam delete inboundssoprofile [saml|oidc] <SSOProfileItem>
```
Select type of profile:
* `saml` - SAML profile; this is the default
* `oidc` - OIDC profile

## Display profiles
Display a specific profile.
```
gam info inboundssoprofile [all|saml|oidc] <SSOProfileItem>
        [formatjson]
```
Select type of profile:
* `all` - All profiles are displayed; this is the default
* `saml` - SAML profile
* `oidc` - OIDC profile

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display profiles.
```
gam show inboundssoprofiles [all|saml|oidc]
        [formatjson]
```
Select profiles to display:
* `all` - All profiles are displayed; this is the default
* `saml` - Display SAML profiles
* `oidc` - Display OIDC profiles

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display profiles in a CSV file.
```
gam print inboundssoprofiles [all|saml|oidc] [todrive <ToDriveAttribute>*]
        [[formatjson [quotechar <Character>]]
```
Select profiles to display:
* `all` - All profiles are displayed; this is the default
* `saml` - Display SAML profiles
* `oidc` - Display OIDC profiles

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage credentials
```
gam create inboundssocredential profile <SSOProfileItem>
        (pemfile <FileName>)|(generatekey [keysize 1024|2048|4096]) [replaceolddest]
gam delete inboundssocredential <SSOCredentialsName>
```

## Display credentials
Display a specific credential.
```
gam info inboundssocredential <SSOCredentialsName>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display all credentials.
```
gam show inboundssocredentials [profile|profiles <SSOProfileItemList>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display all credentials in a CSV file.
```
gam print inboundssocredentials [profile|profiles <SSOProfileItemList>]
        [[formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage assignments
```
gam create inboundssoassignment
        (group <GroupItem> rank <Number>)|(ou|org|orgunit <OrgUnitItem>)
        (mode sso_off)|(mode saml_sso profile <SSOProfileItem>)(mode domain_wide_saml_if_enabled)
        [neverredirect]
gam update inboundssoassignment  <SSOAssignmentName>
        [(group <GroupItem> rank <Number>)|(ou|org|orgunit <OrgUnitItem>)]
        [(mode sso_off)|(mode saml_sso profile <SSOProfileItem>)(mode domain_wide_saml_if_enabled)]
        [neverredirect]
gam delete inboundssoassignment <SSOAssignmentSelector>
```

## Display assignments
Display a specific assignment.
```
gam info inboundssoassignment <SSOAssignmentSelector>
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display all assignments.
```
gam show inboundssoassignments
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display all assignments in a CSV file.
```
gam print inboundssoassignments [todrive <ToDriveAttribute>*]
        [[formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
