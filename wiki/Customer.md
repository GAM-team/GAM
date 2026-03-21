# Customer
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Update customer](#update-customer)
- [Display customer](#display-customer)
- [Display instance](#display-instance)
- [Display Customer ID](#display-customer-id)
- [Display GCP organization ID](#display-gcp-organization-id)

## API documentation
* [Directory API - Customers](https://developers.google.com/admin-sdk/directory/reference/rest/v1/customers)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>

<CustomerAttribute> ::=
        (primary <DomainName>)|
        (adminsecondaryemail|alternateemail <EmailAddress>)|
        (contact|contactname <String>)|
        (language <LanguageCode>)|
        (phone|phonenumber <String>)|
        (name|organizationname <String>)|
        (address|address1|addressline1 <String>)|
        (address2|addressline2 <String>)|
        (address3|addressline3 <String>)|
        (city|locality <String>)|
        (state|region <String>)|
        (zipcode|postal|postalcode <String>)|
        (country|countrycode <String>)
```
## Update customer
```
gam update customer <CustomerAttribute>*
```
## Display customer
```
gam info customer [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display instance
```
gam info instance [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display Customer ID
You can get and set the `gam.cfg/customer_id` value with these commands:
```
$ gam info customerid             
C78abc9de
$ gam config customer_id C78abc9de save
```
## Display GCP organization ID
You can get and set the `gam.cfg/gcp_org_id` value with these commands:
```
$ gam info gcporgid             
organizations/906207637890
$ gam config gcp_org_id organizations/906207637890 save
```

