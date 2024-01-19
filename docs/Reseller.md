# Reseller
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Manage Multiple Domains](#manage-multiple-domains)
- [Definitions](#definitions)
- [Manage Resold Customers](#manage-resold-customers)
- [Display Resold Customers](#display-resold-customers)
- [Manage Resold Subscriptions](#manage-resold-subscriptions)
- [Display Resold Subscriptions](#display-resold-subscriptions)

## API documentation
* https://developers.google.com/admin-sdk/reseller/v1/reference/customers
* https://developers.google.com/admin-sdk/reseller/v1/reference/subscriptions

## Notes

Updated handling of `seats` option in `gam create|update resoldsubscription` to properly assign
the API fields `numberOfSeats` and `maximumNumberOfSeats`.
Prior to version 6.50.00, this is how the `seats <NumberOfSeats> <MaximumNumberOfSeats>` option was processed:
  * Plan name `ANNUAL_MONTHLY_PAY` or `ANNUAL_YEARLY_PAY`
    * `seats <NumberOfSeats>` - `<NumberOfSeats>` was properly passed to the API
    * `seats <NumberOfSeats> <MaximumNumberOfSeats>` - `<NumberOfSeats>` was properly passed to the API; `<MaximumNumberOfSeats>` was passed to the API which ignored it
  * Plan name `FLEXIBLE` or `TRIAL`
    * `seats <NumberOfSeats>` - `<NumberOfSeats>` was improperly passed to the API; an API error was generated
    * `seats <NumberOfSeats> <MaximumNumberOfSeats>` - `<MaximumNumberOfSeats>` was properly passed to the API; `<NumberOfSeats>` was passed to the API which ignored it

Now, you can still use the above option which has been corrected or you can specify `seats <Number>` which will be properly passed in the correct form to the API based on plan name.

## Manage Multiple Domains
Thanks to Duncan Isaksen-Loxton for a script to help manage multiple domains.

* See: https://gist.github.com/65/b5e9cee9b5812b487b8ae3e8256e262b

## Definitions
```
<CustomerID> ::= <String>
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<ResoldCustomerAttribute> ::=
        (email|alternateemail <EmailAddress>)|
        (contact|contactname <String>)|
        (phone|phonenumber <String>)|
        (name|organizationname <String>)|
        (address|address1|addressline1 <String>)|
        (address2|addressline2 <String>)|
        (address3|addressline3 <String>)|
        (city|locality <String>)|
        (state|region <String>)|
        (zipcode|postal|postalcode <String>)|
        (country|countrycode <String>)
<SKUID> ::=
        nv:<String>:<String> |
        20gb | drive20gb | googledrivestorage20gb | Google-Drive-storage-20GB |
        50gb | drive50gb | googledrivestorage50gb | Google-Drive-storage-50GB |
        200gb | drive200gb | googledrivestorage200gb | Google-Drive-storage-200GB |
        400gb | drive400gb | googledrivestorage400gb | Google-Drive-storage-400GB |
        1tb | drive1tb | googledrivestorage1tb | Google-Drive-storage-1TB |
        2tb | drive2tb | googledrivestorage2tb | Google-Drive-storage-2TB |
        4tb | drive4tb | googledrivestorage4tb | Google-Drive-storage-4TB |
        8tb | drive8tb | googledrivestorage8tb | Google-Drive-storage-8TB |
        16tb | drive16tb | googledrivestorage16tb | Google-Drive-storage-16TB |
        assuredcontrols | 1010390001 |
        bce | beyondcorp | beyondcorpenterprise | 1010400001 |
        cdm | chrome | googlechromedevicemanagement | Google-Chrome-Device-Management |
        cloudidentity | identity | 1010010001 |
        cloudidentitypremium | identitypremium | 1010050001 |
        cloudsearch | 1010350001 |
        gsuitebasic | gafb | gafw | basic | Google-Apps-For-Business |
        gsuitebusiness | gau | gsb | unlimited | Google-Apps-Unlimited |
        gsuitebusinessarchived | gsbau | businessarchived | 1010340002 |
        gsuiteenterprisearchived | gseau | enterprisearchived | 1010340001 |
        gsuiteenterpriseeducation | gsefe | e4e | 1010310002 |
        gsuiteenterpriseeducationstudent | gsefes | e4es | 1010310003 |
        gsuitegov | gafg | gsuitegovernment | Google-Apps-For-Government |
        gsuitelite | gal | gsl | lite | Google-Apps-Lite |
        gwep | workspaceeducationplus | 1010310008 |
        gwepstaff | workspaceeducationplusstaff | 1010310009 |
        gwepstudent | workspaceeducationplusstudent | 1010310010 |
        gwes | workspaceeducationstandard | 1010310005 |
        gwesstaff | workspaceeducationstandardstaff | 1010310006 |
        gwesstudent | workspaceeducationstandardstudent | 1010310007 |
        gwetlu | workspaceeducationupgrade | 1010370001 |
        meetdialing | googlemeetglobaldialing | 1010360001 |
        postini | gams | gsuitegams | gsuitepostini | gsuitemessagesecurity | Google-Apps-For-Postini |
        standard | free | Google-Apps |
        vault | googlevault | Google-Vault |
        vfe | googlevaultformeremployee | Google-Vault-Former-Employee |
        voicepremier | gvpremier | googlevoicepremier | 1010330002 |
        voicestandard | gvstandard | googlevoicestandard | 1010330004 |
        voicestarter | gvstarter | googlevoicestarter | 1010330003 |
        wsbizplus | workspacebusinessplus | 1010020025 |
        wsbizplusarchived | workspacebusinessplusarchived | 1010340003 |
        wsbizstan | workspacebusinessstandard | 1010020028 |
        wsbizstarter | workspacebusinessstarter | wsbizstart | 1010020027 |
        wsentess | workspaceenterpriseessentials | 1010060003 |
        wsentplus | workspaceenterpriseplus | gae | gse | enterprise | gsuiteenterprise | 1010020020 |
        wsentstan | workspaceenterprisestandard | 1010020026 |
        wsentstanarchived | workspaceenterprisestandardarchived | 1010340004 |
        wsentstarter | workspaceenterprisestarter | 1010020029 | wes |
        wsess | workspaceesentials | gsuiteessentials | essentials | d4e | driveenterprise | drive4enterprise | 1010060001 |
        wsflw | workspacefrontline | workspacefrontlineworker | 1010020030
```
## Manage Resold Customers
```
gam create resoldcustomer <CustomerDomain> (customer_auth_token <String>)
        <ResoldCustomerAttribute>+
gam update resoldcustomer <CustomerID> [customer_auth_token <String>]
        <ResoldCustomerAttribues>+
```
## Display Resold Customers
```
gam info resoldcustomer <CustomerID> [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Manage Resold Subscriptions
```
gam create resoldsubscription <CustomerID> (sku <SKUID>)
         (plan annual_monthly_pay|annual_yearly_pay|flexible|trial)
         (seats <Number>)
         [customer_auth_token <String>] [deal <String>] [purchaseorderid <String>]
gam update resoldsubscription <CustomerID> <SKUID>
        activate|suspend|startpaidservice|
        (renewal auto_renew_monthly_pay|auto_renew_yearly_pay|cancel|
                 renew_current_users_monthly_pay|renew_current_users_yearly_pay|
                 switch_to_pay_as_you_go)|
        (seats <Number>)|
        (plan annual_monthly_pay|annual_yearly_pay|flexible|trial [deal <String>]
        [purchaseorderid <String>] [seats <Number>])
gam delete resoldsubscription <CustomerID> <SKUID> cancel|downgrade|transfer_to_direct
```
## Display Resold Subscriptions
```
gam info resoldsubscription <CustomerID> <SKUID>
        [formatjson]
gam show resoldsubscriptions
        [customerid <CustomerID> [customer_auth_token <String>]]  [customer_prefix <String>]
        [maxresults <Number>]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `maxresults` - Maximum number of results per page. The default is 100 (maximum).
* `formatjson` - Display the fields in JSON format.
```
gam print resoldsubscriptions [todrive <ToDriveAttribute>*]
        [customerid <CustomerID> [customer_auth_token <String>]] [customer_prefix <String>]
        [maxresults <Number>]
        [formatjson [quotechar <Character>]]
```
By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
