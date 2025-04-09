# Domains
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Create a domain](#create-a-domain)
- [Promote a domain to be primary](#promote-a-domain-to-be-primary)
- [Delete a domain](#delete-a-domain)
- [Display domains](#display-domains)
- [Display domains count](#display-domains-count)
- [Create and delete domain aliases](#create-and-delete-domain-aliases)
- [Display domain aliases](#display-domain-aliases)
- [Display domain aliases count](#display-domain-aliases-count)

## API documentation
* [Directory API - Domains](https://developers.google.com/admin-sdk/directory/reference/rest/v1/domains)

## Definitions
```
<DomainAlias> ::= <String>
<DomainName> ::= <String>(.<String>)+
```
## Create a domain
```
gam create domain <DomainName>
```
## Promote a domain to be primary
```
gam update domain <DomainName> primary
```
## Delete a domain
```
gam delete domain <DomainName>
```
## Display domains
```
gam info domain [<DomainName>]
        [formatjson]
gam show domains
        [formatjson]
```
For `info`, if `<DomainName>` is omitted, information about the primary domain will be displayed.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print domains [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields.
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display domains count
Display the number of domains.
```
gam print|show domains
        showitemcountonly
```

## Create and delete domain aliases
```
gam create domainalias|aliasdomain <DomainAlias> <DomainName>
gam delete domainalias|aliasdomain <DomainAlias>
```
## Display domain aliases
```
gam info domainalias|aliasdomain <DomainAlias>
        [formatjson]
gam show domainaliases|aliasdomains
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print domainaliases|aliasdomains [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields.
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display domain aliases count
Display the number of domain aliases.
```
gam print|show domainaliases|aliasdomains
        showitemcountonly
```
