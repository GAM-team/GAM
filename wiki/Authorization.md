# Authorization
- [Introduction](#introduction)
- [Headless computers and Cloud Shells](#headless-computers-and-cloud-shells)
- [API documentation](#api-documentation)
- [Python Regular Expressions](Python-Regular-Expressions)
- [Definitions](#definitions)
- [Manage Projects](#manage-projects)
  - [Authorize a super admin to create projects](#authorize-a-super-admin-to-create-projects)
  - [Authorize Service Account Key Uploads](#authorize-service-account-key-uploads)
  - [Authorize GAM to create projects](#authorize-gam-to-create-projects)
  - [Create a new GCP project folder](#create-a-new-gcp-project-folder)
  - [Create a new project for GAM authorization](#create-a-new-project-for-gam-authorization)
  - [Use an existing project for GAM authorization](#use-an-existing-project-for-gam-authorization)
  - [Update an existing project for GAM authorization](#update-an-existing-project-for-gam-authorization)
  - [Delete an existing project for GAM authorization](#delete-an-existing-project-for-gam-authorization)
  - [Display projects](#display-projects)
- [Manage Client credentials](#manage-client-credentials)
  - [Create Client credentials](#create-client-credentials)
  - [Refresh Client credentials](#refresh-client-credentials)
  - [Update Client credentials](#update-client-credentials)
  - [Delete Client credentials](#delete-client-credentials)
  - [Verify Client credentials](#verify-client-credentials)
  - [Export Client credentials](#export-client-credentials)
- [Manage Service Accounts](#manage-service-accounts)
  - [Add Service Accounts to projects](#add-service-accounts-to-projects)
  - [Delete Service Accounts from projects](#delete-service-accounts-from-projects)
  - [Display Service Accounts for projects](#display-service-accounts-for-projects)
- [Manage Service Account keys](#manage-service-account-keys)
  - [Create a new Service Account key](#create-a-new-service-account-key)
  - [Update an existing Service Account key](#update-an-existing-service-account-key)
  - [Replace all existing Service Account keys](#replace-all-existing-service-account-keys)
  - [Delete Service Account keys](#delete-service-account-keys)
  - [Upload a Service Account key to a service account with no keys](#upload-a-service-account-key-to-a-service-account-with-no-keys)
  - [Display Service Account keys](#display-service-account-keys)
- [Manage Service Account access](#manage-service-account-access)
  - [Full Service Account access](#full-service-account-access)
  - [Selective Service Account access](#selective-service-account-access)
- [Configure Limited access](#configure-limited-access)
  - [Limited Client access](#limited-client-access)
  - [No Client access](#no-client-access)
  - [Limited Service Account access](#limited-service-account-access)
  - [todrive Service Account access](#todrive-service-account-access)
  - [No Service Account access possible](#no-service-account-access-possible)
  - [Test Client and Service Account access on your computer](#test-client-and-service-account-access-on-your-computer)
  - [Install GAM on the limited users computer](#install-gam-on-the-limited-users-computer)
  - [Test Client and Service Account access on the non-administrator computer](#test-client-and-service-account-access-on-the-non-administrator-computer)
  - [Unselect limited section on your computer.](#unselect-limited-section-on-your-computer)
- [Delete old versions of GAM from Configured Apps](#delete-old-versions-of-gam-from-configured-apps)

## Introduction
GAM requires authorization to perform tasks on your domain; the tasks break down into two categories:
* Client - Manipulate objects in the domain; the Client acts on its own behalf to perform the tasks. Examples: add a user, update a group, delete a class, share a printer.
* Service Account - Manipulate objects that belong to users; the Service Account acts on behalf of the user to perform the tasks. Examples: view user files, calendars.

You create projects that define these authorizations.

Verify the following steps:
* See https://support.google.com/a/answer/9197205?hl=en
* Access the admin console and go to Apps -> Additional Google Services 
* Look for the service "Google Cloud Platform", click it
* Expand "Service status"
* Select the OU in the left that contains the super admin you'll be using
* Make sure that "Service status" is ON
* If groups are used to authenticate access, make sure the super admin is in one of the groups
* Collapse "Service status"
* Expand "Cloud Resource Manager API settings"
* Make sure that "Allow users to create projects" is checked

Verify that all scopes are available:
* Access the admin console and go to Apps -> Additional Google Services 
* If this line is present: `Access to additional services without individual control for all organizational units is turned Off`
* Click "CHANGE"
* Select "ON for everyone"
* Click "SAVE"

Verify that internal apps are trusted.
* Access the admin console and go to Security -> Access and data control -> API Controls
* Check that "Trust internal, domain-owned apps" is present in the **Settings** section
* Click "SAVE"

If you run a Google Workspace Education SKU, verify that Classroom API is enabled if required.
* Access the admin console and go to Apps -> Google Workspace - Classroom
* Expand "Data access"
* Check "Users can authorize apps to access their Google Classroom data."
* Click "SAVE"

If you run a Google Workspace Education SKU, verify that the super admin you'll be using is in an OU where "All users are 18 or older".
* Access the admin console and go to Accounts -> Account settings
* Expand "Age based access settings"
* Select the OU containing the super admin
* Choose "All users are 18 or older"
* Click "SAVE"

Based on your domain policies, you may have to mark GAM as a trusted app. These steps are performed after a project is created.
* Access the admin console and go to Security -> Access and data control -> API controls
* Click Manage third-party app access
* Click Configure new app
* Paste client_id value from client_secrets.json in Search for app
* Click Search
* Click the line referencing GAM
* Keep the default scope All in domain.com (all users) or select an org unit that includes your GAM admin
* Click Continue
* Click Trusted: App can request access to all Google data
* Click Continue
* Click Finish
* Press Confirm if Confirm parental consent pops up

Verify whether the super admin you'll be using is in an OU where reauthentication is required.
* Access the admin console and go to Security -> Overview
* Scroll down and open Google Cloud session control section
* Select the OU containing the super admin
* If Require reauthentication is selected and Exempt Trusted apps is not checked, you'll have to do `gam oauth create` at whatever frequency is specified
* If that sounds unappealing, check Exempt Trusted apps
* Click "OVERRIDE"

Additional steps may be required if errors are encountered.
* [Authorize a super admin to create projects](#authorize-a-super-admin-to-create-projects)
* [Authorize Service Account Key Uploads](#authorize-service-account-key-uploads)
* [Authorize GAM to create projects](#authorize-gam-to-create-projects)

## Headless computers and Cloud Shells
With many thanks to Jay, `gam oauth create` now uses a new client access authentication flow
as required by Google for headless computers/cloud shells; this is required as of February 28, 2022.
* See: https://developers.googleblog.com/2022/02/making-oauth-flows-safer.html
  * OAuth out-of-band (oob) flow will be deprecated

## API documentation
* https://cloud.google.com/resource-manager/docs/creating-managing-organization#adding_an_organization_administrator
* https://cloud.google.com/service-usage/docs/reference/rest
* https://cloud.google.com/resource-manager/reference/rest/v3/projects/create
* https://cloud.google.com/resource-manager/reference/rest/v3/projects/list
* https://cloud.google.com/resource-manager/reference/rest/v3/projects/getIamPolicy
* https://cloud.google.com/iam/docs/understanding-service-accounts
* https://developers.google.com/identity/protocols/oauth2
* https://developers.google.com/identity/protocols/googlescopes
* https://developers.google.com/admin-sdk/directory/v1/guides/delegation
* https://support.google.com/a/answer/7281227?hl=en#zippy=%2Cmanage-access-to-apps-trusted-limited-or-blocked

## Definitions
```
<APIScopeURL> ::= <String>
<APIScopeURLList> ::= "<APIScopeURL>(,<APIScopeURL>)*"
<ProjectID> ::= <String>
        Must match this Python Regular Expression: [a-z][a-z0-9-]{4,28}[a-z0-9]
<ProjectIDList> ::= "<ProjectID>(,<ProjectID>)*"
<ProjectIDEntity> ::=
        current | gam | <ProjectID> | (filter <String>) |
        (select <ProjectIDList> | <FileSelector> | <CSVFileSelector>)
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<ProjectName> ::= <String>
        Must match this Python Regular Expression: [a-zA-Z0-9 '"!-]{4,30}
<ServiceAccountName> ::= <String>
        Must match this Python Regular Expression: [a-z][a-z0-9-]{4,28}[a-z0-9]
<ServiceAccountDisplayName> ::= <String>
        Maximum of 100 characters
<ServiceAccountDescrition> ::= <String>
        Maximum of 256 characters
<ServiceAccountEmail> ::= <ServiceAccountName>@<ProjectID>.iam.gserviceaccount.com
<ServiceAccountUniqueID> ::= <Number>
<ServiceAccountKey> ::= <String>
```
## Manage Projects
In all of the project commands, the Google Workspace admin/GCP project manager `<EmailAddress>` can be omitted; you will be prompted for a value.
You must enter a full address, i.e., user@domain.com; you will be required to authenticate.

For `print|show projects`, you can eliminate the password prompt and authentication requirement by specifying the super admin emailaddress used in `gam oauth create`.
```
gam print projects admin admin@domain.com
```

## Authorize a super admin to create projects
If you try to create a project and get an error saying that the admin you specified is not authorized to create projects,
perform these steps and then retry the create project command.

* Login as an existing super admin at console.cloud.google.com
* In the upper left click the three lines to the left of Google Cloud and select IAM & Admin
* Under IAM & Admin select IAM
* Click in the box to the right of Google Cloud
* Click the three dots at the right and select IAM/Permissions
* Now you should be at "Permissions for organization ..."
* Click on Grant Access
* Enter the new admin address in Principals
* Click in the Select a role box
* Type project creator in the Filter box
* Click Project Creator
* Click + Add Another Role
* Type orgpolicy.policyAdmin in the Filter box
* Click Organization Policy Administrator
* Click Save

## Authorize Service Account Key Uploads

If you try to create a project and get an error saying that Constraint `constraints/iam.disableServiceAccountKeyUpload violated for service account projects/gam-project-xxxxx`,
perform these steps and then you should be able to authorize and use your project.

* Login as an existing super admin at console.cloud.google.com
* In the upper left click the three lines to the left of Google Cloud and select IAM & Admin
* Under IAM & Admin select IAM
* Click in the box to the right of Google Cloud
* Click the three dots at the right and select IAM/Permissions
* Now you should be at "Permissions for organization ..."
* Click on Grant Access
* Enter the new admin address in Principals
* Click in the Select a role box
* Type orgpolicy.policyAdmin in the Filter box
* Click Organization Policy Administrator
* Click Save
* In the upper left click the three lines to the left of Google Cloud and select IAM & Admin
* Under IAM & Admin select IAM
* Click in the box to the right of Google Cloud
* Click the three dots at the right and select Manage Resources
* Click the three dots at the end of the line for the GAM project just created
* Click Settings
* Click Organization Policies in the left column
* Now you should be at "Policies for Gam Project"
* Click in the Filter box
* Enter iam.managed.disableServiceAccountKeyUpload
* Click the three dots at the end of the Disable service account key upload/iam.managed.disableServiceAccountKeyUpload line
* Choose Edit policy
* Click Override parent's policy
* Click Add A Rule
* Select Enforcement/Off
* Click Done
* Click Set Policy
* Click the three dots at the end of the Disable Service Account Key Upload/iam.disableServiceAccountKeyUpload line
* Choose Edit policy
* Click Override parent's policy
* Click Add A Rule
* Select Enforcement/Off
* Click Done
* Click Set Policy

Wait a couple of minutes for the policy updates to complete and then do the following to upload the service account key:
```
gam upload sakey [admin <EmailAddress>]
```

## Authorize GAM to create projects
If you try to create a project and get an error saying "This app has been blocked on your domain for either being
insecure or non-edutational"; you'll have to mark the GAM Project Creation app as trusted.
Perform these steps and then retry the create project command.

* Access the admin console and go to Security -> Access and data control -> API controls
* Click **Manage third-party app access**
* Click Add app and select **OAuth App Name Or Client ID**
* Paste 297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com
* Click Search
* Click Select at right end of line referencing GAM Project Creation
* Check box to the left of the line with GAM Project Creation client ID
* Click Select
* Keep the default scope domain.com (all users) or select an org unit that includes your GAM admin
* Click Next/Continue
* Click Trusted: App can request access to all Google data
* Click Next/Continue
* Click Finish/Confirm

## Create a new GCP project folder
This folder can be used in a subsequent `gam create project parent <String>` command.
```
gam create gcpfolder <String>
gam create gcpfolder [admin <EmailAddress] folder <String>
```

## Create a new project for GAM authorization
Create a new project to create and download two files: `client_secrets.json` for the Client and `oauth2service.json` for the Service Account.
On-screen instructions lead you through the process.

An existing project, `GAM Project Creation`, is used to create your GAM project. The initial instructions tell you how to
enable this project as a trusted app as your workspace may not allow untrusted third-party apps.
This is recommended but not mandatory unless your workspace has "Google Cloud" service restricted:
* https://support.google.com/a/answer/7281227?hl=en#zippy=%2Crestrict-or-unrestrict-google-services

If it is restricted and you complete this step it may take an hour or so to take full affect and allow you to approve GAM project creation.

The final instructions tell you how to enable your new GAM project as a trusted app as your workspace may not allow untrusted third-party apps.
You can skip these steps if you know that untrusted third-party apps are allowed.

### Default values
* `<AppName>` - "GAM"
* `<ProjectID>` - "gam-project-a1b2c" where "a1b2c" are randomly generated
* `<ProjectName>` - "GAM Project"
* `<ServiceAccountName>` - `<ProjectID>`
* `<ServiceAccountDisplayName>` - `<ProjectName>`
* `<ServiceAccountDescription>` - `<ServiceAccountDisplayName>`

### Basic
Create a project with default values for the project and service account.
```
gam create project [<EmailAddress>] [<ProjectID>]
```
* `<EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address
* `<ProjectID>` - A new Google project ID; if omitted, a default value will be used

### Advanced
Create a project with user-specified values for the project and service account.
```
gam create project [admin <EmailAddress>] [project <ProjectID>]
        [appname <String>] [supportemail <EmailAddress>]
        [projectname <ProjectName>] [parent <String>]
        [saname <ServiceAccountName>] [sadisplayname <ServiceAccountDisplayName>]
        [sadescription <ServiceAccountDescription>]
        [(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
         (localkeysize 1024|2048|4096 [validityhours <Number>])|
         (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)|
         nokey}
```
* `admin <EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address
* `appname <String>` - Application name, defaults to `GAM`
* `supportemail <EmailAddress>` - Administrator to contact about GAM authentication, defaults to `admin <EmailAddress>`
* `project <ProjectID>` - A new Google project ID; if omitted, a default value will be used
* `projectname <ProjectName>` - Google project name, defaults to "GAM Project"
* `parent <String>` - A Resource Manager folder name
* `saname <ServiceAccountName>` - Service account name; combined with `<ProjectID>` to form `<ServiceAccountEmail>`
* `sadisplayname <ServiceAccountDisplayName>` - Service account display name
* `sadescription <ServiceAccountDescription>` - Service account description

You can optionally specify the type of service account key with `algorithm|localkeysize|yubikey`: [Manage Service Account keys](#manage-service-account-keys)

Use `nokey` if you do not want a service account key created for the project.

## Use an existing project for GAM authorization
Use an existing project to create and download two files: `client_secrets.json` for the Client and `oauth2service.json` for the Service Account.

### Default values
* `<ServiceAccountName>` - `<ProjectID>`
* `<ServiceAccountDisplayName>` - `<ProjectName>`
* `<ServiceAccountDescription>` - `<ServiceAccountDisplayName>`

### Basic
Use an existing uninitialized/uncredentialed project and configure it to be a GAM project; this typically used when
the GCP  administrators have created a basic project because project creation is not available for most users.

See Jay's notes about how to do this: https://github.com/GAM-team/GAM/wiki/GAM-with--minimal-GCP-rights

```
gam use project [<EmailAddress>] [project <ProjectID>]
```
* `<EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address
* `<ProjectID>` - An existing Google project ID; if omitted, you will be prompted for the ID

### Advanced
Use an existing project with user-specified values for the service account. If the project is already
a GAM project you must use `saname <ServiceAccountName>` as the existing service account information
can not be re-downloaded.
```
gam use project [admin <EmailAddress>] [project <ProjectID>]
        [saname <ServiceAccountName>] [sadisplayname <ServiceAccountDisplayName>]
        [sadescription <ServiceAccountDescription>]
        [(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
         (localkeysize 1024|2048|4096 [validityhours <Number>])|
         (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)]
```
* `admin <EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address
* `project <ProjectID>` - An existing Google project ID; if omitted, you will be prompted for the ID
* `saname <ServiceAccountName>` - Service account name; combined with `<ProjectID>` to form `<ServiceAccountEmail>`
* `sadisplayname <ServiceAccountDisplayName>` - Service account display name
* `sadescription <ServiceAccountDescription>` - Service account description

You can optionally specify the type of service account key with `algorithm|localkeysize|yubikey`: [Manage Service Account keys](#manage-service-account-keys)

## Update an existing project for GAM authorization
This command is used when GAM has added new capabilities that require additional APIs to be added to your project.
```
gam update project [[admin] <EmailAddress>] [<ProjectIDEntity>]
```
* `<EmailAddress>` - A Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `current` - The project referenced in `client_secrets.json`; this is the default
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation

## Delete an existing project for GAM authorization
```
gam delete project [[admin] <EmailAddress>] [<ProjectIDEntity>]
```
* `<EmailAddress>` - A Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `current` - The project referenced in `client_secrets.json`; this is the default
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation

## Display projects
Display the current Project ID.
```
gam info currentprojectid
```

Display Google API projects as an indented list of keys and values.
```
gam show projects [[admin] <EmailAddress>] [all|<ProjectIDEntity>]
        [states all|active|deleterequested] [showiampolicies 0|1|3]
```
* `<EmailAddress>` - A Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `all` - All projects accessible by the administrator; this is the default
* `current` - The project referenced in `client_secrets.json`
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation
* `states all|active|deleterequested` - Limit display to projects based on state; the default is `active`

Use the `showiampolicies 0|1|3` option to display IAM policy information for the project.

Display Google API projects as columns of fields.
```
gam print projects [[admin] <EmailAddress>] [all|<ProjectIDEntity>] [todrive <ToDriveAttribute>*]
        [states all|active|deleterequested] [showiampolicies 0|1|3 [onememberperrow]]
        [delimiter <Character>]] [[formatjson [quotechar <Character>]]
```
* `<EmailAddress>` - A Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `all` - All projects accessible by the administrator; this is the default
* `current` - The project referenced in `client_secrets.json`
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation
* `states all|active|deleterequested` - Limit display to projects based on state; the default is `active`

Use the `showiampolicies 0|1|3` option to display IAM policy information for the project. Each role in the policy will be displayed on
a separate row; by default, all members will be shown on that row. By default, the members are separated by
the `csv_output_field_delimiter` from `gam.cfg`.
* `delimiter <Character>` - Separate list items with `<Character>`

Use the `onememberperrow` option to show separate rows for each role/member combination.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Manage Client credentials

## Create Client credentials
```
gam oauth|oauth2 create|request [<EmailAddress>]
gam oauth|oauth2 create|request [admin <EmailAddress>] [scopes <APIScopeURLList>]
```
* `<EmailAddress>` - A Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address
* `scopes <APIScopeURLList>` - A set of specific scopes; if omitted, you will be prompted to select your desired scopes.

You select a list of scopes, GAM uses a browser to get final authorization from Google for these scopes and
writes the credentials into the file oauth2.txt.

```
gam oauth create

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
```

## Update Client credentials
```
gam oauth update [<EmailAddress>]
gam oauth update [admin <EmailAddress>]
```
* `<EmailAddress>` - A Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Read API scopes from any version of `oauth2.txt` and select a list of APIs; GAM uses a browser to get final authorization from Google for these APIs and
writes the credentials into the file `oauth2.txt`.

```
gam oauth update

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
```

If you have multiple sections in `gam.cfg` that reference different `oauth2.txt` files, perform an update on each section:
```
gam select aaa oauth update
gam select bbb oauth update
...
```

## Refresh Client credentials
Refresh the expiration time in `oauth2.txt`.
```
gam oauth refresh
```

If you have multiple sections in `gam.cfg` that reference different `oauth2.txt` files, perform a refresh on each section:
```
gam select aaa oauth refresh
gam select bbb oauth refresh
...
```

## Delete Client credentials
```
gam oauth|oauth2 delete|revoke
```
Revoke the credentials in the file `oauth2.txt` and then delete the file.

## Verify Client credentials
```
<AccessToken> ::= <String>
<IDToken> ::= <String>
gam oauth|oauth2 info|verify [showsecret] [accesstoken <AccessToken> idtoken <IDToken>] [showdetails]
```
The Client Secret is not shown by default, user `showsecret` to have it displayed.

These options are used for debugging: `accesstoken <AccessToken> idtoken <IDToken> showdetails`.

## Export Client credentials

Export `oauth2.txt` in JSON form.
```
gam oauth|oauth2 export [<FileName>]
```
* If `<FileName>` is omitted, the JSON data is written to `oauth2.txt`.
* If `<FileName>` is `-`, the JSON data is written to stdout.

## Manage Service Accounts
In all of the service account commands, the Google Workspace admin/GCP project manager `<EmailAddress>` can be omitted; you will be prompted for a value.
You must enter a full address, i.e., user@domain.com; you will be required to enter the password.

## Add Service Accounts to projects
You can add additional service accounts to a project and assign it specific access APIs. This command
creates a new `oauth2service.json` file; it will not overwrite an existing file so you must rename the existing
file or define a new section in `gam.cfg` that references a different `oauth2service_json` or `config_dir`.

### Default values
* `<ServiceAccountName>` - "gam-svcacct-abc-def-jki" where "abc-def-ghi" are randomly generated
* `<ServiceAccountDisplayName>` - `<ServiceAccountName>`
* `<ServiceAccountDescription>` - `<ServiceAccountDisplayName>`
```
gam create|add svcacct [[admin] <EmailAddress>] [<ProjectIDEntity>]
        [saname <ServiceAccountName>] [sadisplayname <ServiceAccountDisplayName>]
        [sadescription <ServiceAccountDescription>]
        [(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
         (localkeysize 1024|2048|4096 [validityhours <Number>])|
         (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)]
```
* `<EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `current` - The project referenced in `client_secrets.json`; this is the default
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation

Use these options to select user-specified values..
* `saname <ServiceAccountName>` - Service account name; combined with `<ProjectID>` to form `<ServiceAccountEmail>`
* `sadisplayname <ServiceAccountDisplayName>` - Service account display name
* `sadescription <ServiceAccountDescription>` - Service account description

You can optionally specify the type of service account key with `algorithm|localkeysize|yubikey`: [Manage Service Account keys](#manage-service-account-keys)

After adding an additional service account, you can select specific access APIs for it.
[Selective Service Account access](#selective-service-account-access)

## Delete Service Accounts from projects
```
gam delete svcacct [[admin] <EmailAddress>] [<ProjectIDEntity>]
        (saemail <ServiceAccountEmail>)|(saname <ServiceAccountName>)|(sauniqueid <ServiceAccountUniqueID>)
```
* `<EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `current` - The project referenced in `client_secrets.json`; this is the default
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation

## Display Service Accounts for projects
Display Service Accounts as an indented list of keys and values.
```
gam show svcaccts [[admin] <EmailAddress>] [all|<ProjectIDEntity>]
        [showsakeys all|system|user]
```
Display Service Accounts as columns of fields.
```
gam print svcaccts [[admin] <EmailAddress>] [all|<ProjectIDEntity>]
        [showsakeys all|system|user]
        [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]
```
* `<EmailAddress>` - Google Workspace admin/GCP project manager; if omitted, you will be prompted for the address

Use these options to select projects.
* `all` - All projects accessible by the administrator; this is the default
* `current` - The project referenced in `client_secrets.json`
* `gam` - Projects accessible by the administrator that were created by Gam, i.e, their project ID begins with `gam-project-`
* `<ProjectID>` - A Google API project ID
* `filter <String>` - A filter to select projects accessible by the administrator; see the API documentation

By default, no Service Account key information is displayed, use the following options to display keys.
* `showsakeys all` - Display system and user keys; this is the default when keys are displayed
* `showsakeys system` - Display system keys
* `showsakeys user` - Display user keys

## Manage Service Account keys
The `oauth2service.json` file contains a private key that is used to authenticate Service Account access.
This private key will be referred to as the `current` private key.

Each Service Account in a project typically has one private key but it can have multiple keys; this might be the
case if you have several users with Gam access where they will all access the same Service Account but with different keys.
You will distribute different `oauth2service.json` files to each user, each with its own private key.

There are several methods for generating private keys:
* `algorithm KEY_ALG_RSA_1024` - Google generates a 1024 bit key; not recommended
* `algorithm KEY_ALG_RSA_2048` - Google generates a 2048 bit key
* `localkeysize 1024` - Gam generates a 1024 bit key; this is not recommended
* `localkeysize 2048` - Gam generates a 2048 bit key; this is the default
* `localkeysize 4096` - Gam generates a 4096 bit key
* `yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)]` - [Using GAM7 with a YubiKey](Using-GAM7-with-a-YubiKey)

When `localkeysize` is specified, the optional argument `validityhours <Number>` sets the length of time during which the key will be valid and should be used when the [GCP constraints/iam.serviceAccountKeyExpiryHours organization policy](https://cloud.google.com/resource-manager/docs/organization-policy/restricting-service-accounts#limit_key_expiry) is in use. Note that in order to account for system clock skew, GAM sets the key to be valid two minutes earlier than the current system time and thus it will also expire two minutes earlier.

Here are some sample values:
```
   1 hour
   8 hours
  24 hours ( 1 day)
 168 hours ( 7 days)
 336 hours (14 days)
 720 hours (30 days)
1440 hours (60 days)
2160 hours (90 days)
```

## Create a new Service Account key
Create a new Service Account private key; all existing private keys remain valid.
The `oauth2service.json` file is updated with the new private key.

Keep a good record of where each Service Account key is used as the keys themselves do not record this information.

The two forms of the command are equivalent; the second form is used by Legacy GAM.
```
gam create sakey
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
gam rotate sakey retain_existing
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
```
To distribute `oauth2service.json` files with unique private keys perform the following steps:
```
copy oauth2service.json to oauth2service.save
repeat
  gam create sakeys retain_existing
  distribute updated oauth2service.json file
  copy oauth2service.save to oauth2service.json
```

## Update an existing Service Account key
Revoke the current Service Account key and replace it with a new private key; all other private keys remain valid.
The `oauth2service.json` file is updated with the new private key. If you had previously distributed
this `oauth2service.json` file to other users, you must redistribute the updated file as the private key
in the distributed copies has been revoked.

The two forms of the command are equivalent; the second form is used by Legacy GAM.
```
gam update sakey
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
gam rotate sakey replace_current
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
```
## Replace all existing Service Account keys
Create a new Service Account private key; all existing private keys are revoked.
The `oauth2service.json` file is updated with the new private key. If you had previously distributed
any `oauth2service.json` file to other users, you must redistribute the updated file as the private key
in the distributed copies has been revoked.

This command can be used if your Service Account keys have been compromised; all existing private keys are revoked.

The two forms of the command are equivalent; the second form is used by Legacy GAM.
```
gam replace sakeys
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
gam rotate sakeys retain_none
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
```
## Delete Service Account keys
You can delete Service Accounts keys thus revoking access for that key. Generally, you will
delete a service account key for a distributed copy of an `oauth2service.json` file to disable
that user's service account access.

You can disable your current Service Account key if you specify the `doit` argument. This is your
acknowledgement that you will have to manually create a new Service Account key in the Developer's Console
or upload a new key with the `gam upload sakey` command.
```
gam delete sakeys <ServiceAccountKeyList>+ [doit]
```
## Upload a Service Account key to a service account with no keys
There are two cases where you will use this command:
* Your workspace is configured to disable service account private key uploads and you are creating a project.
* All of your service account keys have been deleted, either manually or with the `gam delete sakeys` command.

The `oauth2service.json` file is updated with the new private key. If you had previously distributed
any `oauth2service.json` file to other users, you must redistribute the updated file with the new key.
```
gam upload sakey [admin <EmailAddress>]
        (algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
        (localkeysize 1024|2048|4096 [validityhours <Number>])|
        (yubikey yubikey_pin yubikey_slot AUTHENTICATION|SIGNATURE yubikey_serialnumber <Number>)
```
## Display Service Account keys
There are system keys and user keys; user keys are what Gam uses; GCP uses system keys.

Display Service Account keys as an indented list of keys and values.
```
gam show sakeys [all|system|user]
```
* `all` - Display system and user keys; this is the default
* `system` - Display system keys
* `user` - Display user keys

The private key currently being used in `oauth2service.json` will be marked as `usedToAuthenticateThisRequest: True`.

## Manage Service Account access

## Full Service Account access

Verify that the Service Account credentials have been authorized. If they have not, you will be given instructions
as to how to perform the authorization.
By default, the following scopes are verified:
```
https://mail.google.com/
https://sites.google.com/feeds
https://www.googleapis.com/auth/analytics.readonly
https://www.googleapis.com/auth/apps.alerts
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/chat.delete
https://www.googleapis.com/auth/chat.memberships
https://www.googleapis.com/auth/chat.messages
https://www.googleapis.com/auth/chat.spaces
https://www.googleapis.com/auth/classroom.announcements
https://www.googleapis.com/auth/classroom.coursework.students
https://www.googleapis.com/auth/classroom.courseworkmaterials
https://www.googleapis.com/auth/classroom.profile.emails
https://www.googleapis.com/auth/classroom.profile.photos
https://www.googleapis.com/auth/classroom.rosters
https://www.googleapis.com/auth/classroom.topics
https://www.googleapis.com/auth/cloud-identity
https://www.googleapis.com/auth/cloud-platform
https://www.googleapis.com/auth/contacts
https://www.googleapis.com/auth/contacts.other.readonly
https://www.googleapis.com/auth/datastudio
https://www.googleapis.com/auth/directory.readonly
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/drive.activity
https://www.googleapis.com/auth/drive.admin.labels
https://www.googleapis.com/auth/drive.labels
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.settings.basic
https://www.googleapis.com/auth/gmail.settings.sharing
https://www.googleapis.com/auth/keep
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/tasks
https://www.googleapis.com/auth/userinfo.profile
```
This scope is verified when `user_service_account_access_only = true` in `gam.cfg`.
```
https://www.googleapis.com/auth/apps.groups.migration
```
Verify/enable service account access for the default list of APIs.
The two forms of the command are equivalent.
```
gam check svcacct <UserTypeEntity> (scope|scopes <APIScopeURLList>)*
gam <UserTypeEntity> check serviceaccount (scope|scopes <APIScopeURLList>)*
```
* `<UserTypeEntity>` - Typically `user <EmailAddress>`, a non-Google Workspace administrator.
* `scopes <APIScopeURLList>` - Verify/enable service account access for a set of specific scopes rather than the default list.

## Selective Service Account access

Verify/enable service account access for a selected list of APIs rather than the default list.
The two forms of the command are equivalent.

If `scopes <APIScopeURLList>` is not specified, you will be prompted to select a list of scopes.
```
gam update svcacct <UserTypeEntity> (scope|scopes <APIScopeURLList>)*
gam <UserTypeEntity> update serviceaccount (scope|scopes <APIScopeURLList>)*
```
* `<UserTypeEntity>` - Typically `user <EmailAddress>`, a non-Google Workspace administrator.
* `scopes <APIScopeURLList>` - Verify/enable service account access for a set of specific scopes rather than selecting the scopes.

```
gam user user@domain.com update serviceaccount

[*]  0)  AlertCenter API
[*]  1)  Analytics API - read only
[*]  2)  Analytics Admin API - read only
[*]  3)  Calendar API (supports readonly)
[*]  4)  Chat API - Memberships (supports readonly)
[*]  5)  Chat API - Messages (supports readonly)
[*]  6)  Chat API - Spaces (supports readonly)
[*]  7)  Chat API - Spaces Delete
[*]  8)  Classroom API - Course Announcements (supports readonly)
[*]  9)  Classroom API - Course Topics (supports readonly)
[*] 10)  Classroom API - Course Work/Materials (supports readonly)
[*] 11)  Classroom API - Course Work/Submissions (supports readonly)
[*] 12)  Classroom API - Profile Emails
[*] 13)  Classroom API - Profile Photos
[*] 14)  Classroom API - Rosters (supports readonly)
[*] 15)  Cloud Identity Devices API (supports readonly)
[*] 16)  Cloud Resource Manager API v3
[*] 17)  Docs API (supports readonly)
[*] 18)  Drive API (supports readonly)
[*] 19)  Drive API - todrive
[*] 20)  Drive Activity API v2 - must pair with Drive API
[*] 21)  Drive Labels API - Admin (supports readonly)
[*] 22)  Drive Labels API - User (supports readonly)
[*] 23)  Forms API
[*] 24)  Gmail API - Basic Settings (Filters,IMAP, Language, POP, Vacation) - read/write, Sharing Settings (Delegates, Forwarding, SendAs) - read
[*] 25)  Gmail API - Full Access (Labels, Messages)
[*] 26)  Gmail API - Full Access (Labels, Messages) except delete message
[ ] 27)  Gmail API - Full Access - read only
[ ] 28)  Gmail API - Send Messages - including todrive
[*] 29)  Gmail API - Sharing Settings (Delegates, Forwarding, SendAs) - write
[*] 30)  Identity and Access Management API
[*] 31)  Keep API (supports readonly)
[*] 32)  Looker Studio API (supports readonly)
[*] 33)  OAuth2 API
[*] 34)  People API (supports readonly)
[*] 35)  People API - Other Contacts - read only
[*] 36)  People Directory API - read only
[*] 37)  Sheets API (supports readonly)
[*] 38)  Sheets API - todrive
[*] 39)  Sites API
[*] 40)  Tasks API (supports readonly)
[ ] 41)  Youtube API - read only

Select an unselected scope [ ] by entering a number; yields [*]
For scopes that support readonly, enter a number and an 'r' to grant read-only access; yields [R]
For scopes that support action, enter a number and an 'a' to grant action-only access; yields [A]
Clear read-only access [R] or action-only access [A] from a scope by entering a number; yields [*]
Unselect a selected scope [*] by entering a number; yields [ ]
Select all default scopes by entering an 's'; yields [*] for default scopes, [ ] for others
Unselect all scopes by entering a 'u'; yields [ ] for all scopes
Exit without changes/authorization by entering an 'e'
Continue to authorization by entering a 'c'

Please enter 0-41[a|r] or s|u|e|c: c

System time status
  Your system time differs from admin.googleapis.com by less than 1 second  PASS
Service Account Private Key Authentication
  Authentication                                                            PASS
Service Account Private Key age; Google recommends rotating keys on a routine basis
  Service Account Private Key age: 364 days                                 WARN
Domain-wide Delegation authentication:, User: user@domain.com, Scopes: 34
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
  https://www.googleapis.com/auth/classroom.profile.photos                  PASS (14/34)
  https://www.googleapis.com/auth/classroom.rosters                         PASS (15/34)
  https://www.googleapis.com/auth/classroom.topics                          PASS (16/34)
  https://www.googleapis.com/auth/cloud-identity                            PASS (17/34)
  https://www.googleapis.com/auth/cloud-platform                            PASS (18/34)
  https://www.googleapis.com/auth/contacts                                  PASS (19/34)
  https://www.googleapis.com/auth/contacts.other.readonly                   PASS (20/34)
  https://www.googleapis.com/auth/datastudio                                PASS (21/34)
  https://www.googleapis.com/auth/directory.readonly                        PASS (22/34)
  https://www.googleapis.com/auth/documents                                 PASS (23/34)
  https://www.googleapis.com/auth/drive                                     PASS (24/34)
  https://www.googleapis.com/auth/drive.activity                            PASS (25/34)
  https://www.googleapis.com/auth/drive.admin.labels                        FAIL (26/34)
  https://www.googleapis.com/auth/drive.labels                              FAIL (27/34)
  https://www.googleapis.com/auth/gmail.modify                              PASS (28/34)
  https://www.googleapis.com/auth/gmail.settings.basic                      PASS (29/34)
  https://www.googleapis.com/auth/gmail.settings.sharing                    PASS (30/34)
  https://www.googleapis.com/auth/keep                                      PASS (31/34)
  https://www.googleapis.com/auth/spreadsheets                              PASS (32/34)
  https://www.googleapis.com/auth/tasks                                     PASS (33/34)
  https://www.googleapis.com/auth/userinfo.profile                          PASS (34/34)
Some scopes Failed!
To authorize them, please go to the following link in your browser:

    https://admin.google.com/ac/owl/domainwidedelegation?clientScopeToAdd=https://mail.google.com/,...

You will be directed to the Google Workspace admin console Security > API Controls > Domain-wide Delegation page
The "Add a new Client ID" box will open
Make sure that "Overwrite existing client ID" is checked
Click AUTHORIZE
When the box closes you're done
After authorizing it may take some time for this test to pass so wait a few moments and then try this command again.
```

## Configure Limited access
You can configure GAM to allow users limited access to your domain via GAM.
You can limit both client and service account access.
You can repeat these steps if you want to configure multiple limited users;
substitute a unique value for `limited` in each of the steps.

In the Admin console, define a new Admin role with the desired privileges,
assign it to the limited user and indicate whether it is for all Org Units or a specific Org Unit.

On your computer, perform these initial steps:

Make a subdirectory `limited` under the directory specified in `gam.cfg config_dir`

Create a new section at the end of your `gam.cfg` file.
```
[limited]
config_dir = limited
```
Copy `client_secrets.json` to the `limited` subdirectory

Select the `limited` section
```
gam select limited save
```

## Limited Client access
Perform these steps to allow limited client access:

Configure `todrive` to allow uploading of files to the limited user's Google Drive.
```
gam config todrive_user limited@domain.com save
```
If it is not possible to allow the limited user any service account access (this is not common),
perform the following command so that the user can upload files with `todrive` using client access.
```
gam config todrive_clientaccess true save
```

Authorize the desired client access APIs; this will create `oauth2.txt`.
If it is not possible to allow the limited user any service account access,
login as the limited user; you must have assigned Admin API Privileges to the limited user
in the Admin console under Admin roles,

If the limited user will have service account access, login as a Google admin.

```
gam oauth create
```

## No Client access
Perform these steps to allow no client access:

Configure `todrive` to allow uploading of files to the limited user's Google Drive.
```
gam config todrive_user limited@domain.com todrive_clientaccess false save
```

Configure for service account access only.
```
gam config user_service_account_access_only true save
```

Make a `oauth2.txt` file in the `limited` subdirectory with a single line as follows:
```
{}
```
This will prevent the limited user from having any client access.

## Limited Service Account access
Perform these steps:

Create a a new service account in your project that will be used for the limited user;
this will create `oauth2service.json`.
```
gam add svcacct saname "gam-limited" sadisplayname "GAM Limited"
```

Authorize the  desired APIs; this will update `oauth2service.json` with the list of authorized APIs.
Follow the directions to authorize the APIs; remember, you will login to the Admin console as a current
Google administrator.
```
gam user limited@domain.com update serviceaccount
```
If you disable a scope that was previously enabled, all of the remaining APIs will pass.
However, you should still go to the Admin console and update the client so that only the APIs
you've enabled are authorized.

## todrive Service Account access
If the limited user is going to use `todrive`, authorize these APIs:
```
Drive API - todrive
Gmail API - Send Messages - including todrive
Sheets API - todrive
```
These APIs are only used to process `todrive`, they do not grant access to other user's files/sheets.
If the limited user is allowed access to other user's files/sheets, authorize these APIs:
```
Drive API (supports readonly)
Sheets API (supports readonly)
```
## No Service Account access possible
If it is not possible to allow the limited user any service account access (this is not common),
perform these steps:

Make a `oauth2service.json` file in the `limited` subdirectory with a single line as follows:
```
{}
```

## Test Client and Service Account access on your computer

Issue various Gam commands to verify that the limited user has only the desired access.
Repeat previous steps as required. Once testing is complete, perform the following step
to prevent the limited user from creating/updating `oauth2.txt`.

Edit the `client_secrets.json` file in the `limited` subdirectory to have a single line as follows:
```
{}
```

## Install GAM on the limited users computer
Install GAM on the limited user's computer; it can be a different OS than your computer;
if asked by the installer, indicate:
* that you do not want to set up a project
* that you are performing an update

Make the necessary directories.
* Make the GAM configuration directory; this can be different than on your computer.
* Set the GAMCFGDIR environment variable to point to the GAM configuration directory.
* Make a subdirectory `gamcache` under the GAM configuration directory.
* Make a subdirectory `limited` under the GAM configuration directory.

Copy `gam.cfg` from your computer to the GAM configuration directory on the limited user's computer.
Edit `gam.cfg` 
* Remove any sections other than `[DEFAULT]` and `[limited]`
* If the GAM configuration directory on the limited users computer is different than that on yours, update these values in the [DEFAULT] section:
    * cache_dir
    * config_dir
* You may also want to update the GAM downloads directory:
    * drive_dir

Copy `client_secrets.json`, `oauth2.txt` and `oauth2service.json` from the `limited` subdirectory on your computer to the `limited` subdirectory on the limited user's computer.

## Test Client and Service Account access on the non-administrator computer

Issue various Gam commands to verify that the limited user has only the desired access.
If you need to make changes, make them on your computer and then re-copy `client_secrets.json`, `oauth2.txt` and `oauth2service.json` to the limited user's computer.

## Unselect limited section on your computer.
Once you have finished setting up authorizations for the limited user, you need to reset your `gam.cfg` to point to your default section or another section.
```
gam select default save
gam select <Section> save
```

## Delete old versions of GAM from Configured Apps

```
In the Admin console, go to Security/Access and Data Control/API Controls/MANAGE THIRD-PARTY APP ACCESS
Click Download list
Select Comma-separated values (.csv)
Click Download
Click Download CSV
The CSV file will be named: owl_apps.csv
Remove the rows of apps you want to keep.
Edit the column Access to UNCONFIGURED for those rows you want to remove.
Click Bulk update list
Click Attach CSV file
Locate owl_apps.csv
Click Upload
Click Upload
Click Confirm
```
