# Users - Tag Manager
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Display Tag Manager Accounts](#display-tag-manager-accounts)
- [Display Tag Manager Containers](#display-tag-manager-containers)
- [Display Tag Manager Workspaces](#display-tag-manager-workspaces)
- [Display Tag Manager Tags](#display-tag-manager-tags)
- [Display Tag Manager User Permissions](#display-tag-manager-user-permissions)
- [Examples](#examples)

## API documentation
* [Tag Manager API](https://developers.google.com/tag-manager/reference/rest)

## Notes
To use these commands you must add the 'Tag Manager API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount

[*] 41)  Tag Manager API - Accounts, Containers, Workspaces, Tags - read only
[*] 42)  Tag Manager API - Users

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

## Display Tag Manager User Permissions
```
gam <UserTypeEntity> show tagmanagerpermissions <TagManagerAccountPathEntity>
        [formatjson]
```
By default, Gam displays the permissions as an indented list of keys and values.
* `formatjson` - Display the permission in JSON format

```
gam <UserTypeEntity> print tagmanagerpermissions <TagManagerAccountPathEntity> [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the permissions as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Examples
Single user - Get CSV data.
```
$ gam redirect csv ./tmaccounts.csv user taguser@domain.com print tagmanageraccounts 

$ gam redirect csv ./tmcontainers.csv user taguser@domain.com print tagmanagercontainers select csvfile tmaccounts.csv:path

$ gam redirect csv ./tmworkspaces.csv user taguser@domain.com print tagmanagerworkspaces select csvfile tmcontainers.csv:path

$ gam redirect csv ./tmtags.csv user taguser@domain.com print tagmanagertags select csvfile tmworkspaces.csv:path

$ gam redirect csv ./tmpermissions.csv user taguser@domain.com print tagmanagerpermissions select csvfile tmaccounts.csv:path
```

Single user - Get indented keys and values data from CSV data.
```
$ gam redirect stdout ./tmaccounts.txt user taguser@domain.com show tagmanageraccounts 

$ gam redirect stdout ./tmcontainers.txt user taguser@domain.com show tagmanagercontainers select csvfile tmaccounts.csv:path

$ gam redirect stdout ./tmworkspaces.txt user taguser@domain.com show tagmanagerworkspaces select csvfile tmcontainers.csv:path

$ gam redirect stdout ./tmtags.txt user taguser@domain.com show tagmanagertags select csvfile tmworkspaces.csv:path

$ gam redirect stdout ./tmpermissions.txt user taguser@domain.com show tagmanagerpermissions select csvfile tmaccounts.csv:path
```

Multiple  users - Get CSV data.
```
$ gam redirect csv ./tmaccounts.csv multiprocess redirect stderr - multiprocess csv Users.csv gam user "~User" print tagmanageraccounts 

$ gam redirect csv ./tmcontainers.csv multiprocess redirect stderr - multiprocess csv tmaccounts.csv gam user "~User" print tagmanagercontainers "~path"

$ gam redirect csv ./tmworkspaces.csv multiprocess redirect stderr - multiprocess csv tmcontainers.csv gam user "~User" print tagmanagerworkspaces "~path"

$ gam redirect csv ./tmtags.csv multiprocess redirect stderr - multiprocess csv tmworkspaces.csv gam user "~User" print tagmanagertags "~path"

$ gam redirect csv ./tmpermissions.csv multiprocess redirect stderr - multiprocess csv tmaccounts.csv gam user "~User" print tagmanagerpermissions "~path"
```

Multiple users - Get indented keys and values data from CSV data.
```
$ gam redirect stdout ./tmaccounts.txt multiprocess redirect stderr - multiprocess csv Users.csv gam user "~User" show tagmanageraccounts 

$ gam redirect stdout ./tmcontainers.txt multiprocess redirect stderr - multiprocess csv tmaccounts.csv gam user "~User" show tagmanagercontainers "~path"

$ gam redirect stdout ./tmworkspaces.txt multiprocess redirect stderr - multiprocess csv tmcontainers.csv gam user "~User" show tagmanagerworkspaces "~path"

$ gam redirect stdout ./tmtags.txt multiprocess redirect stderr - multiprocess csv tmworkspaces.csv gam user "~User" show tagmanagertags "~path"

$ gam redirect stdout ./tmpermissions.txt multiprocess redirect stderr - multiprocess csv tmaccounts.csv gam  user "~User" show tagmanagerpermissions "~path"

```
