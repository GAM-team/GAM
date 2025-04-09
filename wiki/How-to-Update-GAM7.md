# Updating GAM7
Use these steps to update your version of GAM7.

- [Downloads-Installs](Downloads-Installs)
- [Linux and MacOS and Google Cloud Shell](#linux-and-mac-os-and-google-cloud-shell)
- [Windows](#windows)
- [GAM Configuration](gam.cfg)

## Linux and MacOS and Google Cloud Shell

### Download the latest version

This example assumes that GAM7 has been installed in /Users/admin/bin/gam7.
If you've installed GAM7 in another directory, substitute that value in the directions when downloading.

See: [Downloads-Installs](Downloads-Installs)

In these examples, your Google Super admin is shown as admin@domain.com; replace with the
actual email adddress.

In these examples, the user home folder is shown as /Users/admin; adjust according to your
specific situation; e.g., /home/administrator.

### Update your project with local browser to include the additional APIs that GAM7 uses.
This step may be omitted if you are updating from a recent version.
```
admin@server:/Users/admin/bin/gam7 gam update project

Enter your Google Workspace admin or GCP project manager email address authorized to manage project(s): gam-project-abc-123-xyz? admin@domain.com

Your browser has been opened to visit:

    https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&response_type=code&client_id=...

If your browser is on a different machine then press CTRL+C,
set no_browser = true in gam.cfg and re-run this command.

Authentication successful.
API: admin.googleapis.com, already enabled...
API: appsactivity.googleapis.com, already enabled...
API: calendar-json.googleapis.com, already enabled...
API: classroom.googleapis.com, already enabled...
API: contacts.googleapis.com, already enabled...
API: drive.googleapis.com, already enabled...
API: gmail.googleapis.com, already enabled...
API: groupssettings.googleapis.com, already enabled...
API: licensing.googleapis.com, already enabled...
API: plus.googleapis.com, already enabled...
API: reseller.googleapis.com, already enabled...
API: siteverification.googleapis.com, already enabled...
API: vault.googleapis.com, already enabled...
Enable 3 APIs
  API: audit.googleapis.com, Enabled (1/3)
  API: groupsmigration.googleapis.com, Enabled (2/3)
  API: sheets.googleapis.com, Enabled (3/3)

admin@server:/Users/admin/bin/gam7
```
### Update your project without local browser (Google Cloud Shell for instance) to include the additional APIs that GAM7 uses
This step may be omitted if you are updating from a recent version.
```
admin@server:/Users/admin/bin/gam7 gam config no_browser true save
admin@server:/Users/admin/bin/gam7 gam update project

Enter your Google Workspace admin or GCP project manager email address authorized to manage project(s): gam-project-abc-123-xyz? admin@domain.com

Go to the following link in a browser on other computer:

    https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&response_type=code&client_id=...

Enter verification code: abc...xyz

Authentication successful.
API: admin.googleapis.com, already enabled...
API: appsactivity.googleapis.com, already enabled...
API: calendar-json.googleapis.com, already enabled...
API: classroom.googleapis.com, already enabled...
API: contacts.googleapis.com, already enabled...
API: drive.googleapis.com, already enabled...
API: gmail.googleapis.com, already enabled...
API: groupssettings.googleapis.com, already enabled...
API: licensing.googleapis.com, already enabled...
API: plus.googleapis.com, already enabled...
API: reseller.googleapis.com, already enabled...
API: siteverification.googleapis.com, already enabled...
API: vault.googleapis.com, already enabled...
Enable 3 APIs
  API: audit.googleapis.com, Enabled (1/3)
  API: groupsmigration.googleapis.com, Enabled (2/3)
  API: sheets.googleapis.com, Enabled (3/3)

admin@server:/Users/admin/bin/ga7
```
### Update GAM7 client access

You select a list of scopes, GAM7 uses a browser to get final authorization from Google for these scopes and
writes the credentials into the file oauth2.txt.

```
admin@server:/Users/admin/bin/gam7 ./gam oauth create

[*]  0)  Calendar API (supports readonly)
[*]  1)  Chrome Browser Cloud Management API (supports readonly)
[*]  2)  Chrome Management API - AppDetails read only
[*]  3)  Chrome Management API - Telemetry read only
[*]  4)  Chrome Management API - read only
[*]  5)  Chrome Policy API (supports readonly)
[*]  6)  Chrome Printer Management API (supports readonly)
[*]  7)  Chrome Version History API
[*]  8)  Classroom API - Course Announcements (supports readonly)
[*]  9)  Classroom API - Course Topics (supports readonly)
[*] 10)  Classroom API - Course Work/Materials (supports readonly)
[*] 11)  Classroom API - Course Work/Submissions (supports readonly)
[*] 12)  Classroom API - Courses (supports readonly)
[*] 13)  Classroom API - Profile Emails
[*] 14)  Classroom API - Profile Photos
[*] 15)  Classroom API - Rosters (supports readonly)
[*] 16)  Classroom API - Student Guardians (supports readonly)
[ ] 17)  Cloud Channel API (supports readonly)
[*] 18)  Cloud Identity - Inbound SSO Settings (supports readonly)
[*] 19)  Cloud Identity Groups API (supports readonly)
[*] 20)  Cloud Identity OrgUnits API (supports readonly)
[*] 21)  Cloud Identity User Invitations API (supports readonly)
[ ] 22)  Cloud Storage API (Read Only, Vault/Takeout Download, Cloud Storage)
[ ] 23)  Cloud Storage API (Read/Write, Vault/Takeout Copy/Download, Cloud Storage)
[*] 24)  Contact Delegation API (supports readonly)
[*] 25)  Contacts API - Domain Shared Contacts and GAL
[*] 26)  Data Transfer API (supports readonly)
[*] 27)  Directory API - Chrome OS Devices (supports readonly)
[*] 28)  Directory API - Customers (supports readonly)
[*] 29)  Directory API - Domains (supports readonly)
[*] 30)  Directory API - Groups (supports readonly)
[*] 31)  Directory API - Mobile Devices Directory (supports readonly and action)
[*] 32)  Directory API - Organizational Units (supports readonly)
[*] 33)  Directory API - Resource Calendars (supports readonly)
[*] 34)  Directory API - Roles (supports readonly)
[*] 35)  Directory API - User Schemas (supports readonly)
[*] 36)  Directory API - User Security
[*] 37)  Directory API - Users (supports readonly)
[ ] 38)  Email Audit API
[*] 39)  Groups Migration API
[*] 40)  Groups Settings API
[*] 41)  License Manager API
[*] 42)  People API (supports readonly)
[*] 43)  People Directory API - read only
[ ] 44)  Pub / Sub API
[*] 45)  Reports API - Audit Reports
[*] 46)  Reports API - Usage Reports
[ ] 47)  Reseller API
[*] 48)  Site Verification API
[ ] 49)  Sites API
[*] 50)  Vault API (supports readonly)

Select an unselected scope [ ] by entering a number; yields [*]
For scopes that support readonly, enter a number and an 'r' to grant read-only access; yields [R]
For scopes that support action, enter a number and an 'a' to grant action-only access; yields [A]
Clear read-only access [R] or action-only access [A] from a scope by entering a number; yields [*]
Unselect a selected scope [*] by entering a number; yields [ ]
Select all default scopes by entering an 's'; yields [*] for default scopes, [ ] for others
Unselect all scopes by entering a 'u'; yields [ ] for all scopes
Exit without changes/authorization by entering an 'e'
Continue to authorization by entering a 'c'
  Note, if all scopes are selected, Google will probably generate an authorization error

Please enter 0-50[a|r] or s|u|e|c: c

Enter your Google Workspace admin email address? admin@domain.com

Go to the following link in a browser on this computer or on another computer:

    https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=423565144751-10lsdt2lgnsch9jmdhl35uq4617u1ifp&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2F&scope=...

If you use a browser on another computer, you will get a browser error that the site can't be reached AFTER you
click the Allow button, paste "Unable to connect" URL from other computer (only URL data up to &scope required):

Enter verification code or paste "Unable to connect" URL from other computer (only URL data up to &scope required):

The authentication flow has completed.
Client OAuth2 File: /Users/admin/GAMConfig/oauth2.txt, Created

admin@server:/Users/admin/bin/gam7 
```
### Update GAM7 service account access.
```
admin@server:/Users/admin/bin/gam7 ./gam user admin@domain.com check serviceaccount
$ gam user admin@domain.com check serviceaccount
System time status
  Your system time differs from www.googleapis.com by less than 1 second    PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 0 days                                   PASS
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 34
  https://mail.google.com/                                                  PASS (1/34)
  https://sites.google.com/feeds                                            PASS (2/34)
  https://www.googleapis.com/auth/analytics.readonly                        PASS (3/34)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/34)
  https://www.googleapis.com/auth/calendar                                  PASS (5/34)
  https://www.googleapis.com/auth/chat.delete                               PASS (6/34)
  https://www.googleapis.com/auth/chat.memberships                          PASS (7/34)
  https://www.googleapis.com/auth/chat.messages                             PASS (8/34)
  https://www.googleapis.com/auth/chat.spaces                               PASS (9/34)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (10/34)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (11/34)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (12/34)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (13/34)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (14/34)
  https://www.googleapis.com/auth/classroom.topics                          PASS (15/34)
  https://www.googleapis.com/auth/cloud-identity                            PASS (16/34)
  https://www.googleapis.com/auth/cloud-platform                            PASS (17/34)
  https://www.googleapis.com/auth/contacts                                  PASS (18/34)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (19/34)
  https://www.googleapis.com/auth/datastudio                                PASS (20/34)
  https://www.googleapis.com/auth/directory.readonly                        PASS (21/34)
  https://www.googleapis.com/auth/documents                                 PASS (22/34)
  https://www.googleapis.com/auth/drive                                     PASS (23/34)
  https://www.googleapis.com/auth/drive.activity                            PASS (24/34)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (25/34)
  https://www.googleapis.com/auth/drive.labels                              FAIL (26/34)
  https://www.googleapis.com/auth/gmail.modify                              PASS (27/34)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (28/34)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (29/34)
  https://www.googleapis.com/auth/keep                                      PASS (30/34)
  https://www.googleapis.com/auth/spreadsheets                              PASS (31/34)
  https://www.googleapis.com/auth/tasks                                     PASS (32/34)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (33/34)
  https://www.googleapis.com/auth/youtube.readonly                          PASS (34/34)
Some scopes FAILED!
To authorize them, please go to:

    https://admin.google.com/ac/owl/domainwidedelegation?clientScopeToAdd=https://mail.google.com/,https://sites.google.com/feeds,https://www.googleapis.com/auth/apps.alerts,https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/classroom.announcements,https://www.googleapis.com/auth/classroom.coursework.students,https://www.googleapis.com/auth/classroom.courseworkmaterials,https://www.googleapis.com/auth/classroom.profile.emails,https://www.googleapis.com/auth/classroom.rosters,https://www.googleapis.com/auth/classroom.topics,https://www.googleapis.com/auth/cloud-identity,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/contacts,https://www.googleapis.com/auth/contacts.other.readonly,https://www.googleapis.com/auth/datastudio,https://www.googleapis.com/auth/directory.readonly,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/drive.activity,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.settings.basic,https://www.googleapis.com/auth/gmail.settings.sharing,https://www.googleapis.com/auth/keep,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/tasks,https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/userinfo.email&clientIdToAdd=SVCACCTID&overwriteClientId=true&dn=domain.com&authuser=admin@domain.com

You will be directed to the Google Workspace admin console Security/API Controls/Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.

admin@server:/Users/admin/bin/gam7
```
The link shown in the error message should take you directly to the authorization screen.
If not, make sure that you are logged in as a domain admin, then re-enter the link.

### Verify GAM7 service account access.

Wait a moment and then perform the following command; it it still fails, wait a bit longer, it can sometimes take serveral minutes
for the authorization to complete.
```
admin@server:/Users/admin/bin/gam7 ./gam user admin@domain.com check serviceaccount
System time status:
  Your system time differs from www.googleapis.com by less than 1 second    PASS
Service Account Private Key Authentication:
  Authentication                                                            PASS
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 34
  https://mail.google.com/                                                  PASS (1/34)
  https://sites.google.com/feeds                                            PASS (2/34)
  https://www.googleapis.com/auth/analytics.readonly                        PASS (3/34)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/34)
  https://www.googleapis.com/auth/calendar                                  PASS (5/34)
  https://www.googleapis.com/auth/chat.delete                               PASS (6/34)
  https://www.googleapis.com/auth/chat.memberships                          PASS (7/34)
  https://www.googleapis.com/auth/chat.messages                             PASS (8/34)
  https://www.googleapis.com/auth/chat.spaces                               PASS (9/34)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (10/34)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (11/34)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (12/34)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (13/34)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (14/34)
  https://www.googleapis.com/auth/classroom.topics                          PASS (15/34)
  https://www.googleapis.com/auth/cloud-identity                            PASS (16/34)
  https://www.googleapis.com/auth/cloud-platform                            PASS (17/34)
  https://www.googleapis.com/auth/contacts                                  PASS (18/34)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (19/34)
  https://www.googleapis.com/auth/datastudio                                PASS (20/34)
  https://www.googleapis.com/auth/directory.readonly                        PASS (21/34)
  https://www.googleapis.com/auth/documents                                 PASS (22/34)
  https://www.googleapis.com/auth/drive                                     PASS (23/34)
  https://www.googleapis.com/auth/drive.activity                            PASS (24/34)
  https://www.googleapis.com/auth/drive.admin.labels                        PASS (25/34)
  https://www.googleapis.com/auth/drive.labels                              PASS (26/34)
  https://www.googleapis.com/auth/gmail.modify                              PASS (27/34)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (28/34)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (29/34)
  https://www.googleapis.com/auth/keep                                      PASS (30/34)
  https://www.googleapis.com/auth/spreadsheets                              PASS (31/34)
  https://www.googleapis.com/auth/tasks                                     PASS (32/34)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (33/34)
  https://www.googleapis.com/auth/youtube.readonly                          PASS (34/34)
All scopes PASSED!

Service Account Client name: SVCACCTID is fully authorized.

admin@server:/Users/admin/bin/gam7 
```

## Windows

### Download the latest version

This example assumes that GAM7 has been installed in C:\GAM7.
If you've installed GAM7 in another directory, substitute that value in the directions when downloading.

See: [Downloads-Installs](Downloads-Installs)

In these examples, your Google Super admin is shown as admin@domain.com; replace with the
actual email adddress.

This example assumes that GAM7 has been installed in C:\GAM7; if you've installed
GAM7 in another directory, substitute that value in the directions.

These steps assume Command Prompt, adjust if you're using PowerShell.

### Update your project with local browser to include the additional APIs that GAM7 uses.
This step may be omitted if you are updating from a recent version.
```
C:\GAM7>gam update project

Enter your Google Workspace admin or GCP project manager email address authorized to manage project(s) gam-project-abc-123-xyz? admin@domain.com

Your browser has been opened to visit:

    https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&response_type=code&client_id=...

Authentication successful.
API: admin.googleapis.com, already enabled...
API: appsactivity.googleapis.com, already enabled...
API: calendar-json.googleapis.com, already enabled...
API: classroom.googleapis.com, already enabled...
API: contacts.googleapis.com, already enabled...
API: drive.googleapis.com, already enabled...
API: gmail.googleapis.com, already enabled...
API: groupssettings.googleapis.com, already enabled...
API: licensing.googleapis.com, already enabled...
API: plus.googleapis.com, already enabled...
API: reseller.googleapis.com, already enabled...
API: siteverification.googleapis.com, already enabled...
API: vault.googleapis.com, already enabled...
Enable 3 APIs
  API: audit.googleapis.com, Enabled (1/3)
  API: groupsmigration.googleapis.com, Enabled (2/3)
  API: sheets.googleapis.com, Enabled (3/3)

C:\GAM7>
```
### Update your project without local browser (headless server for instance) to include the additional APIs that GAM7 uses
This step may be omitted if you are updating from a recent version.
```
C:\GAM7>gam config no_browser true save
C:\GAM7>gam update project

Enter your Google Workspace admin or GCP project manager email address authorized to manage project(s) gam-project-abc-123-xyz? admin@domain.com

Go to the following link in a browser on other computer:

    https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&response_type=code&client_id=...

Enter verification code: abc...xyz

Authentication successful.
API: admin.googleapis.com, already enabled...
API: appsactivity.googleapis.com, already enabled...
API: calendar-json.googleapis.com, already enabled...
API: classroom.googleapis.com, already enabled...
API: contacts.googleapis.com, already enabled...
API: drive.googleapis.com, already enabled...
API: gmail.googleapis.com, already enabled...
API: groupssettings.googleapis.com, already enabled...
API: licensing.googleapis.com, already enabled...
API: plus.googleapis.com, already enabled...
API: reseller.googleapis.com, already enabled...
API: siteverification.googleapis.com, already enabled...
API: vault.googleapis.com, already enabled...
Enable 3 APIs
  API: audit.googleapis.com, Enabled (1/3)
  API: groupsmigration.googleapis.com, Enabled (2/3)
  API: sheets.googleapis.com, Enabled (3/3)

C:\GAM7>
```
### Update GAM7 client access

You select a list of scopes, GAM uses a browser to get final authorization from Google for these scopes and
writes the credentials into the file oauth2.txt.

```
C:\GAM7>gam oauth create

[*]  0)  Calendar API (supports readonly)
[*]  1)  Chrome Browser Cloud Management API (supports readonly)
[*]  2)  Chrome Management API - AppDetails read only
[*]  3)  Chrome Management API - Telemetry read only
[*]  4)  Chrome Management API - read only
[*]  5)  Chrome Policy API (supports readonly)
[*]  6)  Chrome Printer Management API (supports readonly)
[*]  7)  Chrome Version History API
[*]  8)  Classroom API - Course Announcements (supports readonly)
[*]  9)  Classroom API - Course Topics (supports readonly)
[*] 10)  Classroom API - Course Work/Materials (supports readonly)
[*] 11)  Classroom API - Course Work/Submissions (supports readonly)
[*] 12)  Classroom API - Courses (supports readonly)
[*] 13)  Classroom API - Profile Emails
[*] 14)  Classroom API - Profile Photos
[*] 15)  Classroom API - Rosters (supports readonly)
[*] 16)  Classroom API - Student Guardians (supports readonly)
[ ] 17)  Cloud Channel API (supports readonly)
[*] 18)  Cloud Identity - Inbound SSO Settings (supports readonly)
[*] 19)  Cloud Identity Groups API (supports readonly)
[*] 20)  Cloud Identity OrgUnits API (supports readonly)
[*] 21)  Cloud Identity User Invitations API (supports readonly)
[ ] 22)  Cloud Storage API (Read Only, Vault/Takeout Download, Cloud Storage)
[ ] 23)  Cloud Storage API (Read/Write, Vault/Takeout Copy/Download, Cloud Storage)
[*] 24)  Contact Delegation API (supports readonly)
[*] 25)  Contacts API - Domain Shared Contacts and GAL
[*] 26)  Data Transfer API (supports readonly)
[*] 27)  Directory API - Chrome OS Devices (supports readonly)
[*] 28)  Directory API - Customers (supports readonly)
[*] 29)  Directory API - Domains (supports readonly)
[*] 30)  Directory API - Groups (supports readonly)
[*] 31)  Directory API - Mobile Devices Directory (supports readonly and action)
[*] 32)  Directory API - Organizational Units (supports readonly)
[*] 33)  Directory API - Resource Calendars (supports readonly)
[*] 34)  Directory API - Roles (supports readonly)
[*] 35)  Directory API - User Schemas (supports readonly)
[*] 36)  Directory API - User Security
[*] 37)  Directory API - Users (supports readonly)
[ ] 38)  Email Audit API
[*] 39)  Groups Migration API
[*] 40)  Groups Settings API
[*] 41)  License Manager API
[*] 42)  People API (supports readonly)
[*] 43)  People Directory API - read only
[ ] 44)  Pub / Sub API
[*] 45)  Reports API - Audit Reports
[*] 46)  Reports API - Usage Reports
[ ] 47)  Reseller API
[*] 48)  Site Verification API
[ ] 49)  Sites API
[*] 50)  Vault API (supports readonly)

Select an unselected scope [ ] by entering a number; yields [*]
For scopes that support readonly, enter a number and an 'r' to grant read-only access; yields [R]
For scopes that support action, enter a number and an 'a' to grant action-only access; yields [A]
Clear read-only access [R] or action-only access [A] from a scope by entering a number; yields [*]
Unselect a selected scope [*] by entering a number; yields [ ]
Select all default scopes by entering an 's'; yields [*] for default scopes, [ ] for others
Unselect all scopes by entering a 'u'; yields [ ] for all scopes
Exit without changes/authorization by entering an 'e'
Continue to authorization by entering a 'c'
  Note, if all scopes are selected, Google will probably generate an authorization error

Please enter 0-50[a|r] or s|u|e|c: c

Enter your Google Workspace admin email address? admin@domain.com

Go to the following link in a browser on this computer or on another computer:

    https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=423565144751-10lsdt2lgnsch9jmdhl35uq4617u1ifp&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2F&scope=...

If you use a browser on another computer, you will get a browser error that the site can't be reached AFTER you
click the Allow button, paste "Unable to connect" URL from other computer (only URL data up to &scope required):

Enter verification code or paste "Unable to connect" URL from other computer (only URL data up to &scope required):

The authentication flow has completed.
Client OAuth2 File: C:\GAMConfig\oauth2.txt, Created

C:\GAM7>
```
### Update GAM7 service account access.
```
C:\GAM7>gam user admin@domain.com check serviceaccount
System time status
  Your system time differs from www.googleapis.com by less than 1 second    PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 0 days                                   PASS
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 34
  https://mail.google.com/                                                  PASS (1/34)
  https://sites.google.com/feeds                                            PASS (2/34)
  https://www.googleapis.com/auth/analytics.readonly                        PASS (3/34)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/34)
  https://www.googleapis.com/auth/calendar                                  PASS (5/34)
  https://www.googleapis.com/auth/chat.delete                               PASS (6/34)
  https://www.googleapis.com/auth/chat.memberships                          PASS (7/34)
  https://www.googleapis.com/auth/chat.messages                             PASS (8/34)
  https://www.googleapis.com/auth/chat.spaces                               PASS (9/34)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (10/34)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (11/34)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (12/34)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (13/34)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (14/34)
  https://www.googleapis.com/auth/classroom.topics                          PASS (15/34)
  https://www.googleapis.com/auth/cloud-identity                            PASS (16/34)
  https://www.googleapis.com/auth/cloud-platform                            PASS (17/34)
  https://www.googleapis.com/auth/contacts                                  PASS (18/34)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (19/34)
  https://www.googleapis.com/auth/datastudio                                PASS (20/34)
  https://www.googleapis.com/auth/directory.readonly                        PASS (21/34)
  https://www.googleapis.com/auth/documents                                 PASS (22/34)
  https://www.googleapis.com/auth/drive                                     PASS (23/34)
  https://www.googleapis.com/auth/drive.activity                            PASS (24/34)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (25/34)
  https://www.googleapis.com/auth/drive.labels                              FAIL (26/34)
  https://www.googleapis.com/auth/gmail.modify                              PASS (27/34)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (28/34)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (29/34)
  https://www.googleapis.com/auth/keep                                      PASS (30/34)
  https://www.googleapis.com/auth/spreadsheets                              PASS (31/34)
  https://www.googleapis.com/auth/tasks                                     PASS (32/34)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (33/34)
  https://www.googleapis.com/auth/youtube.readonly                          PASS (34/34)
Some scopes FAILED!
To authorize them, please go to:

    https://admin.google.com/ac/owl/domainwidedelegation?clientScopeToAdd=https://mail.google.com/,https://sites.google.com/feeds,https://www.googleapis.com/auth/apps.alerts,https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/classroom.announcements,https://www.googleapis.com/auth/classroom.coursework.students,https://www.googleapis.com/auth/classroom.courseworkmaterials,https://www.googleapis.com/auth/classroom.profile.emails,https://www.googleapis.com/auth/classroom.rosters,https://www.googleapis.com/auth/classroom.topics,https://www.googleapis.com/auth/cloud-identity,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/contacts,https://www.googleapis.com/auth/contacts.other.readonly,https://www.googleapis.com/auth/datastudio,https://www.googleapis.com/auth/directory.readonly,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/drive.activity,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.settings.basic,https://www.googleapis.com/auth/gmail.settings.sharing,https://www.googleapis.com/auth/keep,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/tasks,https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/userinfo.email&clientIdToAdd=SVCACCTID&overwriteClientId=true&dn=domain.com&authuser=admin@domain.com

You will be directed to the Google Workspace admin console Security/API Controls/Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.

C:\GAM7>
```
The link shown in the error message should take you directly to the authorization screen.
If not, make sure that you are logged in as a domain admin, then re-enter the link.

### Verify GAM7 service account access.

Wait a moment and then perform the following command; it it still fails, wait a bit longer, it can sometimes take serveral minutes
for the authorization to complete.
```
C:\GAM7>gam user admin@domain.com check serviceaccount
System time status:
  Your system time differs from www.googleapis.com by less than 1 second    PASS
Service Account Private Key Authentication:
  Authentication                                                            PASS
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 34
  https://mail.google.com/                                                  PASS (1/34)
  https://sites.google.com/feeds                                            PASS (2/34)
  https://www.googleapis.com/auth/analytics.readonly                        PASS (3/34)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/34)
  https://www.googleapis.com/auth/calendar                                  PASS (5/34)
  https://www.googleapis.com/auth/chat.delete                               PASS (6/34)
  https://www.googleapis.com/auth/chat.memberships                          PASS (7/34)
  https://www.googleapis.com/auth/chat.messages                             PASS (8/34)
  https://www.googleapis.com/auth/chat.spaces                               PASS (9/34)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (10/34)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (11/34)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (12/34)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (13/34)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (14/34)
  https://www.googleapis.com/auth/classroom.topics                          PASS (15/34)
  https://www.googleapis.com/auth/cloud-identity                            PASS (16/34)
  https://www.googleapis.com/auth/cloud-platform                            PASS (17/34)
  https://www.googleapis.com/auth/contacts                                  PASS (18/34)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (19/34)
  https://www.googleapis.com/auth/datastudio                                PASS (20/34)
  https://www.googleapis.com/auth/directory.readonly                        PASS (21/34)
  https://www.googleapis.com/auth/documents                                 PASS (22/34)
  https://www.googleapis.com/auth/drive                                     PASS (23/34)
  https://www.googleapis.com/auth/drive.activity                            PASS (24/34)
  https://www.googleapis.com/auth/drive.admin.labels                        PASS (25/34)
  https://www.googleapis.com/auth/drive.labels                              PASS (26/34)
  https://www.googleapis.com/auth/gmail.modify                              PASS (27/34)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (28/34)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (29/34)
  https://www.googleapis.com/auth/keep                                      PASS (30/34)
  https://www.googleapis.com/auth/spreadsheets                              PASS (31/34)
  https://www.googleapis.com/auth/tasks                                     PASS (32/34)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (33/34)
  https://www.googleapis.com/auth/youtube.readonly                          PASS (34/34)
All scopes PASSED!

Service Account Client name: SVCACCTID is fully authorized.

C:\GAM7>
```
