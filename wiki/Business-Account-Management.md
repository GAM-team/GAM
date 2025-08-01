# Users - Business Account Management
- [API documentation](#api-documentation)
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Display Business Profile Accounts](#display-business-profile-accounts)

## API documentation
* [Business Account Management](https://developers.google.com/my-business/reference/accountmanagement/rest)


## Introduction
These features were added in version 7.18.00.

To use these commands you add the 'Business Account Management API' to your project and update client authorization.
```
gam update project
gam oauth create
...
[*]  0)  Business Account Management API

```
## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Display Business Profile Accounts
```
gam <UserItem> show businessprofileaccounts
        [type locationgroup|organization|personal|usergroup]
```
Gam displays the information as an indented list of keys and values.

```
gam <UserItem> print businessprofileaccounts [todrive <ToDriveAttribute>*]
        [type locationgroup|organization|personal|usergroup]
```
Gam displays the information as columns of fields.
