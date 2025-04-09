# Users - Application Specific Passwords
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage application specific passwords](#manage-application-specific-passwords)
- [Display application specific passwords](#display-application-specific-passwords)

## API documentation
* [Directory API - ASPs](https://developers.google.com/admin-sdk/directory/reference/rest/v1/asps)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<ASPID> ::= <String>
<ASPIDList> ::= "<ASPID>(,<ASPID>)*"
```
## Manage Application Specific Passwords
```
gam <UserTypeEntity> delete asps|applicationspecificpasswords all|<ASPIDList>
```
## Display application specific passwords
```
gam <UserTypeEntity> show asps|applicationspecificpasswords
```
Gam displays the information as an indented list of keys and values.

Exit Status of 0 indicates no errors, and ASPs are sent to stdout.

Exit status of 60 indicates no errors, and that no ASPs are available for this user.
```
gam <UserTypeEntity> print asps|applicationspecificpasswords [todrive <ToDriveAttribute>*]
        [oneitemperrow]
```
Gam displays the information in CSV form.

All ASPs for a user are shown on the same row unless `oneitemperrow` is specified.
