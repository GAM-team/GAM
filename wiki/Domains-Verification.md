# Domains - Verification
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Introduction](#introduction)
- [Create site verification tokens](#create-site-verification-tokens)
- [Test site verification token](#test-site-verification-token)
- [Display site verification information](#display-site-verification-information)

## API documentation
* [Getting Sarted](https://developers.google.com/site-verification/v1/getting_started)
* [Site Verification API](https://developers.google.com/site-verification/v1)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
```
## Introduction
To use Google Apps Gmail and other Web services, your account's site ownership must be verified.

## Create site verification tokens
```
gam create verify|verification <DomainName>
```
## Test site verification token
```
gam update verify|verification <DomainName> cname|txt|text|site|file
```
## Display site verification information
```
gam info verify|verification
```
