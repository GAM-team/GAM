# Installation - Upgrade Legacy GAM to GAM7
Use these steps if you have used any version of GAM in your domain. They will update your GAM project
and all necessary authentications.

- [Downloads-Installs](Downloads-Installs)
- [Linux and MacOS and Google Cloud Shell](#linux-and-mac-os-and-google-cloud-shell)
- [Windows](#windows)
- [GAM Configuration](gam.cfg)

## Linux and MacOS and Google Cloud Shell

In these examples, your Google Super admin is shown as admin@domain.com; replace with the
actual email adddress.

In these examples, the user home folder is shown as /Users/admin; adjust according to your
specific situation; e.g., /home/administrator.

This example assumes that GAM7 has been installed in /Users/admin/bin/gam7.
If you've installed GAM7 in another directory, substitute that value in the directions.

### Set a configuration directory

The default GAM configuration directory is /Users/admin/.gam; for more flexibility you
probably want to select a non-hidden location. This example assumes that the GAM
configuration directory will be /Users/admin/GAMConfig; If you've chosen another directory,
substitute that value in the directions.

Make the directory:
```
admin@server:/Users/admin$ mkdir -p /Users/admin/GAMConfig
```

Add the following line:
```
export GAMCFGDIR="/Users/admin/GAMConfig"
```
to one of these files based on your shell:
```
~/.bash_profile
~/.bashrc
~/.zshrc
~/.profile
```

Issue the following command replacing `<Filename>` with the name of the file you edited:
```
admin@server:/Users/admin$ source <Filename>
```

You need to make sure the GAM configuration directory actually exists. Test that like this:
```
admin@server:/Users/admin$ ls -l $GAMCFGDIR
```

### Set a working directory

You should establish a GAM working directory; you will store your GAM related
data in this folder and execute GAM commands from this folder. You should not use
/Users/admin/bin/gam7 or /Users/admin/GAMConfig for this purpose.
This example assumes that the GAM working directory will be /Users/admin/GAMWork; If you've chosen
another directory, substitute that value in the directions.

Make the directory:
```
admin@server:/Users/admin$ mkdir -p /Users/admin/GAMWork
```

### Set an alias
You should set an alias to point to /Users/admin/bin/gam7/gam so you can operate from the /Users/admin/GAMWork directory.
Aliases aren't available in scripts, so you may want to set a symlink instead, see below.

Add the following line:
```
alias gam="/Users/admin/bin/gam7/gam"
```
to one of these files based on your shell:
```
~/.bash_aliases
~/.bash_profile
~/.bashrc
~/.zshrc
~/.profile
```

If you already have an alias for legacy GAM but are no longer going to run it, delete these lines:
```
function gam() { "/Users/admin/bin/gam/gam" "$@" ; }"
alias gam="/Users/admin/bin/gam/gam"
```

If you already have an alias for legacy GAM and want to run it and GAM7, give your old alias a different name:
```
function gamstd() { "/Users/admin/bin/gam/gam" "$@" ; }"
alias gamstd="/Users/admin/bin/gam/gam"
```

Issue the following command replacing `<Filename>` with the name of the file you edited:
```
admin@server:/Users/admin$ source <Filename>
```

### Set a symlink
Set a symlink in `/usr/local/bin` (or some other location on $PATH) to point to GAM. 
```
admin@server:/Users/admin$ ln -s "/Users/admin/bin/gam7/gam" /usr/local/bin/gam
```

Set environment variable OLDGAMPATH to point to the existing Gam directory; /Users/admin/bin/gam will be used in this example.
If your existing Gam is in another directory, substitute that value in the directions.
```
admin@server:/Users/admin$ export OLDGAMPATH=/Users/admin/bin/gam
```
Verify that OLDGAMPATH points to the correct location.
```
admin@server:/Users/admin$ ls -l $OLDGAMPATH/*.json
-rw-r-----@ 1 admin  staff   553 Feb 26 10:39 /Users/admin/bin/gam/client_secrets.json
-rw-r-----@ 1 admin  staff  2377 Feb 26 10:39 /Users/admin/bin/gam/oauth2service.json
admin@server:/Users/admin$ 
```
### Initialize GAM7; this should be the first GAM7 command executed.
```
admin@server:/Users/admin$ gam config drive_dir /Users/admin/GAMWork verify
Created: /Users/admin/GAMConfig
Created: /Users/admin/GAMConfig/gamcache
Copied: /Users/admin/bin/gam/oauth2service.json, To: /Users/admin/GAMConfig/oauth2service.json
Copied: /Users/admin/bin/gam/oauth2.txt, To: /Users/admin/GAMConfig/oauth2.txt
Copied: /Users/admin/bin/gam/client_secrets.json, To: /Users/admin/GAMConfig/client_secrets.json
Config File: /Users/admin/GAMConfig/gam.cfg, Initialized
Section: DEFAULT
  ...
  cache_dir = /Users/admin/GAMConfig/gamcache
  ...
  config_dir = /Users/admin/GAMConfig
  ...
  drive_dir = /Users/admin/GAMWork
  ...

admin@server:/Users/admin$
```
### Verify initialization, this was a successful installation.
```
admin@server:/Users/admin$ ls -l $GAMCFGDIR
total 48
-rw-r-----+ 1 admin  staff   553 Mar  3 09:23 client_secrets.json
-rw-r-----+ 1 admin  staff  1069 Mar  3 09:23 gam.cfg
drwxr-x---+ 2 admin  staff    68 Mar  3 09:23 gamcache
-rw-r-----+ 1 admin  staff    10 Mar  3 09:23 lastupdatecheck.txt
-rw-r-----+ 1 admin  staff  5104 Mar  3 09:23 oauth2.txt
-rw-rw-rw-+ 1 admin  staff     0 Mar  3 09:23 oauth2.txt.lock
-rw-r-----+ 1 admin  staff  2377 Mar  3 09:23 oauth2service.json
admin@server:/Users/admin$ 
```
If the verification looks like this, then you'll have to copy client_secrets.json and oauth2service.json manually.
```
admin@server:/Users/admin$ ls -l $GAMCFGDIR
total 40
-rw-r-----+  1 admin  admin  1427 Nov  1 11:38 gam.cfg
drwxr-x---+ 16 admin  admin   544 Nov  2 07:25 gamcache
-rw-r--r--+  1 admin  admin    10 Nov  2 15:31 lastupdatecheck.txt
-rw-rw-rw-+  1 admin  admin     0 Sep 19 17:28 oauth2.txt.lock

admin@server:/Users/admin$ cp -p $OLDGAMPATH/client_secrets.json $GAMCFGDIR/
admin@server:/Users/admin$ cp -p $OLDGAMPATH/oauth2service.json $GAMCFGDIR/
admin@server:/Users/admin$ cp -p $OLDGAMPATH/oauth2.txt $GAMCFGDIR/
admin@server:/Users/admin$ ls -l $GAMCFGDIR
total 40
-rw-r-----+ 1 admin  staff   553 Mar  3 09:23 client_secrets.json
-rw-r-----+ 1 admin  staff  1069 Mar  3 09:23 gam.cfg
drwxr-x---+ 2 admin  staff    68 Mar  3 09:23 gamcache
-rw-r-----+ 1 admin  staff    10 Mar  3 09:23 lastupdatecheck.txt
-rw-r-----+ 1 admin  staff  5104 Mar  3 09:23 oauth2.txt
-rw-rw-rw-+ 1 admin  staff     0 Mar  3 09:23 oauth2.txt.lock
-rw-r-----+ 1 admin  staff  2377 Mar  3 09:23 oauth2service.json
```
### Update your project with local browser to include the additional APIs that GAM7 uses.
```
admin@server:/Users/admin$ gam update project

Enter your Google Workspace admin or GCP project manager email address authorized to manage project(s) gam-project-abc-123-xyz? admin@domain.com

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

admin@server:/Users/admin$
```
### Update your project without local browser (Google Cloud Shell for instance) to include the additional APIs that GAM7 uses
```
admin@server:/Users/admin$ gam config no_browser true save
admin@server:/Users/admin$ gam update project

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

admin@server:/Users/admin$
```
### Enable GAM7 client access

Create oauth2.txt; it must be deleted and recreated because it is in a different format than in Legacy GAM.

You select a list of scopes, GAM uses a browser to get final authorization from Google for these scopes and
writes the credentials into the file oauth2.txt.

```
admin@server:/Users/admin$ rm -f /Users/admin/GAMConfig/oauth2.txt
admin@server:/Users/admin$ gam version
WARNING: Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, Item: oauth2_txt, Value: /Users/admin/GAMConfig/oauth2.txt, Not Found
GAM 7.06.03 - https://github.com/GAM-team/GAM - pyinstaller
GAM Team <google-apps-manager@googlegroups.com>
Python 3.13.3 64-bit final
MacOS Sequoia 15.4 x86_64
Path: /Users/admin/bin/gam7
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain: domain.com

admin@server:/Users/admin$ gam oauth create

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

admin@server:/Users/admin$
```
### Enable GAM7 service account access.
```
admin@server:/Users/admin$ gam user admin@domain.com update serviceaccount
[*]  0)  AlertCenter API
[*]  1)  Analytics API - read only
[*]  2)  Analytics Admin API - read only
[*]  3)  Calendar API (supports readonly)
[*]  4)  Chat API - Memberships (supports readonly)
[*]  5)  Chat API - Memberships Admin (supports readonly)
[*]  6)  Chat API - Messages (supports readonly)
[*]  7)  Chat API - Spaces (supports readonly)
[*]  8)  Chat API - Spaces Admin (supports readonly)
[*]  9)  Chat API - Spaces Delete
[*] 10)  Chat API - Spaces Delete Admin
[*] 11)  Classroom API - Course Announcements (supports readonly)
[*] 12)  Classroom API - Course Topics (supports readonly)
[*] 13)  Classroom API - Course Work/Materials (supports readonly)
[*] 14)  Classroom API - Course Work/Submissions (supports readonly)
[*] 15)  Classroom API - Profile Emails
[*] 16)  Classroom API - Profile Photos
[*] 17)  Classroom API - Rosters (supports readonly)
[*] 18)  Cloud Identity Devices API (supports readonly)
[*] 19)  Docs API (supports readonly)
[*] 20)  Drive API (supports readonly)
[*] 21)  Drive API - todrive
[*] 22)  Drive Activity API v2 - must pair with Drive API
[*] 23)  Drive Labels API - Admin (supports readonly)
[*] 24)  Drive Labels API - User (supports readonly)
[*] 25)  Forms API
[*] 26)  Gmail API - Basic Settings (Filters,IMAP, Language, POP, Vacation) - read/write, Sharing Settings (Delegates, Forwarding, SendAs) - read
[*] 27)  Gmail API - Full Access (Labels, Messages)
[*] 28)  Gmail API - Full Access (Labels, Messages) except delete message
[ ] 29)  Gmail API - Full Access - read only
[ ] 30)  Gmail API - Send Messages - including todrive
[*] 31)  Gmail API - Sharing Settings (Delegates, Forwarding, SendAs) - write
[*] 32)  Identity and Access Management API
[*] 33)  Keep API (supports readonly)
[*] 34)  Looker Studio API (supports readonly)
[*] 35)  Meet API (supports readonly)
[*] 36)  OAuth2 API
[*] 37)  People API (supports readonly)
[*] 38)  People API - Other Contacts - read only
[*] 39)  People Directory API - read only
[*] 40)  Sheets API (supports readonly)
[*] 41)  Sheets API - todrive
[*] 42)  Sites API
[*] 43)  Tasks API (supports readonly)
[ ] 44)  Youtube API - read only

Select an unselected scope [ ] by entering a number; yields [*]
For scopes that support readonly, enter a number and an 'r' to grant read-only access; yields [R]
For scopes that support action, enter a number and an 'a' to grant action-only access; yields [A]
Clear read-only access [R] or action-only access [A] from a scope by entering a number; yields [*]
Unselect a selected scope [*] by entering a number; yields [ ]
Select all default scopes by entering an 's'; yields [*] for default scopes, [ ] for others
Unselect all scopes by entering a 'u'; yields [ ] for all scopes
Exit without changes/authorization by entering an 'e'
Continue to authorization by entering a 'c'

Please enter 0-44[a|r] or s|u|e|c: c
System time status
  Your system time differs from admin.googleapis.com by less than 1 second  PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 1 day                                    WARN
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 38
  https://mail.google.com/                                                  PASS (1/38)
  https://sites.google.com/feeds                                            FAIL (2/38)
  https://www.googleapis.com/auth/analytics.readonly                        FAIL (3/38)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/38)
  https://www.googleapis.com/auth/calendar                                  PASS (5/38)
  https://www.googleapis.com/auth/chat.admin.delete                         FAIL (6/38)
  https://www.googleapis.com/auth/chat.admin.memberships                    FAIL (7/38)
  https://www.googleapis.com/auth/chat.admin.spaces                         FAIL (8/38)
  https://www.googleapis.com/auth/chat.delete                               FAIL (9/38)
  https://www.googleapis.com/auth/chat.memberships                          FAIL (10/38)
  https://www.googleapis.com/auth/chat.messages                             FAIL (11/38)
  https://www.googleapis.com/auth/chat.spaces                               FAIL (12/38)
  https://www.googleapis.com/auth/classroom.announcements                   FAIL (13/38)
  https://www.googleapis.com/auth/classroom.coursework.students             FAIL (14/38)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             FAIL (15/38)
  https://www.googleapis.com/auth/classroom.profile.emails                  FAIL (16/38)
  https://www.googleapis.com/auth/classroom.profile.photos                  FAIL (17/38)
  https://www.googleapis.com/auth/classroom.rosters                         FAIL (18/38)
  https://www.googleapis.com/auth/classroom.topics                          FAIL (19/38)
  https://www.googleapis.com/auth/cloud-identity                            PASS (20/38)
  https://www.googleapis.com/auth/cloud-platform                            FAIL (21/38)
  https://www.googleapis.com/auth/contacts                                  FAIL (22/38)
  https://www.googleapis.com/auth/contacts.other.readonly                   FAIL (23/38)
  https://www.googleapis.com/auth/datastudio                                FAIL (24/38)
  https://www.googleapis.com/auth/directory.readonly                        FAIL (25/38)
  https://www.googleapis.com/auth/documents                                 FAIL (26/38)
  https://www.googleapis.com/auth/drive                                     PASS (27/38)
  https://www.googleapis.com/auth/drive.activity                            PASS (28/38)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (29/38)
  https://www.googleapis.com/auth/drive.labels                              FAIL (30/38)
  https://www.googleapis.com/auth/gmail.modify                              FAIL (31/38)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (32/38)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (33/38)
  https://www.googleapis.com/auth/keep                                      FAIL (34/38)
  https://www.googleapis.com/auth/meetings.space.created                    FAIL (35/38)
  https://www.googleapis.com/auth/spreadsheets                              PASS (36/38)
  https://www.googleapis.com/auth/tasks                                     FAIL (37/38)
  https://www.googleapis.com/auth/userinfo.profile                          FAIL (38/38)
Some scopes FAILED!
To authorize them, please go to the following link in your browser:

    https://gam-shortn.appspot.com/hvtbrz

You will be directed to the Google Workspace admin console Security > API Controls > Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.

admin@server:/Users/admin$
```
The link shown in the error message should take you directly to the authorization screen.
If not, make sure that you are logged in as a domain admin, then re-enter the link.

### Verify GAM7 service account access.

Wait a moment and then perform the following command; it it still fails, wait a bit longer, it can sometimes take serveral minutes
for the authorization to complete.
```
admin@server:/Users/admin$ gam user admin@domain.com check serviceaccount

System time status
  Your system time differs from admin.googleapis.com by less than 1 second  PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 1 day                                    WARN
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 38
  https://mail.google.com/                                                  PASS (1/38)
  https://sites.google.com/feeds                                            PASS (2/38)
  https://www.googleapis.com/auth/analytics.readonly                        PASS (3/38)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/38)
  https://www.googleapis.com/auth/calendar                                  PASS (5/38)
  https://www.googleapis.com/auth/chat.admin.delete                         PASS (6/38)
  https://www.googleapis.com/auth/chat.admin.memberships                    PASS (7/38)
  https://www.googleapis.com/auth/chat.admin.spaces                         PASS (8/38)
  https://www.googleapis.com/auth/chat.delete                               PASS (9/38)
  https://www.googleapis.com/auth/chat.memberships                          PASS (10/38)
  https://www.googleapis.com/auth/chat.messages                             PASS (11/38)
  https://www.googleapis.com/auth/chat.spaces                               PASS (12/38)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (13/38)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (14/38)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (15/38)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (16/38)
  https://www.googleapis.com/auth/classroom.profile.photos                  PASS (17/38)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (18/38)
  https://www.googleapis.com/auth/classroom.topics                          PASS (19/38)
  https://www.googleapis.com/auth/cloud-identity                            PASS (20/38)
  https://www.googleapis.com/auth/cloud-platform                            PASS (21/38)
  https://www.googleapis.com/auth/contacts                                  PASS (22/38)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (23/38)
  https://www.googleapis.com/auth/datastudio                                PASS (24/38)
  https://www.googleapis.com/auth/directory.readonly                        PASS (25/38)
  https://www.googleapis.com/auth/documents                                 PASS (26/38)
  https://www.googleapis.com/auth/drive                                     PASS (27/38)
  https://www.googleapis.com/auth/drive.activity                            PASS (28/38)
  https://www.googleapis.com/auth/drive.admin.labels                        PASS (29/38)
  https://www.googleapis.com/auth/drive.labels                              PASS (30/38)
  https://www.googleapis.com/auth/gmail.modify                              PASS (31/38)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (32/38)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (33/38)
  https://www.googleapis.com/auth/keep                                      PASS (34/38)
  https://www.googleapis.com/auth/meetings.space.created                    PASS (35/38)
  https://www.googleapis.com/auth/spreadsheets                              PASS (36/38)
  https://www.googleapis.com/auth/tasks                                     PASS (37/38)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (38/38)
All scopes PASSED!
Service Account Client name: SVCACCTID is fully authorized.

admin@server:/Users/admin$
```
### Update gam.cfg with some basic values
* `customer_id` - Having this data keeps Gam from having to make extra API calls
* `domain` - This allows you to omit the domain portion of email addresses
* `timezone local` - Gam will convert all UTC times to your local timezone
```
admin@server:/Users/admin$ gam info domain
Customer ID: C01234567
Primary Domain: domain.com
Customer Creation Time: 2007-06-06T15:47:55.444Z
Primary Domain Verified: True
Default Language: en
...

admin@server:/Users/admin$ gam config customer_id C01234567 domain domain.com timezone local save verify
Config File: /Users/admin/GAMConfig/gam.cfg, Saved
Section: DEFAULT
  activity_max_results = 100
  admin_email = ''
  api_calls_rate_check = false
  api_calls_rate_limit = 100
  api_calls_tries_limit = 10
  auto_batch_min = 0
  bail_on_internal_error_tries = 2
  batch_size = 50
  cacerts_pem = ''
  cache_dir = /Users/admin/GAMConfig/gamcache
  cache_discovery_only = true
  channel_customer_id = ''
  charset = utf-8
  classroom_max_results = 0
  client_secrets_json = client_secrets.json ; /Users/admin/GAMConfig/client_secrets.json
  clock_skew_in_seconds = 10
  cmdlog = ''
  cmdlog_max_backups = 5
  cmdlog_max_kilo_bytes = 1000
  config_dir = /Users/admin/GAMConfig
  contact_max_results = 100
  csv_input_column_delimiter = ,
  csv_input_quote_char = '"'
  csv_input_row_drop_filter = ''
  csv_input_row_drop_filter_mode = anymatch
  csv_input_row_filter = ''
  csv_input_row_filter_mode = allmatch
  csv_input_row_limit = 0
  csv_output_column_delimiter = ,
  csv_output_convert_cr_nl = false
  csv_output_field_delimiter = ' '
  csv_output_header_drop_filter = ''
  csv_output_header_filter = ''
  csv_output_header_force = ''
  csv_output_line_terminator = lf
  csv_output_quote_char = '"'
  csv_output_row_drop_filter = ''
  csv_output_row_drop_filter_mode = anymatch
  csv_output_row_filter = ''
  csv_output_row_filter_mode = allmatch
  csv_output_row_limit = 0
  csv_output_subfield_delimiter = '.'
  csv_output_timestamp_column = ''
  csv_output_users_audit = false
  customer_id = C01234567
  debug_level = 0
  device_max_results = 200
  domain = domain.com
  drive_dir = /Users/admin/GAMWork
  drive_max_results = 1000
  drive_v3_native_names = true
  email_batch_size = 50
  event_max_results = 250
  extra_args = ''
  inter_batch_wait = 0
  license_max_results = 100
  license_skus = ''
  member_max_results = 200
  message_batch_size = 50
  message_max_results = 500
  never_time = Never
  no_browser = false
  no_cache = false
  no_update_check = true
  no_verify_ssl = false
  num_tbatch_threads = 2
  num_threads = 5
  oauth2_txt = oauth2.txt ; /Users/admin/GAMConfig/oauth2.txt
  oauth2service_json = oauth2service.json ; /Users/admin/GAMConfig/oauth2service.json
  people_max_results = 100
  print_agu_domains = ''
  print_cros_ous = ''
  print_cros_ous_and_children = ''
  process_wait_limit = 0
  quick_cros_move = false
  quick_info_user = False
  reseller_id = ''
  retry_api_service_not_available = false
  section = ''
  show_api_calls_retry_data = false
  show_commands = false
  show_convert_cr_nl = false
  show_counts_min = 1
  show_gettings = true
  show_gettings_got_nl = false
  show_multiprocess_info = false
  smtp_fqdn = ''
  smtp_host = ''
  smtp_password = ''
  smtp_username = ''
  timezone = local
  tls_max_version = ''
  tls_min_version = 'TLSv1_2'
  todrive_clearfilter = false
  todrive_clientaccess = false
  todrive_conversion = true
  todrive_localcopy = false
  todrive_locale = ''
  todrive_nobrowser = false
  todrive_noemail = true
  todrive_parent = root
  todrive_sheet_timeformat = ''
  todrive_sheet_timestamp = false
  todrive_timeformat = ''
  todrive_timestamp = false
  todrive_timezone = ''
  todrive_upload_nodata = true
  todrive_user = ''
  truncate_client_id = false
  update_cros_ou_with_id = false
  use_projectid_as_name = false
  user_max_results = 500
  user_service_account_access_only = false

admin@server:/Users/admin$
```

## Windows

In these examples, your Google Super admin is shown as admin@domain.com; replace with the
actual email adddress.

This example assumes that GAM7 has been installed in C:\GAM7; if you've installed
GAM7 in another directory, substitute that value in the directions.

These steps assume Command Prompt, adjust if you're using PowerShell.

### Set a configuration directory

The default GAM configuration directory is C:\Users\<UserName>\.gam; for more flexibility you
probably want to select a non user-specific location. This example assumes that the GAM
configuration directory will be C:\GAMConfig; If you've chosen another directory,
substitute that value in the directions.
* Make the C:\GAMConfig directory before proceeding.

### Set a working directory

You should extablish a GAM working directory; you will store your GAM related
data in this folder and execute GAM commands from this folder. You should not use
C:\GAM7 or C:\GAMConfig for this purpose.
This example assumes that the GAM working directory will be C:\GAMWork; If you've chosen
another directory, substitute that value in the directions.
* Make the C:\GAMWork directory before proceeding.

### Set system path and GAM configuration directory
You should set the system path to point to C:\GAM7 so you can operate from the C:\GAMWork directory.
```
Start Control Panel
Click System
Click Advanced system settings
Click Environment Variables...
Click Path under System variables
Click Edit...
If you have an existing entry referencing legacy GAM:
  Click that entry
  Click Delete
If C:\GAM7 is already on the Path, skip the next three steps
  Click New
  Enter C:\GAM7
  Click OK
Click New
Set Variable name: GAMCFGDIR
Set Variable value: C:\GAMConfig
Click OK
Click OK
Click OK
Exit Control Panel
```

At this point, you should restart Command Prompt so that it has the updated path and environment variables.

Set environment variable OLDGAMPATH to point to the existing Gam directory; C:\GAM will be used in this example.
If your existing Gam is in another directory, substitute that value in the directions.
```
C:\>set OLDGAMPATH=C:\GAM
```
### Verify that OLDGAMPATH points to the correct location.
```
C:\>dir %OLDGAMPATH%\*.json
 Volume in drive C has no label.
 Volume Serial Number is 663F-DA8B

 Directory of C:\GAM

02/26/2017  10:39 AM               553 client_secrets.json
02/12/2017  09:22 AM            10,133 cloudprint-v2.json
02/12/2017  09:22 AM             3,448 email-settings-v2.json
02/26/2017  10:39 AM             2,377 oauth2service.json
               4 File(s)         16,511 bytes
               0 Dir(s)  434,214,162,432 bytes free
```
### Initialize GAM7; this should be the first GAM7 command executed.
```
C:\>gam config drive_dir C:\GAMWork verify
Created: C:\GAMConfig
Created: C:\GAMConfig\gamcache
Copied: C:\GAM\oauth2service.json, To: C:\GAMConfig\oauth2service.json
Copied: C:\GAM\oauth2.txt, To: C:\GAMConfig\oauth2.txt
Copied: C:\GAM\client_secrets.json, To: C:\GAMConfig\client_secrets.json
Config File: C:\GAMConfig\gam.cfg, Initialized
Section: DEFAULT
  activity_max_results = 100
  admin_email = ''
  api_calls_rate_check = false
  api_calls_rate_limit = 100
  api_calls_tries_limit = 10
  auto_batch_min = 0
  bail_on_internal_error_tries = 2
  batch_size = 50
  cacerts_pem = ''
  cache_dir = C:\GAMConfig\gamcache
  cache_discovery_only = true
  channel_customer_id = ''
  charset = utf-8
  classroom_max_results = 0
  client_secrets_json = client_secrets.json ; C:\GAMConfig\client_secrets.json
  clock_skew_in_seconds = 10
  cmdlog = ''
  cmdlog_max_backups = 5
  cmdlog_max_kilo_bytes = 1000
  config_dir = C:\GAMConfig
  contact_max_results = 100
  csv_input_column_delimiter = ,
  csv_input_quote_char = '"'
  csv_input_row_drop_filter = ''
  csv_input_row_drop_filter_mode = anymatch
  csv_input_row_filter = ''
  csv_input_row_filter_mode = allmatch
  csv_input_row_limit = 0
  csv_output_column_delimiter = ,
  csv_output_convert_cr_nl = false
  csv_output_field_delimiter = ' '
  csv_output_header_drop_filter = ''
  csv_output_header_filter = ''
  csv_output_header_force = ''
  csv_output_line_terminator = lf
  csv_output_quote_char = '"'
  csv_output_row_drop_filter = ''
  csv_output_row_drop_filter_mode = anymatch
  csv_output_row_filter = ''
  csv_output_row_filter_mode = allmatch
  csv_output_row_limit = 0
  csv_output_subfield_delimiter = '.'
  csv_output_timestamp_column = ''
  csv_output_users_audit = false
  customer_id = my_customer
  debug_level = 0
  device_max_results = 200
  domain = ''
  drive_dir = C:\GAMWork
  drive_max_results = 1000
  drive_v3_native_names = true
  email_batch_size = 50
  event_max_results = 250
  extra_args = ''
  inter_batch_wait = 0
  license_max_results = 100
  license_skus = ''
  member_max_results = 200
  message_batch_size = 50
  message_max_results = 500
  never_time = Never
  no_browser = false
  no_cache = false
  no_update_check = true
  no_verify_ssl = false
  num_tbatch_threads = 2
  num_threads = 5
  oauth2_txt = oauth2.txt ; C:\GAMConfig\oauth2.txt
  oauth2service_json = oauth2service.json ; C:\GAMConfig\oauth2service.json
  people_max_results = 100
  print_agu_domains = ''
  print_cros_ous = ''
  print_cros_ous_and_children = ''
  process_wait_limit = 0
  quick_cros_move = false
  quick_info_user = False
  reseller_id = ''
  retry_api_service_not_available = false
  section = ''
  show_api_calls_retry_data = false
  show_commands = false
  show_convert_cr_nl = false
  show_counts_min = 1
  show_gettings = true
  show_gettings_got_nl = false
  show_multiprocess_info = false
  smtp_fqdn = ''
  smtp_host = ''
  smtp_password = ''
  smtp_username = ''
  timezone = utc
  tls_max_version = ''
  tls_min_version = 'TLSv1_2'
  todrive_clearfilter = false
  todrive_clientaccess = false
  todrive_conversion = true
  todrive_localcopy = false
  todrive_locale = ''
  todrive_nobrowser = false
  todrive_noemail = true
  todrive_parent = root
  todrive_sheet_timeformat = ''
  todrive_sheet_timestamp = false
  todrive_timeformat = ''
  todrive_timestamp = false
  todrive_timezone = ''
  todrive_upload_nodata = true
  todrive_user = ''
  truncate_client_id = false
  update_cros_ou_with_id = false
  use_projectid_as_name = false
  user_max_results = 500
  user_service_account_access_only = false

C:\>
```
### Verify initialization, this was a successful installation.
```
C:\>dir %GAMCFGDIR%
 Volume in drive C has no label.
 Volume Serial Number is 663F-DA8B

 Directory of C:\GAMConfig

03/03/2017  10:16 AM    <DIR>          .
03/03/2017  10:16 AM    <DIR>          ..
03/03/2017  10:15 AM               553 client_secrets.json
03/03/2017  10:15 AM             1,125 gam.cfg
03/03/2017  10:15 AM    <DIR>          gamcache
03/03/2017  10:16 AM                10 lastupdatecheck.txt
03/03/2017  10:15 AM            11,704 oauth2.txt
03/03/2017  10:15 AM                 0 oauth2.txt.lock
03/03/2017  10:15 AM             2,377 oauth2service.json
               6 File(s)         15,769 bytes
               3 Dir(s)  110,532,562,944 bytes free
C:\>
```
If the verification looks like this, then you'll have to copy client_secrets.json and oauth2service.json manually.
```
C:\>dir %GAMCFGDIR%
 Volume in drive C has no label.
 Volume Serial Number is 663F-DA8B

 Directory of C:\GAMConfig

03/03/2017  10:19 AM    <DIR>          .
03/03/2017  10:19 AM    <DIR>          ..
03/03/2017  10:15 AM             1,125 gam.cfg
03/03/2017  10:15 AM    <DIR>          gamcache
03/03/2017  10:16 AM                10 lastupdatecheck.txt
03/03/2017  10:15 AM                 0 oauth2.txt.lock
               3 File(s)          1,135 bytes
               3 Dir(s)  110,532,562,944 bytes free

C:\>copy %OLDGAMPATH%\client_secrets.json %GAMCFGDIR%
        1 file(s) copied.

C:\>copy %OLDGAMPATH%\oauth2service.json %GAMCFGDIR%
        1 file(s) copied.

C:\>dir %GAMCFGDIR%
 Volume in drive C has no label.
 Volume Serial Number is 663F-DA8B

 Directory of C:\GAMConfig

03/03/2017  10:20 AM    <DIR>          .
03/03/2017  10:20 AM    <DIR>          ..
02/26/2017  10:39 AM               553 client_secrets.json
03/03/2017  10:15 AM             1,125 gam.cfg
03/03/2017  10:15 AM    <DIR>          gamcache
03/03/2017  10:16 AM                10 lastupdatecheck.txt
03/03/2017  10:15 AM                 0 oauth2.txt.lock
02/26/2017  10:39 AM             2,377 oauth2service.json
               5 File(s)          4,065 bytes
               3 Dir(s)  110,532,538,368 bytes free
```
### Update your project with local browser to include the additional APIs that GAM7 uses.
```
C:\>gam update project

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

C:\>
```
### Update your project without local browser (headless server for instance) to include the additional APIs that GAM7 uses
```
C:\>gam config no_browser true save
C:\>gam update project

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

C:\>
```
### Enable GAM7 client access

Create oauth2.txt; it must be deleted and recreated because it is in a different format than in Legacy GAM.

You select a list of scopes, GAM uses a browser to get final authorization from Google for these scopes and
writes the credentials into the file oauth2.txt.
```
C:\>del C:\GAMConfig\oauth2.txt
C:\>gam version
WARNING: Config File: C:\GAMConfig\gam.cfg, Section: DEFAULT, Item: oauth2_txt, Value: C:\GAMConfig\oauth2.txt, Not Found
GAM 7.06.03 - https://github.com/GAM-team/GAM - pythonsource
GAM Team <google-apps-manager@googlegroups.com>
Python 3.13.3 64-bit final
Windows-10-10.0.17134 AMD64
Path: C:\GAM7
Config File: C:\GAMConfig\gam.cfg, Section: DEFAULT, customer_id: my_customer, domain: domain.com

C:\>gam oauth create

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

C:\>
```

### Enable GAM7 service account access.
```
C:\>gam user admin@domain.com update serviceaccount
[*]  0)  AlertCenter API
[*]  1)  Analytics API - read only
[*]  2)  Analytics Admin API - read only
[*]  3)  Calendar API (supports readonly)
[*]  4)  Chat API - Memberships (supports readonly)
[*]  5)  Chat API - Memberships Admin (supports readonly)
[*]  6)  Chat API - Messages (supports readonly)
[*]  7)  Chat API - Spaces (supports readonly)
[*]  8)  Chat API - Spaces Admin (supports readonly)
[*]  9)  Chat API - Spaces Delete
[*] 10)  Chat API - Spaces Delete Admin
[*] 11)  Classroom API - Course Announcements (supports readonly)
[*] 12)  Classroom API - Course Topics (supports readonly)
[*] 13)  Classroom API - Course Work/Materials (supports readonly)
[*] 14)  Classroom API - Course Work/Submissions (supports readonly)
[*] 15)  Classroom API - Profile Emails
[*] 16)  Classroom API - Profile Photos
[*] 17)  Classroom API - Rosters (supports readonly)
[*] 18)  Cloud Identity Devices API (supports readonly)
[*] 19)  Docs API (supports readonly)
[*] 20)  Drive API (supports readonly)
[*] 21)  Drive API - todrive
[*] 22)  Drive Activity API v2 - must pair with Drive API
[*] 23)  Drive Labels API - Admin (supports readonly)
[*] 24)  Drive Labels API - User (supports readonly)
[*] 25)  Forms API
[*] 26)  Gmail API - Basic Settings (Filters,IMAP, Language, POP, Vacation) - read/write, Sharing Settings (Delegates, Forwarding, SendAs) - read
[*] 27)  Gmail API - Full Access (Labels, Messages)
[*] 28)  Gmail API - Full Access (Labels, Messages) except delete message
[ ] 29)  Gmail API - Full Access - read only
[ ] 30)  Gmail API - Send Messages - including todrive
[*] 31)  Gmail API - Sharing Settings (Delegates, Forwarding, SendAs) - write
[*] 32)  Identity and Access Management API
[*] 33)  Keep API (supports readonly)
[*] 34)  Looker Studio API (supports readonly)
[*] 35)  Meet API (supports readonly)
[*] 36)  OAuth2 API
[*] 37)  People API (supports readonly)
[*] 38)  People API - Other Contacts - read only
[*] 39)  People Directory API - read only
[*] 40)  Sheets API (supports readonly)
[*] 41)  Sheets API - todrive
[*] 42)  Sites API
[*] 43)  Tasks API (supports readonly)
[ ] 44)  Youtube API - read only

Select an unselected scope [ ] by entering a number; yields [*]
For scopes that support readonly, enter a number and an 'r' to grant read-only access; yields [R]
For scopes that support action, enter a number and an 'a' to grant action-only access; yields [A]
Clear read-only access [R] or action-only access [A] from a scope by entering a number; yields [*]
Unselect a selected scope [*] by entering a number; yields [ ]
Select all default scopes by entering an 's'; yields [*] for default scopes, [ ] for others
Unselect all scopes by entering a 'u'; yields [ ] for all scopes
Exit without changes/authorization by entering an 'e'
Continue to authorization by entering a 'c'

Please enter 0-44[a|r] or s|u|e|c: c
System time status
  Your system time differs from admin.googleapis.com by less than 1 second  PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 1 day                                    WARN
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 38
  https://mail.google.com/                                                  PASS (1/38)
  https://sites.google.com/feeds                                            FAIL (2/38)
  https://www.googleapis.com/auth/analytics.readonly                        FAIL (3/38)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/38)
  https://www.googleapis.com/auth/calendar                                  PASS (5/38)
  https://www.googleapis.com/auth/chat.admin.delete                         FAIL (6/38)
  https://www.googleapis.com/auth/chat.admin.memberships                    FAIL (7/38)
  https://www.googleapis.com/auth/chat.admin.spaces                         FAIL (8/38)
  https://www.googleapis.com/auth/chat.delete                               FAIL (9/38)
  https://www.googleapis.com/auth/chat.memberships                          FAIL (10/38)
  https://www.googleapis.com/auth/chat.messages                             FAIL (11/38)
  https://www.googleapis.com/auth/chat.spaces                               FAIL (12/38)
  https://www.googleapis.com/auth/classroom.announcements                   FAIL (13/38)
  https://www.googleapis.com/auth/classroom.coursework.students             FAIL (14/38)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             FAIL (15/38)
  https://www.googleapis.com/auth/classroom.profile.emails                  FAIL (16/38)
  https://www.googleapis.com/auth/classroom.profile.photos                  FAIL (17/38)
  https://www.googleapis.com/auth/classroom.rosters                         FAIL (18/38)
  https://www.googleapis.com/auth/classroom.topics                          FAIL (19/38)
  https://www.googleapis.com/auth/cloud-identity                            PASS (20/38)
  https://www.googleapis.com/auth/cloud-platform                            FAIL (21/38)
  https://www.googleapis.com/auth/contacts                                  FAIL (22/38)
  https://www.googleapis.com/auth/contacts.other.readonly                   FAIL (23/38)
  https://www.googleapis.com/auth/datastudio                                FAIL (24/38)
  https://www.googleapis.com/auth/directory.readonly                        FAIL (25/38)
  https://www.googleapis.com/auth/documents                                 FAIL (26/38)
  https://www.googleapis.com/auth/drive                                     PASS (27/38)
  https://www.googleapis.com/auth/drive.activity                            PASS (28/38)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (29/38)
  https://www.googleapis.com/auth/drive.labels                              FAIL (30/38)
  https://www.googleapis.com/auth/gmail.modify                              FAIL (31/38)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (32/38)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (33/38)
  https://www.googleapis.com/auth/keep                                      FAIL (34/38)
  https://www.googleapis.com/auth/meetings.space.created                    FAIL (35/38)
  https://www.googleapis.com/auth/spreadsheets                              PASS (36/38)
  https://www.googleapis.com/auth/tasks                                     FAIL (37/38)
  https://www.googleapis.com/auth/userinfo.profile                          FAIL (38/38)
Some scopes FAILED!
To authorize them, please go to the following link in your browser:

    https://gam-shortn.appspot.com/hvtbrz

You will be directed to the Google Workspace admin console Security > API Controls > Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.

C:\>
```
The link shown in the error message should take you directly to the authorization screen.
If not, make sure that you are logged in as a domain admin, then re-enter the link.

### Verify GAM7 service account access.

Wait a moment and then perform the following command; it it still fails, wait a bit longer, it can sometimes take serveral minutes
for the authorization to complete.
```
C:\>gam user admin@domain.com check serviceaccount
System time status
  Your system time differs from admin.googleapis.com by less than 1 second  PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 1 day                                    WARN
Domain-wide Delegation authentication:, User: admin@domain.com, Scopes: 38
  https://mail.google.com/                                                  PASS (1/38)
  https://sites.google.com/feeds                                            PASS (2/38)
  https://www.googleapis.com/auth/analytics.readonly                        PASS (3/38)
  https://www.googleapis.com/auth/apps.alerts                               PASS (4/38)
  https://www.googleapis.com/auth/calendar                                  PASS (5/38)
  https://www.googleapis.com/auth/chat.admin.delete                         PASS (6/38)
  https://www.googleapis.com/auth/chat.admin.memberships                    PASS (7/38)
  https://www.googleapis.com/auth/chat.admin.spaces                         PASS (8/38)
  https://www.googleapis.com/auth/chat.delete                               PASS (9/38)
  https://www.googleapis.com/auth/chat.memberships                          PASS (10/38)
  https://www.googleapis.com/auth/chat.messages                             PASS (11/38)
  https://www.googleapis.com/auth/chat.spaces                               PASS (12/38)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (13/38)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (14/38)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (15/38)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (16/38)
  https://www.googleapis.com/auth/classroom.profile.photos                  PASS (17/38)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (18/38)
  https://www.googleapis.com/auth/classroom.topics                          PASS (19/38)
  https://www.googleapis.com/auth/cloud-identity                            PASS (20/38)
  https://www.googleapis.com/auth/cloud-platform                            PASS (21/38)
  https://www.googleapis.com/auth/contacts                                  PASS (22/38)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (23/38)
  https://www.googleapis.com/auth/datastudio                                PASS (24/38)
  https://www.googleapis.com/auth/directory.readonly                        PASS (25/38)
  https://www.googleapis.com/auth/documents                                 PASS (26/38)
  https://www.googleapis.com/auth/drive                                     PASS (27/38)
  https://www.googleapis.com/auth/drive.activity                            PASS (28/38)
  https://www.googleapis.com/auth/drive.admin.labels                        PASS (29/38)
  https://www.googleapis.com/auth/drive.labels                              PASS (30/38)
  https://www.googleapis.com/auth/gmail.modify                              PASS (31/38)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (32/38)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (33/38)
  https://www.googleapis.com/auth/keep                                      PASS (34/38)
  https://www.googleapis.com/auth/meetings.space.created                    PASS (35/38)
  https://www.googleapis.com/auth/spreadsheets                              PASS (36/38)
  https://www.googleapis.com/auth/tasks                                     PASS (37/38)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (38/38)
All scopes PASSED!

Service Account Client name: SVCACCTID is fully authorized.

C:\>
```
### Update gam.cfg with some basic values
* `customer_id` - Having this data keeps Gam from having to make extra API calls
* `domain` - This allows you to omit the domain portion of email addresses
* `timezone local` - Gam will convert all UTC times to your local timezone
```
C:\>gam info domain
Customer ID: C01234567
Primary Domain: domain.com
Customer Creation Time: 2007-06-06T15:47:55.444Z
Primary Domain Verified: True
Default Language: en
...

C:\>gam config customer_id C01234567 domain domain.com timezone local save verify
Config File: C:\GAMConfig\gam.cfg, Saved
Section: DEFAULT
  activity_max_results = 100
  admin_email = ''
  api_calls_rate_check = false
  api_calls_rate_limit = 100
  api_calls_tries_limit = 10
  auto_batch_min = 0
  bail_on_internal_error_tries = 2
  batch_size = 50
  cacerts_pem = ''
  cache_dir = C:\GAMConfig\gamcache
  cache_discovery_only = true
  channel_customer_id = ''
  charset = utf-8
  classroom_max_results = 0
  client_secrets_json = client_secrets.json ; C:\GAMConfig\client_secrets.json
  clock_skew_in_seconds = 10
  cmdlog = ''
  cmdlog_max_backups = 5
  cmdlog_max_kilo_bytes = 1000
  config_dir = C:\GAMConfig
  contact_max_results = 100
  csv_input_column_delimiter = ,
  csv_input_quote_char = '"'
  csv_input_row_drop_filter = ''
  csv_input_row_drop_filter_mode = anymatch
  csv_input_row_filter = ''
  csv_input_row_filter_mode = allmatch
  csv_input_row_limit = 0
  csv_output_column_delimiter = ,
  csv_output_convert_cr_nl = false
  csv_output_field_delimiter = ' '
  csv_output_header_drop_filter = ''
  csv_output_header_filter = ''
  csv_output_header_force = ''
  csv_output_line_terminator = lf
  csv_output_quote_char = '"'
  csv_output_row_drop_filter = ''
  csv_output_row_drop_filter_mode = anymatch
  csv_output_row_filter = ''
  csv_output_row_filter_mode = allmatch
  csv_output_row_limit = 0
  csv_output_subfield_delimiter = '.'
  csv_output_timestamp_column = ''
  csv_output_users_audit = false
  customer_id = C01234567
  debug_level = 0
  device_max_results = 200
  domain = domain.com
  drive_dir = C:\GAMWork
  drive_max_results = 1000
  drive_v3_native_names = true
  email_batch_size = 50
  event_max_results = 250
  extra_args = ''
  inter_batch_wait = 0
  license_max_results = 100
  license_skus = ''
  member_max_results = 200
  message_batch_size = 50
  message_max_results = 500
  never_time = Never
  no_browser = false
  no_cache = false
  no_update_check = true
  no_verify_ssl = false
  num_tbatch_threads = 2
  num_threads = 5
  oauth2_txt = oauth2.txt ; C:\GAMConfig\oauth2.txt
  oauth2service_json = oauth2service.json ; C:\GAMConfig\oauth2service.json
  output_dateformat = ''
  output_timeformat = ''
  people_max_results = 100
  print_agu_domains = ''
  print_cros_ous = ''
  print_cros_ous_and_children = ''
  process_wait_limit = 0
  quick_cros_move = false
  quick_info_user = False
  reseller_id = ''
  retry_api_service_not_available = false
  section = ''
  show_api_calls_retry_data = false
  show_commands = false
  show_convert_cr_nl = false
  show_counts_min = 1
  show_gettings = true
  show_gettings_got_nl = false
  show_multiprocess_info = false
  smtp_fqdn = ''
  smtp_host = ''
  smtp_password = ''
  smtp_username = ''
  timezone = local
  tls_max_version = ''
  tls_min_version = 'TLSv1_2'
  todrive_clearfilter = false
  todrive_clientaccess = false
  todrive_conversion = true
  todrive_localcopy = false
  todrive_locale = ''
  todrive_nobrowser = false
  todrive_noemail = true
  todrive_parent = root
  todrive_sheet_timeformat = ''
  todrive_sheet_timestamp = false
  todrive_timeformat = ''
  todrive_timestamp = false
  todrive_timezone = ''
  todrive_upload_nodata = true
  todrive_user = ''
  truncate_client_id = false
  update_cros_ou_with_id = false
  use_projectid_as_name = false
  user_max_results = 500
  user_service_account_access_only = false

C:\>
```
