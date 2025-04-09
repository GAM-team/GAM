# Cloud Channel
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Channel Customers](#display-channel-customers)
- [Display Channel Customer Entitlements](#display-channel-customer-entitlements)
- [Display Channel Offers](#display-channel-offers)
- [Display Channel Products](#display-channel-products)
- [Display Channel SKUs](#display-channel-skus)

## API documentation
* [Cloud Channel API](https://cloud.google.com/channel/docs/reference/rest)
* [Filter Customers](https://cloud.google.com/channel/docs/concepts/google-cloud/filter-customers)

## Notes
To use these commands you must add the 'Cloud Channel API' to your project and update your client authorization.
```
gam update project
gam oauth create
```

The Customer ID value that the Cloud Channel API describes is not the Google Workspace Customer ID value; it is unique to the Cloud Channel API.

## Definitions
```
<ChannelCustomerID> ::= <String>
<ProductID> ::= <String>
<ResellerID> ::= <String>

<LanguageCode> ::=
        ach|af|ag|ak|am|ar|az|be|bem|bg|bn|br|bs|ca|chr|ckb|co|crs|cs|cy|da|de|
        ee|el|en|en-gb|en-us|eo|es|es-419|et|eu|fa|fi|fil|fo|fr|fr-ca|fy|
        ga|gaa|gd|gl|gn|gu|ha|haw|he|hi|hr|ht|hu|hy|ia|id|ig|in|is|it|iw|ja|jw|
        ka|kg|kk|km|kn|ko|kri|ku|ky|la|lg|ln|lo|loz|lt|lua|lv|
        mfe|mg|mi|mk|ml|mn|mo|mr|ms|mt|my|ne|nl|nn|no|nso|ny|nyn|oc|om|or|
        pa|pcm|pl|ps|pt-br|pt-pt|qu|rm|rn|ro|ru|rw|
        sd|sh|si|sk|sl|sn|so|sq|sr|sr-me|st|su|sv|sw|
        ta|te|tg|th|ti|tk|tl|tn|to|tr|tt|tum|tw|
        ug|uk|ur|uz|vi|wo|xh|yi|yo|zh-cn|zh-hk|zh-tw|

<ChannelCustomerField> ::=
        alternateemail |
        channelpartnerid |
        cloudidentityid |
        cloudidentityinfo |
        createtime |
        domain |
        languagecode |
        name |
        orgdisplayname |
        orgpostaladdress |
        primarycontactinfo |
        updatetime
<ChannelCustomerFieldList> ::= "<ChannelCustomerField>(,<ChannelCustomerField>)*"

<ChannelCustomerEntitlementField> ::=
        associationinfo |
        commitmentsettings |
        createtime |
        name |
        offer |
        parameters |
        provisionedservice |
        provisioningstate |
        purchaseorderid |
        suspensionreasons |
        trialsettings |
        updatetime
<ChannelCustomerEntitlementFieldList> ::= "<ChannelCustomerEntitlementField>(,<ChannelCustomerEntitlementField>)*"
```
```
<ChannelCustomerOfferField> ::=
        constraints |
        endtime |
        marketinginfo |
        name |
        parameterdefinitions |
        plan |
        pricebyresources |
        sku |
        starttime
<ChannelOfferFieldList> ::= "<ChannelOfferField>(,<ChannelOfferField>)*"

<ChannelProductField> ::=
        marketinginfo |
        name
<ChannelProductFieldList> ::= "<ChannelProductField>(,<ChannelProductField>)*"

<ChannelSKUField> ::=
        marketinginfo |
        name |
        product
<ChannelSKUFieldList> ::= "<ChannelSKUField>(,<ChannelSKUField>)*"
```
## Display Channel Customers
```
gam show channelcustomers
        [resellerid <ResellerID>] [filter <String>]
        [fields <ChannelCustomerFieldList>]
        [maxresults <Number>]
        [formatjson]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

Cloud Channel API documentation for `filter <String>`:
* https://cloud.google.com/channel/docs/concepts/google-cloud/filter-customers

The filters will contain `"`, you must quote `<String>` as follows:
* Linux and MacOS
  * Surround `<String>` with single quotes `'`
  * Embedded `"` in `<String>` are entered as is
  * Example: `gam show channelcustomers filter 'cloud_identity_id="someid"'`
* Windows Command Prompt
  * Surround `<String>` with double quotes `"`
  * Embedded `"` in `<String>` are entered as `\"`
  * Example: `gam show channelcustomers filter "cloud_identity_id=\"someid\""`
* Windows PowerShell
  * Surround `<String>` with single quotes `'`
  * Embedded `"` in `<String>` are entered as `\"`
  * Example: `gam show channelcustomers filter "cloud_identity_id=\"someid\""`

When retrieving lists of customers from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many customers to retrieve in each API call; default is 50, the maximum.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print channelcustomers [todrive <ToDriveAttribute>*]
        [resellerid <ResellerID>] [filter <String>]
        [fields <ChannelCustomerFieldList>]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

Cloud Channel API documentation for `filter <String>`:
* https://cloud.google.com/channel/docs/concepts/google-cloud/filter-customers

The filters will contain `"`, you must quote `<String>` as follows:
* Linux and MacOS
  * Surround `<String>` with single quotes `'`
  * Embedded `"` in `<String>` are entered as is
* Windows Command Prompt
  * Surround `<String>` with double quotes `"`
  * Embedded `"` in `<String>` are entered as `\"`
* Windows PowerShell
  * Surround `<String>` with single quotes `'`
  * Embedded `"` in `<String>` are entered as `\"`

When retrieving lists of customers from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many customers to retrieve in each API call; default is 50, the maximum.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Channel Customer Entitlements
```
gam show channelcustomerentitlements
        ([resellerid <ResellerID>] [customerid <ChannelCustomerID>])|
        (name accounts/<ResellerID>/customers/<ChannelCustomerID>)
        [fields <ChannelCustomerEntitlementsFieldList>]
        [maxresults <Number>]
        [formatjson]
```
If `name accounts/<ResellerID>/customers/<ChannelCustomerID>` is specified, `resellerId <ResellerID>` and `customerid <ChannelCustomerID>`
are ignored.

If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

If `customerid <ChannelCustomerID>` is omitted, the `channel_customer_id` value from `gam.cfg` is used.

When retrieving lists of customer entitlements from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many customer entitlements to retrieve in each API call; default is 100, the maximum.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print channelcustomerentitlements [todrive <ToDriveAttribute>*]
        ([resellerid <ResellerID>] [customerid <ChannelCustomerID>])|
        (name accounts/<ResellerID>/customers/<ChannelCustomerID>)
        [fields <ChannelCustomerEntitlementsFieldList>]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
If `name accounts/<ResellerID>/customers/<ChannelCustomerID>` is specified, `resellerId <ResellerID>` and `customerid <ChannelCustomerID>`
are ignored.

If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

If `customerid <ChannelCustomerID>` is omitted, the `channel_customer_id` value from `gam.cfg` is used.

When retrieving lists of customer entitlements from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many customer entitlements to retrieve in each API call; default is 100, the maximum.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Channel Offers
```
gam show channeloffers
        [resellerid <ResellerID>] [filter <String>] [language <LanguageCode>]
        [fields <ChannelOfferFieldList>]
        [maxresults <Number>]
        [formatjson]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

Cloud Channel API documentation for `filter <String>`:
```
The expression to filter results by name (name of the Offer), sku.name (name of the SKU), or sku.product.name (name of the Product).
* Example 1: sku.product.name=products/p1 AND sku.name!=products/p1/skus/s1
* Example 2: name=accounts/a1/offers/o1
```

When retrieving lists of offers from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many offers to retrieve in each API call; default is 1000, the maximum.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print channeloffers [todrive <ToDriveAttribute>*]
        [resellerid <ResellerID>] [filter <String>] [language <LanguageCode>]
        [fields <ChannelOfferFieldList>]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

Cloud Channel API documentation for `filter <String>`:
```
The expression to filter results by name (name of the Offer), sku.name (name of the SKU), or sku.product.name (name of the Product).
* Example 1: sku.product.name=products/p1 AND sku.name!=products/p1/skus/s1
* Example 2: name=accounts/a1/offers/o1
```
When retrieving lists of offers from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many offers to retrieve in each API call; default is 1000, the maximum.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Channel Products
```
gam show channelproducts
        [resellerid <ResellerID>] [language <LanguageCode>]
        [fields <ChannelProductFieldList>]
        [maxresults <Number>]
        [formatjson]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

When retrieving lists of products from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many products to retrieve in each API call; default is 1000, the maximum.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print channelproducts [todrive <ToDriveAttribute>*]
        [resellerid <ResellerID>] [language <LanguageCode>]
        [fields <ChannelProductFieldList>]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

When retrieving lists of products from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many products to retrieve in each API call; default is 1000, the maximum.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Channel SKUs
```
gam show channelskus
        [resellerid <ResellerID>] [language <LanguageCode>] [productid <ProductID>]
        [fields <ChannelSKUFieldList>]
        [maxresults <Number>]
        [formatjson]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

If `productid <ProductID>` is omitted, SKUs for all products are displayed.

When retrieving lists of SKUs from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many SKUs to retrieve in each API call; default is 1000, the maximum.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print channelskus [todrive <ToDriveAttribute>*]
        [resellerid <ResellerID>] [language <LanguageCode>] [productid <ProductID>]
        [fields <ChannelSKUFieldList>]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
If `resellerId <ResellerID>` is omitted, the `reseller_id` value from `gam.cfg` is used.

If `productid <ProductID>` is omitted, SKUs for all products are displayed.

When retrieving lists of SKUs from Cloud Channel API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many SKUs to retrieve in each API call; default is 1000, the maximum.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
