# Users - Tag Manager
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Tag Manager Accounts](#display-tag-manager-accounts)
- [Display Tag Manager Containers](#display-tag-manager-containers)
- [Display Tag Manager Workspaces](#display-tag-manager-workspaces)
- [Display Tag Manager Tags](#display-tag-manager-tags)

## API documentation
* [Tag Manager API](https://developers.google.com/tag-manager/reference/rest)

## Notes
To use these commands you must add the 'Tag Manager API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
* [`<FileSelector> | <CSVFileSelector>`](Collections-of-Items)
```
<TagManagerAccountID> ::= <String>
<TagManagerAccountPath> ::= accounts/<TagManagerAccountID>
<TagManagerAccountPathList> ::= "<TagManagerAccountPath>(,<TagManagerAccountPath>)*"
<TagManagerAccountPathEntity> ::=
        <TagManagerAccountPathList> |
        (select <FileSelector>|<CSVFileSelector>) |

<TagManagerContainerID> ::= <String>
<TagManagerContainerPath> ::= accounts/<TagManagerAccountID>/containers/<TagManagerContainerID>
<TagManagerContainerPathList> ::= "<TagManagerContainerPath>(,<TagManagerContainerPath>)*"
<TagManagerContainerPathEntity> ::=
        <TagManagerContainerPathList> |
        (select <FileSelector>|<CSVFileSelector>) |

<TagManagerWorkspaceID> ::= <String>
<TagManagerWorkspacePath> ::= accounts/<TagManagerAccountID>/containers/<TagManagerContainerID>/workspaces/<TagManagerWorkspaceID>
<TagManagerWorkspacePathList> ::= "<TagManagerWorkspacePath>(,<TagManagerWorkspacePath>)*"
<TagManagerWorkspacePathEntity> ::=
        <TagManagerWorkspacePathList> |
        (select <FileSelector>|<CSVFileSelector>) |

<TagManagerTagID> ::= <String>
<TagManagerTagPath> ::= accounts/<TagManagerAccountID>/containers/<TagManagerContainerID>/workspaces/<TagManagerWorkspaceID>/tags/<TagManagerTagID>
```
## Display Tag Manager Accounts
```
gam <UserTypeEntity> show tagmanageraccounts
        [includegoogletags [<Boolean>]]
        [formatjson]
```
By default, Gam displays the accounts as an indented list of keys and values.
* `formatjson` - Display the account in JSON format

```
gam <UserTypeEntity> print tagmanagerccounts [todrive <ToDriveAttribute>*]
        [includegoogletags [<Boolean>]]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the accounts as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Tag Manager Containers
```
gam <UserTypeEntity> show tagmanagercontainers <TagManagerAccountPathEntity>
        [formatjson]
```
By default, Gam displays the containers as an indented list of keys and values.
* `formatjson` - Display the container in JSON format

```
gam <UserTypeEntity> print tagmanagercontainers <TagManagerAccountPathEntity> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the containers as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Tag Manager Workspaces
```
gam <UserTypeEntity> show tagmanagerworkspaces <TagManagerContainerPathEntity>
        [formatjson]
```
By default, Gam displays the workspaces as an indented list of keys and values.
* `formatjson` - Display the workspace in JSON format

```
gam <UserTypeEntity> print tagmanagerworkspaces <TagManagerContainerPathEntity> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the workspaces as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display Tag Manager Tags
```
gam <UserTypeEntity> show tagmanagertags <TagManagerWorkspacePathEntity>
        [formatjson]
```
By default, Gam displays the tags as an indented list of keys and values.
* `formatjson` - Display the tag in JSON format

```
gam <UserTypeEntity> print tagmanagertags <TagManagerWorkspacePathEntity> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the tags as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
