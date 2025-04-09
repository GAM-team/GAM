# Users - Looker Studio
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Looker Studio assets](#display-looker-studio-assets)
- [Manage Looker Studio permissions](#manage-looker-studio-permissions)
  - [Add Permissions](#add-permissions)
  - [Delete Permissions](#delete-permissions)
  - [Update Permissions](#update-permissions)
- [Display Looker Studio permissions](#display-looker-studio-permissions)

## API documentation
* [Looker Studio API](https://developers.google.com/looker-studio/integrate/api/reference)

## Notes
To use these commands you must add the 'Looker Studio API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
...
[*] 35)  Looker Studio API (supports readonly)
```
## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<LookerStudioAssetID> ::= <String>
<LookerStudioAssetIDList> ::= "<LookerStudioAssetID>(,<LookerStudioAssetID>)*"
<LookerStudioAssetIDEntity> ::=
        <LookerStudioAssetIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<LookerStudioPermission> ::=
        user:<EmailAddress>|
        group:<EmailAddress>|
        domain:<DomainName>|
        serviceAccount:<EmailAddress>
<LookerStudioPermissionList> ::= "<LookerStudioPermission>(,<LookerStudioPermission>)*"
<LookerStudioPermissionEntity> ::=
        <LookerStudioPermissionList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
```

Looker Studio assets have an ID that is referred to by Google as its `name`; this is the value
you will use wherever `<LookerStudioAssetID>` is required.

## Display Looker Studio assets
```
gam <UserTypeEntity> show lookerstudioassets
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity>)]
        [stripcrsfromtitle]
        [formatjson]
```
By default, all assets of type `report` not in the trash are displayed; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Display assets with the specified `assettype`
  * `title <String>` - Display assets with the specified `title`
  * `owner <Emailddress>` - Display assets with the specified `owner`
  * `includetrashed` - Display assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Display a specific list of `assetids`

The `stripcrsfromtitle` option strips nulls, carriage returns and linefeeds from asset titles.
Use this option if you discover asset titles containing these special characters; it is not common.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam <UserTypeEntity> print lookerstudioassets [todrive <ToDriveAttribute>*]
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity>)]
        [stripcrsfromtitle]
        [formatjson [quotechar <Character>]]
```
By default, all assets of type `report` not in the trash are displayed; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Display assets with the specified `assettype`
  * `title <String>` - Display assets with the specified `title`
  * `owner <Emailddress>` - Display assets with the specified `owner`
  * `includetrashed` - Display assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Display a specific list of `assetids`

The `stripcrsfromtitle` option strips nulls, carriage returns and linefeeds from asset titles.
Use this option if you discover asset titles containing these special characters; it is not common.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage Looker Studio permissions
* The owner of an asset can not have it's role changed.
* The owner of an asset can not be deleted.
* A new owner can not be added to an asset.

`<EmailAddress>` in `<LookerStudioPermission>` must be complete, GAM will not add a domain name.

A viewer can not manage permissions.
### Add permissions
```
gam <UserTypeEntity> add lookerstudiopermissions
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity)]
        (role editor|viewer <LookerStudioPermissionEntity>)+
        [nodetails]
```
By default, the permission is added to all assets of type `report` not in the trash; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Add permission to assets with the specified `assettype`
  * `title <String>` - Add permission to assets with the specified `title`
  * `owner <Emailddress>` - Add permission to assets with the specified `owner`
  * `includetrashed` - Add permission to assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Add permission to a specific list of `assetids`

By default, when a permission is added, GAM outputs details of the permission. The `nodetails` option
suppresses this output.

### Delete permissions
```
gam <UserTypeEntity> delete lookerstudiopermissions
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity)]
        (role any <LookerStudioPermissionEntity>)+
        [nodetails]
```
By default, the permission is deleted from all assets of type `report` not in the trash; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Delete permission from assets with the specified `assettype`
  * `title <String>` - Delete permission from assets with the specified `title`
  * `owner <Emailddress>` - Delete permission from assets with the specified `owner`
  * `includetrashed` - Delete permission from assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Delete permission from a specific list of `assetids`

By default, when a permission is deleted, GAM outputs details of the permission. The `nodetails` option
suppresses this output.

### Update permissions
A permission is updated by deleting the existing permission and then adding the new permission.
```
gam <UserTypeEntity> update lookerstudiopermissions
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity)]
        (role editor|viewer <LookerStudioPermissionEntity>)+
        [nodetails]
```
By default, the permission is updated in all assets of type `report` not in the trash; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Update permission in assets with the specified `assettype`
  * `title <String>` - Update permission in assets with the specified `title`
  * `owner <Emailddress>` - Update permission in assets with the specified `owner`
  * `includetrashed` - Update permission in assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Update permission in a specific list of `assetids`

By default, when a permission is updated, GAM outputs details of the permission. The `nodetails` option
suppresses this output.

## Display Looker Studio permissions

A viewer can not display permissions.
```
gam <UserTypeEntity> show lookerstudiopermissions
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity>)]
        [role editor|owner|viewer]
        [formatjson]
```
By default, permissions for all assets of type `report` not in the trash are displayed; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Display permissions for assets with the specified `assettype`
  * `title <String>` - Display permissions for assets with the specified `title`
  * `owner <Emailddress>` - Display permissions for assets with the specified `owner`
  * `includetrashed` - Display permissions for assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Display permissions for a specific list of `assetids`

The Looker Studio API defines this parameter `role editor|owner|viewer` but it doesn't seem to have any effect.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam <UserTypeEntity> print lookerstudiopermissions [todrive <ToDriveAttribute>*]
        [([assettype report|datasource|all] [title <String>]
          [owner <Emailddress>] [includetrashed]
          [orderby title [ascending|descending]]) |
         (assetids <LookerStudioAssetIDEntity>)]
        [role editor|owner|viewer]
        [formatjson [quotechar <Character>]]
```
By default, permissions for all assets of type `report` not in the trash are displayed; use the following options to select a subset of assets.
* Search
  * `assettype report|datasource|all` - Display permissions for assets with the specified `assettype`
  * `title <String>` - Display permissions for assets with the specified `title`
  * `owner <Emailddress>` - Display permissions for assets with the specified `owner`
  * `includetrashed` - Display permissions for assets in the trash
  * `orderby title [ascending|descending]` - Order of assets
* Specific
  * `assetids <LookerStudioAssetIDEntity>` - Display permissions for a specific list of `assetids`

The Looker Studio API defines this parameter `role editor|owner|viewer` but it doesn't seem to have any effect.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
