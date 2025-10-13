# Cloud Identity Policies
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Policies](#policies)
- [Display Cloud Identity Policies](#display-cloud-identity-policies)

## API documentation
* [Policy API](https://cloud.google.com/identity/docs/reference/rest/v1/policies)
* [Policy Settings](https://cloud.google.com/identity/docs/concepts/supported-policy-api-settings)

## Notes
To use these commands you must update your client access authentication.
You'll enter 20r to turn on the Cloud Identity Policy scope; then continue
with authentication.
```
gam oauth delete
gam oauth create
...
[R] 20)  Cloud Identity - Policy (supports readonly)
```
You must enable access to policies in the GCP cloud console.

* Login at console.cloud.google.com
* In the upper left click the three lines to the left of Google Cloud and select IAM & Admin
* Under IAM & Admin select IAM
* Click in the box to the right of Google Cloud
* Click the three dots at the right and select IAM/Permissions
* Now you should be at "Permissions for organization ..."
* Click on Grant Access
* Enter the GAM project creator address in Principals
* Click in the Select a role box
* Type orgpolicy.policyAdmin in the Filter box
* Click Organization Policy Administrator
* Click Save

## Definitions
```
<CIPolicyName> ::= policies/<String>|settings/<String>|<String>
<CIPolicyNameList> ::= "<CIPolicyName>(,<CIPolicyName>)*"
<CIPolicyNameEntity> ::=
        <CIPolicyNameList> | <FileSelector> | <CSVFileSelector>

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>
```

## Policies
These are the supported policies GAM can show today.

See: https://cloud.google.com/identity/docs/concepts/supported-policy-api-settings

## Display Cloud Identity Policies
Display selected policies.
```
gam info policies <CIPolicyEntity>
        [nowarnings] [noappnames]
        [formatjson]
```

Select policies::
* `polices/<String>` - A policy name, `policies/ahv4hg7qc24kvaghb7zihwf4riid4`
* `settings/<String>` - A policy setting type, `settings/workspace_marketplace.apps_allowlist`
* `<String>` - A policy setting type, `workspace_marketplace.apps_allowlist`

By default, policy warnings are displayed, use the 'nowarnings` option to suppress their display.

By default,  additional API calls are made for `settings/workspace_marketplace.apps_allowlist`
to get the application name for the application ID. Use option `noappnames` to suppress these calls.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

Display all or filtered policies.
```
gam show policies
        [filter <String>] [nowarnings] [noappnames]
        [group <REMatchPattern>] [ou|org|orgunit <REMatchPattern>]
        [formatjson]
```
By default, all policies are displayed.
* `filter <String>` - Display filtered policies, See https://cloud.google.com/identity/docs/reference/rest/v1beta1/policies/list
* `group <REMatchPattern>` - Only display policies whose group email address matches the `<REMatchPattern>`
* `ou|org|orgunit <REMatchPattern>` - Only display policies whose OU path matches the `<REMatchPattern>`

By default, policy warnings are displayed, use the `nowarnings` option to suppress their display.

By default,  additional API calls are made for `settings/workspace_marketplace.apps_allowlist`
to get the application name for the application ID. Use option `noappnames` to suppress these calls.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print policies [todrive <ToDriveAttribute>*]
        [filter <String>] [nowarnings] [noappnames]
        [group <REMatchPattern>] [ou|org|orgunit <REMatchPattern>]
        [formatjson [quotechar <Character>]]
```
By default, all policies are displayed:
* `filter <String>` - Display filtered policies, See https://cloud.google.com/identity/docs/reference/rest/v1beta1/policies/list
* `group <REMatchPattern>` - Only display policies whose group email address matches the `<REMatchPattern>`
* `ou|org|orgunit <REMatchPattern>` - Only display policies whose OU path matches the `<REMatchPattern>`

By default, policy warnings are displayed, use the `nowarnings` option to suppress their display.

By default,  additional API calls are made for `settings/workspace_marketplace.apps_allowlist`
to get the application name for the application ID. Use option `noappnames` to suppress these calls.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Examples
Print all service status policies.
```
gam redirect csv ./ServiceStatusPolicies.csv print policies filter "setting.type.matches('.*service_status')"
```

Print all polices that apply directly to the OU "/Staff".
```
gam redirect csv ./StaffPolicies.csv print policies ou "^/Staff$"
```

Print all polices that apply to the OU "/Staff" and its sub-OUs.
```
gam redirect csv ./StaffPolicies.csv print policies ou "^/Staff"
```
