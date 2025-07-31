# Users - Web Resources and Sites
- [API documentation](#api-documentation)
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Display Web Resources](#display-web-resources)
- [Display Web Master Sites](#display-web-master-sites)

## API documentation
* [Web Resources](https://developers.google.com/site-verification/v1/webResource/list)
* [Web Sites](https://developers.google.com/webmaster-tools/v1/sites/list)


## Introduction
These features were added in version 7.17.00.

To use these commands you add the 'Search Console API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com update serviceaccount
...
[*] 39)  Search Console  API - read only
[*] 42)  Site Verification API

```
## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Display Web Resources
```
gam <UserItem> show webresources
```
Gam displays the information as an indented list of keys and values.

```
gam <UserItem> print webresources [todrive <ToDriveAttribute>*]
```
Gam displays the information as columns of fields.

## Display Web Master Sites
```
gam <UserItem> show webmastersites
```
Gam displays the information as an indented list of keys and values.

```
gam <UserItem> print webmastersites [todrive <ToDriveAttribute>*]
```
Gam displays the information as columns of fields.
