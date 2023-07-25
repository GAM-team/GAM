# Installation - Upgrading from a prior version of GAMADV-X or GAMADV-XTD
Use these steps if you have used any version of GAMADV-X or GAMADV-XTD in your domain.
They will update your GAM project and all necessary authentications.

- [Downloads](Downloads)
- [GAM Configuration](gam.cfg)
- [Linux and MacOS and Google Cloud Shell](#linux-and-mac-os-and-google-cloud-shell)
- [Windows](#windows)

## Linux and MacOS and Google Cloud Shell

In these examples, your Google Super admin is shown as admin@domain.com; replace with the
actual email adddress.

In these examples, the user home folder is shown as /Users/admin; adjust according to your
specific situation; e.g., /home/administrator.

This example assumes that GAMADV-XTD3 has been installed in /Users/admin/bin/gamadv-xtd3.
If you've installed GAMADV-XTD3 in another directory, substitute that value in the directions.

GAMADV-XTD3 uses the same configuration directory and gam.cfg file as GAMADV-X and GAMADV-XTD.

### Update your alias
You should update your alias to point to /Users/admin/bin/gamadv-xtd3/gam.

Add the following line:
```
alias gam="/Users/admin/bin/gamadv-xtd3/gam"
```
to one of these files if you're running bash or an equivalent file if you're running some other shell:
```
~/.bash_aliases
~/.bash_profile
~/.bashrc
```

If you already have a gam alias for standard GAM and want to run it and GAMADV-XTD3, give your new alias a different name:
```
alias gam3="/Users/admin/bin/gamadv-xtd3/gam"
```
### Do you have a browser?
If your computer doesn't support a browser, Google Cloud Shell for instance, execute this command:
```
admin@server:/Users/admin/bin/gamadv-xtd3$ gam config no_browser true save
```
### Update your project to include the additional APIs that GAMADV-XTD3 uses.
```
admin@server:/Users/admin/bin/gamadv-xtd3$ gam update project

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

admin@server:/Users/admin/bin/gamadv-xtd3$
```
### Update GAMADV-XTD3 client access.

Update oauth2.txt; it must be updated to reflect the additional capabilites of GAMADV-XTD3.

You select a list of scopes, GAM uses a browser to get final authorization from Google for these scopes and
writes the credentials into the file oauth2.txt.

If the computer on which you are running GAM does not have access to a browser, issue this command:
```
gam config no_browser true oauth update
```
You will be given instructions on how to get the authorization on another computer and apply it locally.
```
admin@server:/Users/admin/bin/gamadv-xtd3$ ./gam oauth update

Select the authorized scopes by entering a number.
Append an 'r' to grant read-only access or an 'a' to grant action-only access.

[*]  0)  Calendar API (supports readonly)
[*]  1)  Chrome Browser Cloud Management API (supports readonly)
[*]  2)  Chrome Management API - Telemetry read only
[*]  3)  Chrome Management API - read only
[*]  4)  Chrome Policy API (supports readonly)
[*]  5)  Chrome Printer Management API (supports readonly)
[*]  6)  Chrome Version History API
[*]  7)  Classroom API - Course Announcements (supports readonly)
[*]  8)  Classroom API - Course Topics (supports readonly)
[*]  9)  Classroom API - Course Work/Materials (supports readonly)
[*] 10)  Classroom API - Course Work/Submissions (supports readonly)
[*] 11)  Classroom API - Courses (supports readonly)
[*] 12)  Classroom API - Profile Emails
[*] 13)  Classroom API - Profile Photos
[*] 14)  Classroom API - Rosters (supports readonly)
[*] 15)  Classroom API - Student Guardians (supports readonly)
[*] 16)  Cloud Identity Groups API (supports readonly)
[*] 17)  Cloud Storage (Vault Export - read only)
[*] 18)  Contact Delegation API (supports readonly)
[*] 19)  Contacts API - Domain Shared and Users and GAL
[*] 20)  Data Transfer API (supports readonly)
[*] 21)  Directory API - Chrome OS Devices (supports readonly)
[*] 22)  Directory API - Customers (supports readonly)
[*] 23)  Directory API - Domains (supports readonly)
[*] 24)  Directory API - Groups (supports readonly)
[*] 25)  Directory API - Mobile Devices Directory (supports readonly and action)
[*] 26)  Directory API - Organizational Units (supports readonly)
[*] 27)  Directory API - Resource Calendars (supports readonly)
[*] 28)  Directory API - Roles (supports readonly)
[*] 29)  Directory API - User Schemas (supports readonly)
[*] 30)  Directory API - User Security
[*] 31)  Directory API - Users (supports readonly)
[*] 32)  Email Audit API
[*] 33)  Groups Migration API
[*] 34)  Groups Settings API
[*] 35)  License Manager API
[*] 36)  People API (supports readonly)
[*] 37)  People Directory API - read only
[ ] 38)  Pub / Sub API
[*] 39)  Reports API - Audit Reports
[*] 40)  Reports API - Usage Reports
[ ] 41)  Reseller API
[*] 42)  Site Verification API
[*] 43)  Sites API
[*] 44)  Vault API (supports readonly)

     s)  Select all scopes
     u)  Unselect all scopes
     e)  Exit without changes
     c)  Continue to authorization
Please enter 0-44[a|r] or s|u|e|c: c

Enter your Google Workspace admin email address?admin@domain.com

Your browser has been opened to visit:

    https://accounts.google.com/o/oauth2/v2/auth?client_id=CLIENTID&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&scope=email+profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.courses+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.announcements+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.coursework.students+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.guardianlinks.students+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.profile.emails+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.profile.photos+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.rosters+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloudprint+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdevstorage.read_only+https%3A%2F%2Fwww.google.com%2Fm8%2Ffeeds+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.datatransfer+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.device.chromeos+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.customer+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.domain+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.group+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.device.mobile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.orgunit+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.resource.calendar+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.rolemanagement+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.userschema+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.user.security+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.user+https%3A%2F%2Fapps-apis.google.com%2Fa%2Ffeeds%2Fcompliance%2Faudit%2F+https%3A%2F%2Fapps-apis.google.com%2Fa%2Ffeeds%2Femailsettings%2F2.0%2F+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.groups.migration+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.groups.settings+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.licensing+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcontacts+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.reports.audit.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.reports.usage.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.order+https%3A%2F%2Fsites.google.com%2Ffeeds+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fediscovery&login_hint=admin%40domain.com&access_type=offline&response_type=code

If your browser is on a different machine then press CTRL+C,
set no_browser = true in gam.cfg and re-run this command.

Authentication successful.
Client OAuth2 File: /Users/admin/GAMConfig/oauth2.txt, Updated

admin@server:/Users/admin/bin/gamadv-xtd3$
```
### Update GAMADV-XTD3 service account access.
```
admin@server:/Users/admin/bin/gamadv-xtd3$ ./gam user user@domain.com check serviceaccount
System time status:
  Your system time differs by less than 1 second from Google                PASS
Service Account Private Key Authentication:
  Authentication                                                            PASS
Domain-Wide Delegation authentication:, User: user@domain.com, Scopes: 28
  https://mail.google.com/                                                  PASS (1/28)
  https://sites.google.com/feeds                                            PASS (2/28)
  https://www.googleapis.com/auth/apps.alerts                               PASS (3/28)
  https://www.googleapis.com/auth/calendar                                  PASS (4/28)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (5/28)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (6/28)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (7/28)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (8/28)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (9/28)
  https://www.googleapis.com/auth/classroom.topics                          PASS (10/28)
  https://www.googleapis.com/auth/cloud-identity                            PASS (11/28)
  https://www.googleapis.com/auth/cloud-platform                            PASS (12/28)
  https://www.googleapis.com/auth/contacts                                  PASS (13/28)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (14/28)
  https://www.googleapis.com/auth/datastudio                                PASS (15/28)
  https://www.googleapis.com/auth/directory.readonly                        PASS (16/28)
  https://www.googleapis.com/auth/documents                                 PASS (17/28)
  https://www.googleapis.com/auth/drive                                     PASS (18/28)
  https://www.googleapis.com/auth/drive.activity                            PASS (19/28)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (20/28)
  https://www.googleapis.com/auth/drive.labels                              FAIL (21/28)
  https://www.googleapis.com/auth/gmail.modify                              PASS (22/28)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (23/28)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (24/28)
  https://www.googleapis.com/auth/keep                                      PASS (25/28)
  https://www.googleapis.com/auth/spreadsheets                              PASS (26/28)
  https://www.googleapis.com/auth/tasks                                     PASS (27/28)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (28/28)
Some scopes FAILED! Please go to:

https://admin.google.com/domain.com/ManageOauthClients?clientScopeToAdd=https://mail.google.com/,https://sites.google.com/feeds,https://www.google.com/m8/feeds,https://www.googleapis.com/auth/activity,https://www.googleapis.com/auth/apps.alerts,https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/classroom.announcements,https://www.googleapis.com/auth/classroom.coursework.students,https://www.googleapis.com/auth/classroom.rosters,https://www.googleapis.com/auth/classroom.topics,https://www.googleapis.com/auth/cloudprint,https://www.googleapis.com/auth/contacts,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/drive.activity,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.settings.basic,https://www.googleapis.com/auth/gmail.settings.sharing,https://www.googleapis.com/auth/iam,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/userinfo.email&clientNameToAdd=SVCACCTID

You will be directed to the Google Workspace admin console. The Client Name and API
Scopes fields will be pre-populated. Please click Authorize to allow these
scopes access. After authorizing it may take some time for this test to pass so
wait a few moments and then try this command again.

admin@server:/Users/admin/bin/gamadv-xtd3$
```
The link shown in the error message should take you directly to the authorization screen.
If not, make sure that you are logged in as a domain admin, then re-enter the link.

### Verify GAMADV-XTD3 service account access.

Wait a moment and then perform the following command; it it still fails, wait a bit longer, it can sometimes take serveral minutes
for the authorization to complete.
```
admin@server:/Users/admin/bin/gamadv-xtd3$ ./gam user user@domain.com check serviceaccount
System time status:
  Your system time differs by less than 1 second from Google                PASS
Service Account Private Key Authentication:
  Authentication                                                            PASS
Domain-Wide Delegation authentication:, User: user@domain.com, Scopes: 28
  https://mail.google.com/                                                  PASS (1/28)
  https://sites.google.com/feeds                                            PASS (2/28)
  https://www.googleapis.com/auth/apps.alerts                               PASS (3/28)
  https://www.googleapis.com/auth/calendar                                  PASS (4/28)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (5/28)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (6/28)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (7/28)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (8/28)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (9/28)
  https://www.googleapis.com/auth/classroom.topics                          PASS (10/28)
  https://www.googleapis.com/auth/cloud-identity                            PASS (11/28)
  https://www.googleapis.com/auth/cloud-platform                            PASS (12/28)
  https://www.googleapis.com/auth/contacts                                  PASS (13/28)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (14/28)
  https://www.googleapis.com/auth/datastudio                                PASS (15/28)
  https://www.googleapis.com/auth/directory.readonly                        PASS (16/28)
  https://www.googleapis.com/auth/documents                                 PASS (17/28)
  https://www.googleapis.com/auth/drive                                     PASS (18/28)
  https://www.googleapis.com/auth/drive.activity                            PASS (19/28)
  https://www.googleapis.com/auth/drive.admin.labels                        PASS (20/28)
  https://www.googleapis.com/auth/drive.labels                              PASS (21/28)
  https://www.googleapis.com/auth/gmail.modify                              PASS (22/28)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (23/28)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (24/28)
  https://www.googleapis.com/auth/keep                                      PASS (25/28)
  https://www.googleapis.com/auth/spreadsheets                              PASS (26/28)
  https://www.googleapis.com/auth/tasks                                     PASS (27/28)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (28/28)
All scopes PASSED!
Service Account Client name: SVCACCTID is fully authorized.

admin@server:/Users/admin/bin/gamadv-xtd3$
```

## Windows

In these examples, your Google Super admin is shown as admin@domain.com; replace with the
actual email adddress.

This example assumes that GAMADV-XTD3 has been installed in C:\GAMADV-XTD3; if you've installed
GAMADV-XTD3 in another directory, substitute that value in the directions.

GAMADV-XTD3 uses the same configuration directory and gam.cfg file as GAMADV-X and GAMADV-XTD.

### Update system path
You should update the system path to point to C:\GAMADV-XTD3.
```
Start Control Panel
Click System
Click Advanced system settings
Click Environment Variables...
Click Path under System variables
Click Edit...
If you have an existing entry referencing GAMADV-X or GAMADV-XTD:
  Click that entry
  Click Delete
If C:\GAMADV-XTD3 is already on the Path, skip the next three steps
  Click New
  Enter C:\GAMADV-XTD3
  Click OK
Click OK
Click OK
Exit Control Panel
```

### Do you have a compatible browser?
If the computer on which you are running GAM does not have access to a browser or
your default browser is Internet Explorer or Edge, issue this command:
```
C:\GAMADV-X>gam config no_browser true save
```
### Update your project to include the additional APIs that GAMADV-XTD3 uses.
```
C:\GAMADV-XTD3>gam update project

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

C:\GAMADV-XTD3>
```
### Update GAMADV-XTD3 client access.

Update oauth2.txt; it must be updated to reflect the additional capabilites of GAMADV-XTD3.

If the PC on which you are running GAM does not have access to a browser or if
your default browser is Internet Explorer or Edge, issue this command:
```
gam config no_browser true oauth update
```
You will be given instructions on how to get the authorization; this involves a long URL that must be copied/pasted.
Older versions of Command Prompt and PowerShell (Windows 7/8, Server 2008) can't properly copy/paste multi line strings;
GAM writes the long URL into the file `gamoauthurl.txt` in the folder with the GAM executable.
You can open the file with Notepad/Wordpad, do a control-A to select the text, control-C to copy the text,
start a browser and paste the URL (control-V) into the address bar. Authenticate and copy the Verification code
back to your Command Prompt/PowerShell window.
```
C:\GAMADV-XTD3>gam oauth update

Select the authorized scopes by entering a number.
Append an 'r' to grant read-only access or an 'a' to grant action-only access.

[*]  0)  Calendar API (supports readonly)
[*]  1)  Chrome Browser Cloud Management API (supports readonly)
[*]  2)  Chrome Management API - Telemetry read only
[*]  3)  Chrome Management API - read only
[*]  4)  Chrome Policy API (supports readonly)
[*]  5)  Chrome Printer Management API (supports readonly)
[*]  6)  Chrome Version History API
[*]  7)  Classroom API - Course Announcements (supports readonly)
[*]  8)  Classroom API - Course Topics (supports readonly)
[*]  9)  Classroom API - Course Work/Materials (supports readonly)
[*] 10)  Classroom API - Course Work/Submissions (supports readonly)
[*] 11)  Classroom API - Courses (supports readonly)
[*] 12)  Classroom API - Profile Emails
[*] 13)  Classroom API - Profile Photos
[*] 14)  Classroom API - Rosters (supports readonly)
[*] 15)  Classroom API - Student Guardians (supports readonly)
[*] 16)  Cloud Identity Groups API (supports readonly)
[*] 17)  Cloud Storage (Vault Export - read only)
[*] 18)  Contact Delegation API (supports readonly)
[*] 19)  Contacts API - Domain Shared and Users and GAL
[*] 20)  Data Transfer API (supports readonly)
[*] 21)  Directory API - Chrome OS Devices (supports readonly)
[*] 22)  Directory API - Customers (supports readonly)
[*] 23)  Directory API - Domains (supports readonly)
[*] 24)  Directory API - Groups (supports readonly)
[*] 25)  Directory API - Mobile Devices Directory (supports readonly and action)
[*] 26)  Directory API - Organizational Units (supports readonly)
[*] 27)  Directory API - Resource Calendars (supports readonly)
[*] 28)  Directory API - Roles (supports readonly)
[*] 29)  Directory API - User Schemas (supports readonly)
[*] 30)  Directory API - User Security
[*] 31)  Directory API - Users (supports readonly)
[*] 32)  Email Audit API
[*] 33)  Groups Migration API
[*] 34)  Groups Settings API
[*] 35)  License Manager API
[*] 36)  People API (supports readonly)
[*] 37)  People Directory API - read only
[ ] 38)  Pub / Sub API
[*] 39)  Reports API - Audit Reports
[*] 40)  Reports API - Usage Reports
[ ] 41)  Reseller API
[*] 42)  Site Verification API
[*] 43)  Sites API
[*] 44)  Vault API (supports readonly)

     s)  Select all scopes
     u)  Unselect all scopes
     e)  Exit without changes
     c)  Continue to authorization
Please enter 0-44[a|r] or s|u|e|c: c

Enter your Google Workspace admin email address? admin@domain.com

Your browser has been opened to visit:

    https://accounts.google.com/o/oauth2/v2/auth?client_id=CLIENTID&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&scope=email+profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.courses+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.announcements+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.coursework.students+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.guardianlinks.students+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.profile.emails+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.profile.photos+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fclassroom.rosters+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloudprint+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdevstorage.read_only+https%3A%2F%2Fwww.google.com%2Fm8%2Ffeeds+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.datatransfer+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.device.chromeos+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.customer+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.domain+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.group+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.device.mobile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.orgunit+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.resource.calendar+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.rolemanagement+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.userschema+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.user.security+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.directory.user+https%3A%2F%2Fapps-apis.google.com%2Fa%2Ffeeds%2Fcompliance%2Faudit%2F+https%3A%2F%2Fapps-apis.google.com%2Fa%2Ffeeds%2Femailsettings%2F2.0%2F+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.groups.migration+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.groups.settings+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.licensing+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcontacts+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.reports.audit.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fadmin.reports.usage.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fapps.order+https%3A%2F%2Fsites.google.com%2Ffeeds+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fediscovery&login_hint=admin%40domain.com&access_type=offline&response_type=code

If your browser is on a different machine then press CTRL+C,
set no_browser = true in gam.cfg and re-run this command.

Authentication successful.
Client OAuth2 File: C:\GAMConfig\oauth2.txt, Updated

C:\GAMADV-XTD3>
```
### Enable GAMADV-XTD3 service account access.
```
C:\GAMADV-XTD3>gam user user@domain.com check serviceaccount
System time status:
  Your system time differs by less than 1 second from Google                PASS
Service Account Private Key Authentication:
  Authentication                                                            PASS
Domain-Wide Delegation authentication:, User: user@domain.com, Scopes: 28
  https://mail.google.com/                                                  PASS (1/28)
  https://sites.google.com/feeds                                            PASS (2/28)
  https://www.googleapis.com/auth/apps.alerts                               PASS (3/28)
  https://www.googleapis.com/auth/calendar                                  PASS (4/28)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (5/28)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (6/28)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (7/28)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (8/28)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (9/28)
  https://www.googleapis.com/auth/classroom.topics                          PASS (10/28)
  https://www.googleapis.com/auth/cloud-identity                            PASS (11/28)
  https://www.googleapis.com/auth/cloud-platform                            PASS (12/28)
  https://www.googleapis.com/auth/contacts                                  PASS (13/28)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (14/28)
  https://www.googleapis.com/auth/datastudio                                PASS (15/28)
  https://www.googleapis.com/auth/directory.readonly                        PASS (16/28)
  https://www.googleapis.com/auth/documents                                 PASS (17/28)
  https://www.googleapis.com/auth/drive                                     PASS (18/28)
  https://www.googleapis.com/auth/drive.activity                            PASS (19/28)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (20/28)
  https://www.googleapis.com/auth/drive.labels                              FAIL (21/28)
  https://www.googleapis.com/auth/gmail.modify                              PASS (22/28)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (23/28)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (24/28)
  https://www.googleapis.com/auth/keep                                      PASS (25/28)
  https://www.googleapis.com/auth/spreadsheets                              PASS (26/28)
  https://www.googleapis.com/auth/tasks                                     PASS (27/28)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (28/28)
Some scopes FAILED! Please go to:

https://admin.google.com/domain.com/ManageOauthClients?clientScopeToAdd=https://mail.google.com/,https://sites.google.com/feeds,https://www.google.com/m8/feeds,https://www.googleapis.com/auth/activity,https://www.googleapis.com/auth/apps.alerts,https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/classroom.announcements,https://www.googleapis.com/auth/classroom.coursework.students,https://www.googleapis.com/auth/classroom.rosters,https://www.googleapis.com/auth/classroom.topics,https://www.googleapis.com/auth/cloudprint,https://www.googleapis.com/auth/contacts,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/drive.activity,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.settings.basic,https://www.googleapis.com/auth/gmail.settings.sharing,https://www.googleapis.com/auth/iam,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/userinfo.email&clientNameToAdd=SVCACCTID

You will be directed to the Google Workspace admin console. The Client Name and API
Scopes fields will be pre-populated. Please click Authorize to allow these
scopes access. After authorizing it may take some time for this test to pass so
wait a few moments and then try this command again.

C:\GAMADV-XTD3>
```
The link shown in the error message should take you directly to the authorization screen.
If not, make sure that you are logged in as a domain admin, then re-enter the link.

### Verify GAMADV-XTD3 service account access.

Wait a moment and then perform the following command; it it still fails, wait a bit longer, it can sometimes take serveral minutes
for the authorization to complete.
```
C:\GAMADV-XTD3>gam user user@domain.com check serviceaccount
System time status:
  Your system time differs by less than 1 second from Google                PASS
Service Account Private Key Authentication:
  Authentication                                                            PASS
Domain-Wide Delegation authentication:, User: user@domain.com, Scopes: 28
  https://mail.google.com/                                                  PASS (1/28)
  https://sites.google.com/feeds                                            PASS (2/28)
  https://www.googleapis.com/auth/apps.alerts                               PASS (3/28)
  https://www.googleapis.com/auth/calendar                                  PASS (4/28)
  https://www.googleapis.com/auth/classroom.announcements                   PASS (5/28)
  https://www.googleapis.com/auth/classroom.coursework.students             PASS (6/28)
  https://www.googleapis.com/auth/classroom.courseworkmaterials             PASS (7/28)
  https://www.googleapis.com/auth/classroom.profile.emails                  PASS (8/28)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (9/28)
  https://www.googleapis.com/auth/classroom.topics                          PASS (10/28)
  https://www.googleapis.com/auth/cloud-identity                            PASS (11/28)
  https://www.googleapis.com/auth/cloud-platform                            PASS (12/28)
  https://www.googleapis.com/auth/contacts                                  PASS (13/28)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (14/28)
  https://www.googleapis.com/auth/datastudio                                PASS (15/28)
  https://www.googleapis.com/auth/directory.readonly                        PASS (16/28)
  https://www.googleapis.com/auth/documents                                 PASS (17/28)
  https://www.googleapis.com/auth/drive                                     PASS (18/28)
  https://www.googleapis.com/auth/drive.activity                            PASS (19/28)
  https://www.googleapis.com/auth/drive.admin.labels                        PASS (20/28)
  https://www.googleapis.com/auth/drive.labels                              PASS (21/28)
  https://www.googleapis.com/auth/gmail.modify                              PASS (22/28)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (23/28)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (24/28)
  https://www.googleapis.com/auth/keep                                      PASS (25/28)
  https://www.googleapis.com/auth/spreadsheets                              PASS (26/28)
  https://www.googleapis.com/auth/tasks                                     PASS (27/28)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (28/28)
All scopes PASSED!
Service Account Client name: SVCACCTID is fully authorized.

C:\GAMADV-XTD3>
```
