- [OAuth Tokens](#oauth-tokens)
  - [Listing All OAuth Tokens for Users](#listing-all-oauth-tokens-for-users)
  - [Checking For A Single OAuth Token For Users](#checking-for-a-single-oauth-token-for-users)
  - [Deleting a OAuth Token for Users](#deleting-a-oauth-token-for-users)
- [Application Specific Passwords](#application-specific-passwords)
  - [Listing Application Specific Passwords For Users](#listing-application-specific-passwords-for-users)
  - [Delete Application Specific Passwords For Users](#delete-application-specific-passwords-for-users)
- [Two Step Verification Status](#two-step-verification-status)
- [Two Step Verification Backup Codes](#two-step-verification-backup-codes)
  - [List Backup Codes For Users](#list-backup-codes-for-users)
  - [Generate New Backup Codes For Users](#generate-new-backup-codes-for-users)
  - [Delete Backup Codes For Users](#delete-backup-codes-for-users)
- [Disabling 2SV for a user](#disabling-2sv-for-a-user)
- [Signing a user out](#signing-a-user-out)
- [Deprovisioning A User](#deprovisioning-a-user)

# OAuth Tokens
## Listing All OAuth Tokens for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users show tokens
```
Prints all OAuth tokens that the given users have granted access to their Google Account. OAuth tokens allow third party websites and applications to access a user's Google data.

### Example
This example shows that the admin has granted GAM access to act on the admin's behalf.
```
gam user admin@acme.com show tokens
Tokens for admin@acme.com:
 Client ID: 380063494358.apps.googleusercontent.com
 scopes:
  https://www.googleapis.com/auth/admin.reports.usage.readonly
  https://www.googleapis.com/auth/admin.reports.audit.readonly
  https://www.googleapis.com/auth/admin.directory.device.chromeos
  https://www.googleapis.com/auth/admin.directory.user
  https://apps-apis.google.com/a/feeds/compliance/audit/
  https://www.googleapis.com/auth/apps.groups.settings
  https://www.googleapis.com/auth/admin.directory.device.mobile
  https://www.googleapis.com/auth/plus.me
  https://www.googleapis.com/auth/apps.licensing
  https://www.googleapis.com/auth/calendar
  https://www.googleapis.com/auth/admin.directory.orgunit
  https://apps-apis.google.com/a/feeds/domain/
  https://www.googleapis.com/auth/userinfo.email
  https://apps-apis.google.com/a/feeds/emailsettings/2.0/
  https://www.googleapis.com/auth/admin.directory.user.security
  https://www.googleapis.com/auth/apps/reporting/audit.readonly
  https://www.googleapis.com/auth/drive.file
  https://www.googleapis.com/auth/admin.directory.group
  https://apps-apis.google.com/a/feeds/calendar/resource/
 displayText: GAM
 userKey: 105809295792492927768
```

---


## Checking For A Single OAuth Token For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users show token clientid <client id>
```
shows if the given users have the given token allowed for their account. If they have the token, GAM says the token is present. If they don't nothing is output for that user.

### Example
This example shows which domain users have the Google Apps Sync for Microsoft Outlook app allowed for their account
```
gam all users show token clientid 1095133494869.apps.googleusercontent.com
Getting all users in Google Apps account (may take some time on a large account)
...
Got 32 users
done getting 32 users.
jon@acme.com has allowed this token
mike@acme.com has allowed this token
```

---


## Deleting a OAuth Token for Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users delete token clientid <client id>
```
Revokes the authentication token for the given users. This will block the website or app from connecting to the user's account until the user re-authorizes the site/app.

### Example
This example revokes Google Apps Sync for Outlook support for all users.
```
gam all users delete token clientid 1095133494869.apps.googleusercontent.com
```

---


# Application Specific Passwords
## Listing Application Specific Passwords For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users show asps
```
Prints a list of Application Specific Passwords that the given users have created with the descriptive name the user has supplied. The actual password is not shown and cannot be retrieved.

### Example
This example shows the ASPs for Ryan
```
gam user ryan@acme.com show asps
ID: 35
  Name: Windows PC Chrome Sync
  Created: 2012-11-14 12:44:04
  Last Used: 2012-11-14 12:44:13

ID: 36
  Name: iPhone
  Created: 2013-02-14 22:10:32
  Last Used: 2013-05-28 14:40:37

ID: 40
  Name: Google Talk
  Created: 2013-05-07 13:40:49
  Last Used: 2013-05-07 13:41:27
```

---


## Delete Application Specific Passwords For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users delete asp <ID>
```
revokes the supplied application specific password ID for the given users. This will stop the password from working on whatever devices/applications it was used.

### Example
This example will revoke the ASP for Ryan's iPhone (muhahah, get an Android dude!)
```
gam user ryan@acme.com delete asp 36
```

---


# Two Step Verification Backup Codes
## List Backup Codes For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users show backupcodes
```
lists the two step verification backup codes for the given users. Some users may not have any backup codes generated in which case nothing will be printed for them.

### Example
This example prints out the backup codes for Mike.
```
gam user mike@acme.com show backupcodes
Backup verification codes for mike@acme.com

1. 93964433
2. 91867555
3. 43621384
4. 06304268
5. 96022530
6. 40678584
7. 26886356
8. 27259873
9. 13882290
10. 76700736

```

---


## Generate New Backup Codes For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users update backupcodes
```
invalidates the users current backup codes (if any) and generates 10 new backup codes for the user. Note that this process works even if the user has not turned on 2SV yet so it's possible to generate backup codes for a new user who has 2SV enrollment required. Then they'll be able to login for the first time with the backup code and should immediately turn 2SV on for their account.

### Example
This example generates and prints backup codes for Tina, a new employee.

```
gam user tina@acme.com update backupcodes
Backup verification codes for tina@acme.com

1. 04840506
2. 44120560
3. 52754730
4. 25270184
5. 43229491
6. 39659107
7. 51065328
8. 10844915
9. 81131130
10. 54044421
```

---


## Delete Backup Codes For Users
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users delete backupcodes
```
Revokes the user's current backup codes if any. The backup codes will no longer work for authenticating the user and new codes will not be generated.

### Example
This example deletes all backup codes for Charles.
```
gam user charles delete backupcodes
```

---


# Two Step Verification Status

### Syntax
```
gam print users is2svenrolled is2svenforced
```
Print all users and their respective 2-step verification status (2SV enrolled, 2SV enforced)

### Example
```
gam print users is2svenrolled is2svenforced

larry@acme.com,True,True
sally@acme.com,True,False

```
# Disabling 2SV for a user
## Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users turnoff2sv
```
Turns two-step verification off for the specified users. This is only recommended when a user is unable to complete 2nd factor authentication (and admin has verified user identity) or when admin needs to take over a user account and does not have the second factor credentials.

## Example
This example turns 2sv off for Juan's account
```
gam user juan@example.com turnoff2sv
```
----
# Signing a user out
## Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users signout
```
Signs a user out of their account by resetting their cookies. Note that how different devices and accounts react to the cookie reset will vary and is not something GAM can control. See [Google's help article](https://support.google.com/a/answer/2537800?hl=en#resetcookies) for more details.

## Example
Michele checked his email on a hotel lobby kiosk computer and thinks he forgot to sign out. This command signs him out of all locations
```
gam user michele@example.com signout
```
This example signs all students out and can be scheduled to run at 10pm each night. We'll use [CSV processing](https://github.com/jay0lee/GAM/wiki/BulkOperations#using-csv-files) to speed up the signout.
```
gam print users query "orgUnitPath=/Students" | gam csv - gam user ~primaryEmail signout
```
---

# Deprovisioning A User
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>| file <filename> | all users deprovision
```
Revokes all application specific passwords, 2SV Backup Codes and OAuth Tokens for the listed user. This process can be used at part of the deprovisioning process for terminated users. You may want to precede this command with a "gam update user (user email) password random" command to reset the user's password to an unknown value and/or follow this command with a "gam update user (user email) suspended on" to suspend the account or delegate it to a manager.

### Example
This example performs deprovisioning steps for Larry. We'll first reset his password to a random value. Then we'll kill all ASPs, backup codes and tokens and finally we'll delegate his mailbox to his manager Jim. We don't disable the account because we don't want mail to his address to bounce.
```
gam update user larry@acme.com password random
updating user larry@acme.com...

gam user larry@acme.com deprovision
Getting Application Specific Passwords for larry@acme.com
No ASPs
Invaliating 2SV Backup Codes for larry@acme.com
Getting tokens for larry@acme.com...
No Tokens
Done deprovisioning larry@acme.com

gam user larry@acme.com delegate to jim@acme.com
```

---
