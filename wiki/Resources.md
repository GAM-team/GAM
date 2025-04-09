# Resources
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Region Codes](#region-codes)
- [Special quoting](#special-quoting)
- [Manage buildings](#manage-buildings)
- [Display buildings](#display-buildings)
- [Manage features](#manage-features)
- [Display features](#display-features)
- [Manage resources](#manage-resources)
- [Display resources](#display-resources)
- [Display resource counts](#display-resource-counts)
- [Manage resource calendar ACLs](#manage-resource-calendar-acls)
- [Display resource calendar ACLs](#display-resource-calendar-acls)

## API documentation
* [Use Calendar Resources](https://support.google.com/a/answer/7540850)
* [Create Buildings, Features, Calendar Resources]( https://support.google.com/a/answer/1033925)
* [Directory API - Buildings](https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.buildings)
* [Directory API - Features](https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.features)
* [Directory API - Calendar Resources](https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.calendars)
* [Postal Addresses](https://developers.google.com/my-business/reference/rest/v4/PostalAddress)

As resource calendar ids can contain spaces, some care must be used when entering `<ResourceID>` and `<ResourceEntity>`.
Suppose you have an resource calendar `Foo Bar`. To get information about it you enter the command: `gam info resource "Foo Bar"`

The shell strips the `"` leaving a single argument `Foo Bar`; gam correctly processes the argument.

Suppose you enter the command: `gam info resources "Foo Bar"`

The shell strips the `"` leaving a single argument `Foo Bar`; gam splits the argument on space leaving two items and then tries to process `Foo` and `Bar`, not what you want.

You must enter: `gam info resources "'Foo Bar'"`

The shell strips the `"` leaving a single argument `'Foo Bar'`; gam splits the argument on space while honoring the `'` leaving one item `Foo Bar` and correctly processes the item.

In general, when you're accessing a single resource calendar, use the `resource` option to minimize quoting issues.

## Definitions
See [Collections of Items](Collections-of-Items)
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>

<CalendarACLRole> ::= editor|freebusy|freebusyreader|owner|reader|writer
<CalendarACLScope> ::= <EmailAddress>|user:<EmailAdress>|group:<EmailAddress>|domain:<DomainName>)|domain|default
<CalendarACLScopeList> ::= "<CalendarACLScope>(,<CalendarACLScope>)*"
<CalendarACLScopeEntity>::= <CalendarACLScopeList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>

<BuildingID> ::= <String>|id:<String>
<FeatureName> ::= <String>
<FeatureNameList> ::= "'<FeatureName>'(,'<FeatureName>')*"
<ResourceID> ::= <String>
<ResourceIDList> ::= "<ResourceID>(,<ResourceID>)*"
<ResourceEntity> ::=
        <ResourceIDList> | <FileSelector> | <CSVkmdSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<BuildingFieldName> ::=
        address|
        buildingid|
        buildingname|
        coordinates|
        description|
        floors|
        floornames|
        id|
        name
<BuildingFieldNameList> ::= "<BuildingFieldName>(,<BuildingFieldName>)*"

<BuildingAttribute> ::=
        (address|addresslines <String>)|
        (city|locality <String>)|
        (country|regioncode <String>)|
        (description <String>)|
        (floors <FloorNameList>)|
        (id <String>)|
        (language|languageCode <Language>)|
        (latitude <Float>)|
        (longitude <Float>)|
        (name <String>)
        (state|administrativearea <String>)|
        (sublocality <String>)|
        (zipcode|postalcode <String>)

<ResourceAttribute> ::=
        (addfeatures <FeatureNameList>)|
        (buildingid <BuildingID>)|
        (capacity <Number>)|
        (category other|room|conference_room|category_unknown|unknown)|
        (description <String>)|
        (features <FeatureNameList>)|
        (floor <FloorName>)|
        (floorsection <String>)|
        (name <String>)|
        (removefeatures <FeatureNameList>)|
        (type <String>)|
        (uservisibledescription <String>)

<ResourceFieldName> ::=
        acls|
        buildingid|
        calendar|
        capacity|
        category|
        description|
        email|
        featureinstances|
        features|
        floor|
        floorsection|
        generatedresourcename|
        id|
        name|
        resourcecategory|
        resourcedescription|
        resourceemail|
        resourceid|
        resourcename|
        resourcetype|
        type|
        uservisibledescription
<ResourceFieldNameList> ::= "<ResourceFieldName>(,<ResourceFieldName>)*"
```

## Region Codes

| Region | Code |
|--------|------|
| Afghanistan | AF |
| Aland Islands | AX |
| Albania | AL |
| Algeria | DZ |
| American Samoa | AS |
| Andorra | AD |
| Angola | AO |
| Anguilla | AI |
| Antarctica | AQ |
| Antigua & Barbuda | AG |
| Argentina | AR |
| Armenia | AM |
| Aruba | AW |
| Ascension Island | AC |
| Australia | AU |
| Austria | AT |
| Azerbaijan | AZ |
| Bahamas | BS |
| Bahrain | BH |
| Bangladesh | BD |
| Barbados | BB |
| Belarus | BY |
| Belgium | BE |
| Belize | BZ |
| Benin | BJ |
| Bermuda | BM |
| Bhutan | BT |
| Bolivia | BO |
| Bosnia & Herzegovina | BA |
| Botswana | BW |
| Bouvet Island | BV |
| Brazil | BR |
| British Indian Ocean Territory | IO |
| British Virgin Islands | VG |
| Brunei | BN |
| Bulgaria | BG |
| Burkina Faso | BF |
| Burundi | BI |
| Cambodia | KH |
| Cameroon | CM |
| Canada | CA |
| Canary Islands | IC |
| Cape Verde | CV |
| Caribbean Netherlands | BQ |
| Cayman Islands | KY |
| Central African Republic | CF |
| Ceuta & Melilla | EA |
| Chad | TD |
| Chile | CL |
| China | CN |
| Christmas Island | CX |
| Clipperton Island | CP |
| Cocos (Keeling) Islands | CC |
| Columbia | CO |
| Comoros | KM |
| Congo - Brazzaville | CG |
| Congo - Kinshasa | CD |
| Cook Islands | CK |
| Costa Rica | CR |
| Cote d’Ivoire | CI |
| Croatia | HR |
| Cuba | CU |
| Curacao | CW |
| Cyprus | CY |
| Czech Republic | CZ |
| Falkland Islands | FK |
| Faroe Islands | FO |
| Fiji | FJ |
| Finland | FI |
| France | FR |
| Gabon | GA |
| Gambia | GM |
| Georgia | GE |
| Germany | DE |
| Ghana | GH |
| Gibraltar | GI |
| Greece | GR |
| Greenland | GL |
| Grenada | GD |
| Guadeloupe | GP |
| Guam | GU |
| Guatemala | GT |
| Guernsey | GG |
| Guinea | GN |
| Guinea-Bissau | GW |
| Guyana | GY |
| Haiti | HT |
| Heard & McDonald Islands | HM |
| Honduras | HN |
| Hong Kong SAR China | HK |
| Hungary | HU |
| Iceland | IS |
| India | IN |
| Indonesia | ID |
| Iran | IR |
| Iraq | IQ |
| Ireland | IE |
| Isle of Man | IM |
| Israel | IL |
| Italy | IT |
| Jamaica | JM |
| Japan | JP |
| Jersey | JE |
| Jordan | JO |
| Kazakhstan | KZ |
| Kenya | KE |
| Kiribati | KI |
| Kosovo | XK |
| Kuwait | KW |
| Kyrgyzstan | KG |
| Laos | LA |
| Latvia | LV |
| Lebanon | LB |
| Lesotho | LS |
| Liberia | LR |
| Libya | LY |
| Liechtenstein | LI |
| Lithuania | LT |
| Luxembourg | LU |
| Macau SAR China | MO |
| Macedonia | MK |
| Madagascar | MG |
| Malawi | MW |
| Malaysia | MY |
| Maldives | MV |
| Mali | ML |
| Malta | MT |
| Marshall Islands | MH |
| Martinique | MQ |
| Mauritania | MR |
| Mauritius | MU |
| Mayotte | YT |
| Mexico | MX |
| Micronesia | FM |
| Moldova | MD |
| Monaco | MC |
| Mongolia | MN |
| Montenegro | ME |
| Montserrat | MS |
| Morocco | MA |
| Mozambique | MZ |
| Myanmar | MM |
| Namibia | NA |
| Nauru | NR |
| Nepal | NP |
| Netherlands | NL |
| New Caledonia | NC |
| New Zealand | NZ |
| Nicaragua | NI |
| Niger | NE |
| Nigeria | NG |
| Niue | NU |
| Norfolk Island | NF |
| North Korea | KP |
| Northern Mariana Islands | MP |
| Norway | NO |
| Oman | OM |
| Pakistan | PK |
| Palau | PW |
| Palestinia Territories | PS |
| Panama | PA |
| Papua New Guinea | PG |
| Paraguay | PY |
| Peru | PE |
| Philippines | PH |
| Pitcairn Islands | PN |
| Poland | PL |
| Portugal | PT |
| Puerto Rico | PR |
| Qatar | QA |
| Reunion | RE |
| Romania | RO |
| Russia | RU |
| Rwanda | RW |
| Samoa | WS |
| San Marino | SM |
| Sao Tomm & Principe | ST |
| Saudi Arabia | SA |
| Senegal | SN |
| Serbia | RS |
| Seychelles | SC |
| Sierra Leone | SL |
| Singapore | SG |
| Sint Maarten | SX |
| Slovakia | SK |
| Slovenia | SI |
| Solomon Islands | SB |
| Somalia | SO |
| South Africa | ZA |
| South Georgia & South Sandwich Islands | GS |
| South Korea | KR |
| South Sudan | SS |
| Spain | ES |
| Sri Lanka | LK |
| St. Barthelemy | BL |
| St. Helena | SH |
| St. Kitts & Nevis | KN |
| St. Lucia | LC |
| St. Martin | MF |
| St. Pierre & Miquelon | PM |
| St. Vincent & Grenadines | VC |
| Sudan | SD |
| Suriname | SR |
| Svalbard & Jan Mayen | SJ |
| Swaziland | SZ |
| Sweden | SE |
| Switzerland | CH |
| Syria | SY |
| Taiwan | TW |
| Tajikistan | TJ |
| Tanzania | TZ |
| Thailand | TH |
| Timor-Leste | TL |
| Togo | TG |
| Tokelau | TK |
| Tonga | TO |
| Trinidad & Tobago | TT |
| Tristan da Cunha | TA |
| Tunisia | TN |
| Turkey | TR |
| Turkmenistan | TM |
| Turks & Caicos Islands | TC |
| Tuvalu | TV |
| U.S. Outlying Islands | UM |
| U.S. Virgin Islands | VI |
| Uganda | UG |
| Ukraine | UA |
| United Arab Emirates | AE |
| United Kingdom | GB |
| United States | US |
| Unknown Region | ZZ |
| Uraguay | UY |
| Uzbekistan | UZ |
| Vanuatu | VU |
| Vatican City | VA |
| Venezuela | VE |
| Vietnam | VN |
| Yemen | YE |
| Zambia | ZM |
| Zimbabwe | ZW |

## Special quoting
When entering `<FeatureNameList>` with `<FeatureName>s`containing spaces, enclose the list in `"` and the names containing spaces in `'`.
```
features "CameraSet"
features "'Laptop Cart'"
features "CameraSet,'Laptop Cart'"
```
## Manage buildings
When creating a building, at a minimum you must enter `address|addresslines` and `country|regioncode`.

* Enter a single-line address as `address "123 Main Street"`
* Enter a multi-line address as `addresslines "123 Main Street\nAnytown, US"`
```
gam create|add building <Name> <BuildingAttribute>*
gam update building <BuildIngID> <BuildingAttribute>*
gam delete building <BuildingID>
```
## Display buildings
```
gam info building <BuildingID>
        [formatjson]
gam show buildings
        [allfields|<BuildingFildName>*|(fields <BuildingFieldNameList>)]
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print buildings [todrive <ToDriveAttribute>*]
        [allfields|<BuildingFildName>*|(fields <BuildingFieldNameList>)]
        [delimiter <Character>] [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage features
```
gam create|add feature name <Name>
gam update feature <Name> name <Name>
gam delete feature <Name>
```
## Display features
```
gam show features
gam print features [todrive <ToDriveAttribute>*]
```
## Manage resources
These commands operate on a single resource.
```
gam create|add resource <ResourceID> <Name> <ResourceAttribute>*
gam update resource <ResourceID> <ResourceAttribute>*
gam delete resource <ResourceID>
```
These commands operate on multiple resources.
```
gam update resources <ResourceEntity> <ResourceAttribute>*
gam delete resources <ResourceEntity>
```
When updating a resource, use the following options to manage the features.
* `features <FeatureNameList>` - Replace the current set of features with a list of features
* `addfeatures <FeatureNameList>` - Add a list of features to the current set of features
* `removefeatures <FeatureNameList>` - Remove a list features from the current set of features

## Display resources
```
gam info resource <ResourceID>
        [acls] [noselfowner] [calendar]
        [formatjson]
gam info resources <ResourceEntity>
        [acls] [noselfowner] [calendar]
        [formatjson]
gam show resources
        [allfields|<ResourceFieldName>*|(fields <ResourceFieldNameList>)]
        [query <String>]
        [acls] [noselfowner] [calendar] [convertcrnl]
        [formatjson]
```
Optional data may be displayed for the resource:
* `acls` - Display the resource calendar ACLs. This adds Scope and Role values.
* `calendar` - Display the resource calendar settings

Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print resources [todrive <ToDriveAttribute>*]
        [allfields|<ResourceFieldName>*|(fields <ResourceFieldNameList>)]
        [query <String>]
        [acls] [noselfowner] [calendar] [convertcrnl]
        [formatjson [quotechar <Character>]]
```
Optional data may be displayed for the resource:
* `acls` - Display the resource calendar ACLs. This adds columns: id, role, scope.type, scope.value
* `calendar` - Display the resource calendar settings

Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

Some text fields may contain carriage returns or line feeds, displaying fields containing these characters will make processing the CSV file with a script hard; this option converts those characters to a text form.
The default value is `csv_output_convert_cr_nl` from `gam.cfg`
* `convertcrnl` - Convert carriage return to \r and line feed to \n

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Example
Print all resources and their owners.
```
gam config csv_output_row_filter "role:regex:owner" redirect csv Resource.csv print resources acls
```

## Display resource counts
Display the number of mobile devices.
```
gam print resources
        [query <String>]
        showitemcountonly
```
Example
```
$ gam print resources showitemcountonly
Getting all Resource Calendars, may take some time on a large Google Workspace Account...
Got 32 Resource Calendars: Back 50 - Video Cameras Class Set
32
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print resources showitemcountonly)
Windows PowerShell
count = & gam print resources showitemcountonly
```

## Manage resource calendar ACLs
These commands operate on a single resource calendar.
```
gam resource <ResourceID> add acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
        [sendnotifications <Boolean>]
gam resource <ResourceID> update acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
        [sendnotifications <Boolean>]
gam resource <ResourceID> delete acls|calendaracls [<CalendarACLRole>] <CalendarACLScopeEntity>
```
These commands operate on multiple resource calendars.
```
gam resources <ResourceEntity> add acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
        [sendnotifications <Boolean>]
gam resources <ResourceEntity> update acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
        [sendnotifications <Boolean>]
gam resources <ResourceEntity> delete acls|calendaracls [<CalendarACLRole>] <CalendarACLScopeEntity>
```
## Display resource calendar ACLs
```
gam resource <ResourceID> info acls|calendaracls <CalendarACLScopeEntity>
        [formatjson]
gam resources <ResourceEntity> info acls|calendaracls <CalendarACLScopeEntity>
        [formatjson]
gam resources <ResourceEntity> show acls|calendaracls
        [noselfowner]
        [formatjson]
```
Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam resources <ResourceEntity> print acls|calendaracls [todrive <ToDriveAttribute>*]
        [noselfowner] (addcsvdata <FieldName> <String>)*
        [formatjson [quotechar <Character>]]
```
Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

Add additional columns of data from the command line to the output
* `addcsvdata <FieldName> <String>`

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
