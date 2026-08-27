# Cloud Identity Allowlisted Domains
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Create Cloud Identity Allowlisted Domains](#create-cloud-identity-allowlisted-domains)
- [Delete Cloud Identity Allowlisted Domains](#delete-cloud-identity-allowlisted-domains)
- [Display Cloud Identity Allowlisted Domains](#display-cloud-identity-allowlisted-domains)

## API documentation
* [AllowlistedDomains](https://docs.cloud.google.com/identity/docs/reference/rest/v1/allowlistedDomains)

## Notes
To use these commands you must update your client access authentication.
You'll enter 19 or 19r to turn on the Cloud Identity Policy scope; then continue
with authentication.
```
gam oauth delete
gam oauth create
...
[*] 19)  Cloud Identity API - Allowlisted Domains (supports readonly)
```
The commands to process Allowedlisted Domains were added in version `7.48.00`.

## Definitions
```
<AllowlistedDomainsID> ::= allowlistedDomains/<String>|<String>
<AllowlistedDomainsIDList> ::= "<AllowlistedDomainsID>(,<AllowlistedDomainsID>)*"
<AllowlistedDomainsIDEntity> ::=
        <AllowlistedDomainsIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>

<DomainName> ::= <String>(.<String>)+
<DomainNameList> ::= "<DomainName>(,<DomainName>)*"
```

## Create Cloud Identity Allowlisted Domains
```
gam create allowlisteddomains <DomainNameList>
```
## Delete Cloud Identity Allowlisted Domains
```
gam delete allowlisteddomains <AllowlistedDomainsIDEntity>
```

## Display Cloud Identity Allowlisted Domains
Display selected Allowlisted Domains
```
gam info allowlisteddomain <AllowlistedDomainsIDEntity>
        [formatjson]
```

Display all or filtered Allowlisted Domains.
```
gam show allowlisteddomains
        [filter <String>]
        [formatjson]
```
By default, all Allowlisted Domains are displayed.
* `filter <String>` - Display a specific Allowlisted Domain: `filter "domain=xyz.com"`

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print allowlisteddomains [todrive <ToDriveAttribute>*]
        [filter <String>]
        [formatjson [quotechar <Character>]]
```
By default, all Allowlisted Domains are displayed.
* `filter <String>` - Display a specific Allowlisted Domain: `filter "domain=xyz.com"`

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

