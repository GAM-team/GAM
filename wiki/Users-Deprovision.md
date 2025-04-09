# Users - Deprovision
- [Introduction](#introduction)
- [Definitions](#definitions)
- [Deprovision a user](#deprovision-a-user)

## Introduction
Deprovisioning a user deletes the Application Specific Passwords, Backup Verification Codes and Access Tokens belonging to the user.
You can optionally disable POP and IMAP access for the user, sign them out and and turn off their 2-Step Verification.

* [Users - Application Specific Passwords](Users-Application-Specific-Passwords)
* [Users - Backup Verification Codes](Users-Backup-Verification-Codes)
* [Users - Tokens](Users-Tokens)
* [Users - Signout and Turn off 2-Step Verifification](Users-Signout-Turnoff2SV)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Deprovision a user
```
gam <UserTypeEntity> deprovision|deprov [popimap] [signout] [turnoff2sv]
```
You will get the following error message for any user that is suspended:
```
User: user@domain.com, Backup Verification Codes Not Deprovisioned: User is suspended. You must unsuspend to process backupcodes
```
