# Users - Tokens
- [API documentation](#api-documentation)
- [Get Google Cloud organization ID for your workspace](#Get Google Cloud organization ID for your workspace)
- [Definitions](#definitions)
- [Delete a user's token](#delete-a-users-token)
- [Display individual user's tokens](#display-individual-users-tokens)
- [Display individual user's token counts](#display-individual-users-token-counts)
- [Display aggregated user's tokens](#display-aggregated-users-tokens)

## API documentation
* [Directory API - Tokens](https://developers.google.com/admin-sdk/directory/reference/rest/v1/tokens)

## Get Google Cloud organization ID for your workspace
This ID is used by `gam print|show token gcpdetails`; to eliminate additional API calls,
you can get the value and store it in the `gam.cfg/gcp_org_id` variable.
```
$ gam info gcporgid
organizations/906207637890
$ gam config gcp_org_id organizations/906207637890 save
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<ClientID> ::= <String>
```
## Delete a user's token
```
gam <UserTypeEntity> delete|del token|tokens clientid <ClientID>
```
## Display individual user's tokens
```
gam <UserTypeEntity> print tokens|token [todrive <ToDriveAttributes>*] [clientid <ClientID>]
        [orderby clientid|id|appname|displaytext] [delimiter <Character>]
        [gcpdetails]
gam <UserTypeEntity> show tokens|token|3lo|oauth [clientid <ClientID>]
        [orderby clientid|id|appname|displaytext]
        [gcpdetails]
gam print tokens|token [todrive <ToDriveAttributes>*] [clientid <ClientID>]
        [orderby clientid|id|appname|displaytext] [delimiter <Character>]
        [<UserTypeEntity>]
        [gcpdetails]
gam show tokens|token [clientid <ClientID>]
        [orderby clientid|id|appname|displaytext] [delimiter <Character>]
        [<UserTypeEntity>]
        [gcpdetails]
```
By default, all client tokens for a user are displayed, use `clientid <ClientID>` to display a specific client token.

For each user, select the order of token presentation:
* `orderby clientid|id` - Display each user's tokens ordered by Client ID
* `orderby appname|displaytext` - Display each user's tokens ordered by App Name

Use `gcpdetails` to get project information about the client; you get the project number
and whether it is an internal project. In order to accurately determine if a project is internal, your GAM admin user must have at least the `Browser` [IAM role for the entire GCP organization](https://docs.cloud.google.com/iam/docs/roles-permissions/browser) which allows them to lookup basic metadata about your organization projects. If your admin is not able to see all GCP projects in your organization results may not be accurate.

For `print tokens`:
* `delimiter <Character>` - Separate `scopes` entries with `<Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.

### Example
This example shows which domain users have the Google Apps Sync for Microsoft Outlook app allowed for their account
```
gam all users print token clientid 1095133494869.apps.googleusercontent.com
```

## Display individual user's token counts
```
gam <UserTypeEntity> print tokens|token [todrive <ToDriveAttributes>*] [clientid <ClientID>]
        usertokencounts
gam <UserTypeEntity> show tokens|token|3lo|oauth [clientid <ClientID>]
        usertokencounts
gam print tokens|token [todrive <ToDriveAttributes>*] [clientid <ClientID>]
        usertokencounts
        [<UserTypeEntity>]
gam show tokens|token [clientid <ClientID>]
        usertokencounts
        [<UserTypeEntity>]
```

### Example
This example shows which domain users have any access tokens.
```
gam config csv_output_row_filter "tokenCount:count>0" all users print tokens usertokencounts
```

## Display aggregated user's tokens
```
gam <UserTypeEntity> print tokens|token [todrive <ToDriveAttributes>*] [clientid <ClientID>]
        [aggregateusersby clientid|id|appname|displaytext] [delimiter <Character>]
gam <UserTypeEntity> show tokens|token|3lo|oauth [clientid <ClientID>]
        [aggregateusersby clientid|id|appname|displaytext]
gam print tokens|token [todrive <ToDriveAttributes>*] [clientid <ClientID>]
        [aggregateusersby clientid|id|appname|displaytext] [delimiter <Character>]
        [<UserTypeEntity>]
```
By default, all client tokens for aggregated users are displayed, use `clientid <ClientID>` to display a specific client token.

For aggregated users, select the order of token presentation:
* `aggregateusersby clientid|id` - Display aggregated users tokens ordered by Client ID
* `aggregateusersby appname|displaytext` - Display aggregated users tokens ordered by App Name

For `print tokens`:
* `delimiter <Character>` - Separate `scopes` entries with `<Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.

### Generate a list of all Google Apps being used by each of your users.

Serial processing
```
gam config csv_output_header_filter "^user$,clientId,displayText" redirect csv UserApps.csv [todrive <ToDriveAttributes>*] all users print tokens
```
* `config csv_output_header_filter "^user$,clientId,displayText"` - Select relevant columns
* `redirect csv UserApps.csv` - Specify CSV file
* `[todrive <ToDriveAttributes>*]` - Optional, upload CSV to Google Drive
* `all users print tokens` - Get the apps

Parallel processing
```
gam config auto_batch_min 1 num_threads 10 csv_output_header_filter "^user$,clientId,displayText" redirect csv UserApps.csv multiprocess [todrive <ToDriveAttributes>*] all users print tokens
```
* `config auto_batch_min 1 num_threads 10` - Turn on parallel processing
* `csv_output_header_filter "^user$,clientId,displayText"` - Select relevant columns
* `redirect csv UserApps.csv multiprocess` - Specify CSV file with parallel processing
* `[todrive <ToDriveAttributes>*]` - Optional, upload CSV to Google Drive
* `all users print tokens` - Get the apps

### Generate a list of all Google Apps being used by any user.
Serial processing must be used
```
gam config csv_output_header_filter "^users$,clientId,displayText" redirect csv UserApps.csv [todrive <ToDriveAttributes>*] all users print tokens aggregateusersby displaytext
```
* `config csv_output_header_filter "^users$,clientId,displayText"` - Select relevant columns
* `redirect csv UserApps.csv` - Specify CSV file
* `[todrive <ToDriveAttributes>*]` - Optional, upload CSV to Google Drive
* `all users print tokens` - Get the apps
* `aggregateusersby displaytext` - Aggregate users

### Display how many users are using Google Chrome
Serial processing must be used
```
gam config csv_output_header_filter "^users$,clientId,displayText" redirect csv UserApps.csv [todrive <ToDriveAttributes>*] all users print tokens aggregateusersby displaytext clientid 77185425430.apps.googleusercontent.com
```
* `config csv_output_header_filter "^users$,clientId,displayText"` - Select relevant columns
* `redirect csv UserApps.csv` - Specify CSV file
* `[todrive <ToDriveAttributes>*]` - Optional, upload CSV to Google Drive
* `all users print tokens` - Get the apps
* `aggregateusersby displaytext` - Aggregate users
