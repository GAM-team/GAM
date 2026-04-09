# Users - Business Account Management
- [API documentation](#api-documentation)
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Display Business Profile Accounts](#display-business-profile-accounts)

## API documentation
* [Business Account Management](https://developers.google.com/my-business/reference/accountmanagement/rest)


## Introduction
To use these commands you must add the 'Business Account Management API' to your project and update
service account authorization.
```
gam update project
gam user user@domain.com update serviceccount
...
[*]  2)  Business Account Management API

```
## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Display Business Profile Accounts
```
gam <UserTypeEntity> show businessprofileaccounts
        [type locationgroup|organization|personal|usergroup]
```
Gam displays the information as an indented list of keys and values.

```
gam <UserTypeEntity> print businessprofileaccounts [todrive <ToDriveAttribute>*]
        [type locationgroup|organization|personal|usergroup]
```
Gam displays the information as columns of fields.
