# Resources
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Special quoting](#special-quoting)
- [Manage buildings](#manage-buildings)
- [Display buildings](#display-buildings)
- [Manage features](#manage-features)
- [Display features](#display-features)
- [Manage resources](#manage-resources)
- [Display resources](#display-resources)
- [Manage resource calendar ACLs](#manage-resource-calendar-acls)
- [Display resource calendar ACLs](#display-resource-calendar-acls)

## API documentation
* https://support.google.com/a/answer/1033925
* https://support.google.com/a/answer/7540850
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.calendars
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.buildings
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/resources.features
* https://developers.google.com/my-business/reference/rest/v4/PostalAddress

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
<CalendarACLScopeEntity>::= <CalendarACLScopeList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>

<BuildingID> ::= <String>|id:<String>
<FeatureName> ::= <String>
<FeatureNameList> ::= "'<FeatureName>'(,'<FeatureName>')*"
<ResourceID> ::= <String>
<ResourceIDList> ::= "<ResourceID>(,<ResourceID>)*"
<ResourceEntity> ::=
        <ResourceIDList> | <FileSelector> | <CSVkmdSelector>
        See: https://github.com/taers232c/GAMADV-XTD3/wiki/Collections-of-Items

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

For `country|regioncode` see: http://www.unicode.org/cldr/charts/30/supplemental/territory_information.html
```
gam create|add building <BuildIngID> <Name> <BuildingAttribute>*
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
gam create|add feature <Name>
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
        [acls]Documents/GoogleApps/GAM3/Docs/ [calendar]
        [formatjson]
gam info resources <ResourceEntity>
        [acls]Documents/GoogleApps/GAM3/Docs/ [calendar]
        [formatjson]
gam show resources
        [allfields|<ResourceFieldName>*|(fields <ResourceFieldNameList>)]
        [query <String>]
        [acls] [noselfowner] [calendar] [convertcrnl]
        [formatjson]
```
Optional data may be displayed for the resource:
* `acls` - Display the resource calendar ACLs
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
* `acls` - Display the resource calendar ACLs
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

## Manage resource calendar ACLs
These commands operate on a single resource calendar.
```
gam resource <ResourceID> add acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
gam resource <ResourceID> update acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
gam resource <ResourceID> delete acls|calendaracls [<CalendarACLRole>] <CalendarACLScopeEntity>
```
These commands operate on multiple resource calendars.
```
gam resources <ResourceEntity> add acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
gam resources <ResourceEntity> update acls|calendaracls <CalendarACLRole> <CalendarACLScopeEntity>
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
        [noselfowner]
        [formatjson [quotechar <Character>]]
```
Option `noselfowner` suppresses the display of ACLs that reference the calendar itself as its owner.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
