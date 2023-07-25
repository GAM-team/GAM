# Licenses
- [API documentation](#api-documentation)
- [License Products and SKUs](#license-products-and-skus)
- [Definitions](#definitions)
- [Notes](#Notes)
- [Display license counts](#display-license-counts)
- [Display licenses](#display-licenses)
- [Add licenses](#add-licenses)
- [Update licenses](#update-licenses)
- [Delete licenses](#delete-licenses)
- [Synchronize licenses](#synchronize-licenses)

## API documentation
* https://developers.google.com/admin-sdk/licensing/v1/reference/licenseAssignments

## License Products and SKUs
* https://developers.google.com/admin-sdk/licensing/v1/how-tos/products

| Product Name | Product ID |
|--------------|------------|
| AppSheet | 101038 |
| Assured Controls | 101039 |
| Beyond Corp Enterprise | 101040 |
| Cloud Identity Free | 101001 |
| Cloud Identity Premium | 101005 |
| Cloud Search | 101035 |
| Google Chrome Device Management | Google-Chrome-Device-Management |
| Google Drive Storage | Google-Drive-storage |
| Google Meet Global Dialing | 101036 |
| Google Vault |Google-Vault |
| Google Voice | 101033 |
| Google Workspace Archived User | 101034 |
| Google Workspace for Education | 101031 |
| Google Workspace for Education | 101037 |
| Google Workspace | Google-Apps |

| License Name | License SKU | Abbreviation  |
|--------------|-------------|---------------|
| AppSheet Core | 1010380001 | appsheetcore |
| AppSheet Enterprise Standard | 1010380002 | appsheetstandard |
| AppSheet Enterprise Plus | 1010380003 | appsheetplus |
| Assured Controls | 1010390001 | assuredcontrols |
| Beyond Corp Enterprise | 1010400001 | bce |
| Cloud Identity Free | 1010010001 | cloudidentity |
| Cloud Identity Premium | 1010050001 | cloudidentitypremium |
| Cloud Search | 1010350001 | cloudsearch |
| G Suite Basic | Google-Apps-For-Business | gsuitebasic |
| G Suite Business | Google-Apps-Unlimited | gsuitebusiness |
| G Suite Legacy | Google-Apps | standard |
| G Suite Lite | Google-Apps-Lite | gsuitelite |
| Google Apps Message Security | Google-Apps-For-Postini | postini |
| Google Chrome Device Management | Google-Chrome-Device-Management | cdm |
| Google Drive Storage 16TB | Google-Drive-storage-16TB | 16tb |
| Google Drive Storage 1TB | Google-Drive-storage-1TB | 1tb |
| Google Drive Storage 200GB | Google-Drive-storage-200GB | 200gb |
| Google Drive Storage 20GB | Google-Drive-storage-20GB | 20gb |
| Google Drive Storage 2TB | Google-Drive-storage-2TB | 2tb |
| Google Drive Storage 400GB | Google-Drive-storage-400GB | 400gb |
| Google Drive Storage 4TB | Google-Drive-storage-4TB | 4tb |
| Google Drive Storage 50GB | Google-Drive-storage-50GB | 50gb |
| Google Drive Storage 8TB | Google-Drive-storage-8TB | 8tb |
| Google Meet Global Dialing | 1010360001 | meetdialing,googlemeetglobaldialing |
| Google Vault Former Employee | Google-Vault-Former-Employee | vfe |
| Google Vault | Google-Vault | vault |
| Google Voice Premier | 1010330002 | voicepremier |
| Google Voice Standard | 1010330004 | voicestandard |
| Google Voice Starter | 1010330003 | voicestarter |
| Google Workspace Business - Archived User | 1010340002 | gsuitebusinessarchived |
| Google Workspace Business Plus - Archived User | 1010340003 | wsbizplusarchived |
| Google Workspace Business Plus | 1010020025 | wsbizplus |
| Google Workspace Business Standard | 1010020028 | wsbizstan |
| Google Workspace Business Starter | 1010020027 | wsbizstarter |
| Google Workspace Enterprise Essentials | 1010060003 | wsentess |
| Google Workspace Enterprise Plus - Archived User | 1010340001 | gsuiteenterprisearchived |
| Google Workspace Enterprise Plus | 1010020020 | wsentplus |
| Google Workspace Enterprise Standard - Archived User | 1010340004 | wsentstanarchived |
| Google Workspace Enterprise Standard | 1010020026 | wsentstan |
| Google Workspace Enterprise Starter | 1010020029 | wsentstarter |
| Google Workspace Essentials | 1010060001 | wsess |
| Google Workspace Government | Google-Apps-For-Government | gsuitegov |
| Google Workspace for Education Plus (Extra Student) | 1010310010 | gwepstudent |
| Google Workspace for Education Plus (Staff) | 1010310009 | gwepstaff |
| Google Workspace for Education Plus - Legacy (Student) | 1010310003 | gsuiteenterpriseeducationstudent |
| Google Workspace for Education Plus - Legacy | 1010310002 | gsuiteenterpriseeducation |
| Google Workspace for Education Plus | 1010310008 | gwep |
| Google Workspace for Education Standard (Extra Student) | 1010310007 | gwesstudent |
| Google Workspace for Education Standard (Staff) | 1010310006 | gwesstaff |
| Google Workspace for Education Standard | 1010310005 | gwes |
| Google Workspace for Education: Teaching and Learning Upgrade | 1010370001 | gwetlu |
| Google Workspace Frontline | 1010020030 | wsflw,workspacefrontline,workspacefrontlineworker |

## Definitions
```
<ProductID> ::=
        nv:<String> |
        101001 |
        101005 |
        101031 |
        101033 |
        101034 |
        101035 |
        101036 |
        101037 |
        101038 |
        101039 |
        101040 |
        Google-Apps |
        Google-Chrome-Device-Management |
        Google-Drive-storage |
        Google-Vault
<ProductIDList> ::= "(<ProductID>|SKUID>)(,<ProductID>|SKUID>)*"

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
        appsheetcore | 1010380001 |
        appsheetstandard | appsheetenterprisestandard | 1010380002 |
        appsheetplus | appsheetenterpriseplus | 1010380003 |
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
<SKUIDList> ::= "<SKUID>(,<SKUID>)*"
```
## Notes
GAM maintains a table of Products and SKUs that it uses to validate `<ProductID>` and `<SKUID>`;
an error is generated for values not in the table. This could cause a problem if Google adds
additional Products or SKUs that are not in the table.

You can enter a non-validated Product as follows:
```
nv:<String>
```
You can enter a non-validated SKU as follows:
```
nv:<String>:<String>
```
The first `<String>` is a Product and the second `<String>` is a SKU.

## Display license counts
```
gam show licenses
        [(products|product <ProductIDList>)|(skus|sku <SKUIDList>)|allskus|gsuite]
        [maxresults <Integer>]
```
By default, license counts are displayed for all Google products; use these options to select which products/SKU license counts to display:
* `products|product <ProductIDList>` - Select specific products
* `skus|sku <SKUIDList>` - Select specific SKUs
* `allskus` - Select all Google product SKUs
* `gsuite` - Select Google Workspace products: Google-Apps and 101031

By default, GAM asks the API for `license_max_results` from `gam.cfg` licenses per page of results,
* `maxresults` - Maximum number of results per page; range is 100-1000; the default is 100.

## Display licenses
```
gam print licenses [todrive <ToDriveAttributes>*]
        [(products|product <ProductIDList>)|(skus|sku <SKUIDList>)|allskus|gsuite]
        [maxresults <Integer>]
        [countsonly]
```
By default, licenses are displayed for all Google products; use these options to select which products/SKU licenses to display:
* `products|product <ProductIDList>` - Select specific products
* `skus|sku <SKUIDList>` - Select specific SKUs
* `allskus` - Select all Google product SKUs
* `gsuite` - Select Google Workspace products: Google-Apps and 101031

By default, users and their licenses are displayed; use the `countsonly` option to only display total license counts.

By default, GAM asks the API for `license_max_results` from `gam.cfg` licenses per page of results,
* `maxresults` - Maximum number of results per page; range is 100-1000; the default is 100.

## Add licenses
```
gam <UserTypeEntity> add license <SKUIDList> [product|productid <ProductID>]
        [preview] [actioncsv]
```
If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `user,productId,skuId,action,message` is generated
that shows the actions performed when adding the licenses.

## Update licenses
```
gam <UserTypeEntity> update license <SKUID> [product|productid <ProductID>] [from] <SKUID>
        [preview] [actioncsv]
```
If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `user,productId,oldskuId,skuId,action,message` is generated
that shows the actions performed when updating the licenses.

## Delete licenses
```
gam <UserTypeEntity> delete|del license <SKUIDList> [product|productid <ProductID>]
         [preview] [actioncsv]
```
If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `user,productId,skuId,action,message` is generated
that shows the actions performed when deleting the licenses.

## Synchronize licenses
```
gam <UserTypeEntity> sync license <SKUIDList> [product|productid <ProductID>]
        [addonly|removeonly] [allskus|onesku] [preview] [actioncsv]
```
* GAM determines which users currently hold a license for `<SKUID>`.

Default:
* The license will be deleted for all current license holders that are not in `<UserTypeEntity>`.
* The license will be added for all users in `<UserTypeEntity>` that are not current license holders.

When the `addonly` option is specified:
* The license will not be deleted for all current license holders that are not in `<UserTypeEntity>`.
* The license will be added for all users in `<UserTypeEntity>` that are not current license holders.

When the `removeonly` option is specified:
* The license will be deleted for all current license holders that are not in `<UserTypeEntity>`.
* The license will not be added for all users in `<UserTypeEntity>` that are not current license holders.

Option `allskus|onesku` is required when multiple SKUs are specified.

* `allskus` indicates that users in `<UserTypeEntity>` will  be updated to have all of the SKUs in `<SKUIDList>`.
  * This is typically used when assigning different types of licenses, such as an Enterprise license and a Voice license.
* `onesku` indicates that users in `<UserTypeEntity>` with none of the licenses in`<SKUIDList>` will be updated to have the first available license SKU in `<SKUIDList>`.
  * This is typically used with Google Education Plus or Google Education Standard licenses, which are split across multiple SKUs.

If `preview` is specified, the changes will be previewed but not executed.

If `actioncsv` is specified, a CSV file with columns `user,productId,skuId,action,message` is generated
that shows the actions performed when adding and deleting the licenses.

### Example
Assign a Google Workspace for Education Plus license based on availability.
```
gam redirect csv ./LicenseUpdates.csv group_users all_google_eduplus_licenses@domain.edu recursive end sync licenses 1010310008,1010310010,1010310009 onesku actioncsv
```
