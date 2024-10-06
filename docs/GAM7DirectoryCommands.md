- [Users](#users)
  - [Creating a User](#creating-a-user)
  - [Update and Rename a User](#update-and-rename-a-user)
  - [Setting User Profile Details at Create or Update](#setting-user-profile-details-at-create-or-update)
  - [Setting Custom User Schema Fields at Create or Update](#setting-custom-user-schema-fields-at-create-or-update)
  - [Get User Info](#get-user-info)
  - [Delete a User](#delete-a-user)
  - [Remove a User from All Groups](#remove-a-user-from-all-groups)
  - [Undelete a User](#undelete-a-user)
  - [Transfer Drive Documents](#transfer-drive-documents)
- [Groups](#groups)
  - [Create a Group](#create-a-group)
  - [Update and Rename a Group](#update-and-rename-a-group)
  - [Add Members, Managers, Owners to a Group](#add-members-managers-owners-to-a-group)
  - [Update Members, Managers, Owners in a Group](#update-members-managers-owners-in-a-group)
  - [Sync Members, Managers, Owners to a Group](#sync-members-managers-owners-to-a-group)
  - [See Delivery Settings for a Member](#see-delivery-setings-for-a-member)
  - [Remove Users from a Group](#remove-users-from-a-group)
  - [Remove Members, Managers, Owners from a Group by Role](#remove-members-managers-owners-from-a-group-by-role)
  - [Get Group Info](#get-group-info)
  - [Delete a Group](#delete-a-group)
  - [Print Group Members](#print-group-members)
- [Email Aliases](#email-aliases)
  - [Creating an Alias for a User or Group](#creating-an-alias-for-a-user-or-group)
  - [Updating an Alias](#updating-an-alias)
  - [Retrieving Alias Information](#retrieving-alias-information)
  - [Deleting an Alias](#deleting-an-alias)
- [Determine if an Email Address is a User, Alias or Group](#determine-if-an-email-address-is-a-user-alias-or-group)
- [Domains](#domains)
  - [Add a Domain](#add-a-domain)
  - [Add a Domain Alias](#add-a-domain-alias)
  - [Changing the Primary Domain](#changing-the-primary-domain)
  - [Get Domain Info](#get-domain-info)
  - [Get Domain Alias Info](#get-domain-alias-info)
  - [Delete a Domain](#delete-a-domain)
  - [Delete a Domain Alias](#delete-a-domain-alias)
- [Mobile Devices](#mobile-devices)
  - [Perform Wipe, Account Wipe, Approve and Other Actions on Mobile Devices](#perform-wipe-approve-and-other-actions-on-mobile-devices)
  - [Get Info on a Mobile Device](#get-info-on-a-mobile-device)
  - [Delete a Mobile Device](#delete-a-mobile-device)
- [Chrome OS Devices](#chrome-os-devices)
  - [Updating Chrome OS Devices](#updating-chrome-os-devices)
  - [Send Commands to Chrome OS Devices](#send-commands-to-chrome-os-devices)
  - [Disable, Deprovision and Re-enable Chrome OS Devices](#disable-deprovision-and-re-enable-chrome-os-devices)
  - [Getting Info About a Chrome OS Device](#getting-info-about-a-chrome-os-device)
- [Resource Calendars](#resource-calendars)
  - [Creating a Resource Calendar](#creating-a-resource-calendar)
  - [Updating a Resource Calendar](#updating-a-resource-calendar)
  - [Retrieving Resource Calendar Information](#retrieving-resource-calendar-information)
  - [Deleting a Resource Calendar](#deleting-a-resource-calendar)
- [Buildings](#buildings)
  - [Creating a Building](#creating-a-building)
  - [Updating a Building](#updating-a-building)
  - [Retrieving Building Information](#retrieving-building-information)
  - [Deleting a Building](#deleting-a-building)
- [Features](#features)
  - [Creating a Feature](#creating-a-feature)
  - [Updating a Feature](#updating-a-feature)
  - [Deleting a Feature](#deleting-a-feature)

# Users
## Creating a User
### Syntax
```
gam create user <email address> firstname <First Name>
 lastname <Last Name> password <Password>
 [suspended on|off] [changepassword on|off]
 [gal on|off] [sha] [md5] [crypt] [nohash]
 [org <Org Name>] [recoveryemail <email> [recoveryphone <phone>]
```
Create a user account. firstname, lastname and password arguments are optional and should be single quoted if they contain spaces or special characters like ! or $ that the shell might try to interpret. If not set, firstname and lastname will default to "Unknown" and password will default to a random, 25-character string. Optional parameter "suspended on" creates the account but marks it as suspended (suspended off, AKA active is the default).  The optional parameter "changepassword on" will force the user to change their password after their first successful login (changepassword off is the default). The optional parameter "gal off" will hide the user from the Global Address List. This user will not be searchable in the Contacts Directory and will not autocomplete for other users composing emails unless they already have the user in their personal contacts (gal on is the default). The optional parameters sha, md5 and crypt indicate that the password is a hash of the given type. By default, if neither sha1, crypt or md5 are specified, GAM will hash the password using the [sha-512 crypt format](https://en.wikipedia.org/wiki/Crypt_(C)#SHA2-based_scheme) for added security. However, when hashes are sent, Google is unable to ensure password length and strength so it's possible to set passwords that do not conform to Google's length requirement this way. The optional parameter nohash disables GAM's automatic hashing of the password (password is still sent over encrypted HTTPS) so that Google can evaluate the length and strength of the password. Optional parameter org moves the user into the desired Organizational Unit. Optional parameters recoveryemail and recoveryphone set a user's [recovery email and/or phone number](https://support.google.com/accounts/answer/183723?visit_id=637014886336452513-3469660930&rd=1). recoveryphone must be the full international phone number including country code. At the same time a user account is created, rich profile information for the user such as phone numbers, organizational information, address and IM can be set. For details on profile fields, see Setting User Profile Details at Create or Update.

### Example
This example creates a user account. Note that the password is in single quotes to prevent the shell from acting on the special characters.

```
gam create user droth
 firstname "David Lee" lastname Roth
 password 'MightAsWellJump!'
```

This example creates a user who is hidden from the GAL, forced to change their password after first login.

```
gam create user jsmith gal off changepassword on
```
---

## Update and Rename a User
### Syntax
```
gam update user <email address>
 [firstname <First Name>] [lastname <Last Name>]
 [password <Password>]
 [username <New Username>]
 [email <New Email>]
 [gal on|off] [suspended on|off] [archived on|off]
 [sha] [md5] [crypt] [nohash]
 [changepassword on|off] [org <Org Name>]
 [recoveryemail <email> [recoveryphone <phone>]
```
Update a user account. firstname, lastname and password arguments are optional and should be single quoted if they contain spaces or special characters like $ or ! that may be interpreted by the shell. Username is optional and will rename the user's account name (and thus their email address). gal and suspended are optional and can be turned on or off. sha, crypt and md5 arguments are optional and indicate that the password specified is a hash of the given type. By default, if neither sha, crypt or md5 are specified, GAM will do a sha hash of the provided password and send the hash instead of the plain text password for an additional layer of security. However, when hashes are sent, Google is unable to ensure password length and strength so it's possible to set passwords that do not conform to Google's length requirement this way. The optional parameter nohash disable's GAM's automatic hashing of the password (password is still sent over encrypted HTTPS) so that Google can evaluate the length and strength of the password. changepassword is optional and indicates whether the user should be forced to change their password on next login. **Note that when `changepassword on` is specified, the user is immediately logged out.**
Optional parameter org allows the user to be moved into the desired Organization. Optional parameters recoveryemail and recoveryphone set a user's [recovery email and/or phone number](https://support.google.com/accounts/answer/183723?visit_id=637014886336452513-3469660930&rd=1). recoveryphone must be the full international phone number including country code.

At the same time a user account is created, rich profile information for the user such as phone numbers, organizational information, address and IM can be set. For details on profile fields, see Setting User Profile Details at Create or Update.

Google makes the following recommendations when renaming a user account:
  * Before renaming a user, it is recommended that you logout the user from all browser sessions and services. For instance, you can get the user on your support desk telephone line during the rename process to ensure they have logged out. The process of renaming can take up to 10 minutes to propagate across all services.
  * Google Talk will lose all remembered chat invitations after renaming. The user must request permission to chat with friends again.
  * When a user is renamed, the old username is retained as a alias to ensure continuous mail delivery in the case of email forwarding settings and will not be available as a new username. If you prefer not to have the alias in place after the rename, you'll need to [Delete the Alias](ExamplesProvisioning#Deleting_an_Alias)

### Example
This example updates a user account, setting the firstname, lastname and password and giving them admin access to the domain. Notice that the password is in single quotes to prevent the shell from acting on the !.
```
gam update user pmcartney
 firstname Paul lastname McCartney
 password 'LetItBe!' admin on
 suspended off
```

This example renames ljones to lsmith, also setting her last name to Smith (in the case of marriage)
```
gam update user ljones username lsmith lastname Smith
```

In this example, George Otfired is no longer at the company and Nate Ewguy has taken his position, we'll change the username, first and last name and password all in one stroke thus retaining George's old Google Apps mail, documents, etc
```
gam update user gotfired
 username newguy
 firstname Nate lastname Ewguy
 password HopeILastHere
```
---

## Setting User Profile Details at Create or Update
### Syntax
Line breaks are for readability, when run, command should be one long line.
```
gam create|update user <email address>
 [relation <relation type> <relation value>]
 [externalID <id type> <id value>]
 [phone type <phone type> value <phone value> primary|notprimary]
 [organization name <org name> title <org title>
  type <org type> department <org dept> symbol <org symbol>
  costcenter <org cost center> location <org location>
  description <org desc> domain <org domain>
  primary|notprimary]
 [address type <address type> unstructured <unstructered address>
  pobox <address pobox> extendedaddress <address extended address>
  streetaddress <address street address> locality <address locality>
  region <address region> postalcode <address postal code>
  countrycode <address country code>
  primary|notprimary]
 [im type <im type> protocol <im protocol> primary <im value>]
 [location type <location type> area <area> building <building> desk <desk> floor <floor> section <section> endlocation]
 [sshkeys expires <date> key <keyvalue>]
 [posixaccounts gecos <gecos> gid <numeric gid> uid <numeric uid> home <home path> primary true|false shell <shell> system <systemid> username <username> endposix]
```

Updates the rich profile information for a user at the same time the user is created or updated (single API call). These additional attributes can all be specified in one GAM command but are separated in the documentation for clarity. All attributes are optional and will show in the user's directory information assuming they have not been hidden from the Global Address List (gal off). The relation attribute allows you to set a relation of the user (e.g. manager). Relation value should be the relations email address in most cases. externalID allows you to specify other identification attributes or numbers for the user. Note that these are visible within the directory so private information like social security numbers or unique org identifiers should not be used. The phone attribute allows you to set phone numbers where the user can be reached. The organization attribute allows you to describe organizations which the member is a part of as well as their role and placement in the org, note that this is entirely unrelated to the Google Apps org setting. The address attribute allows you to set the addresses of a user. The address can be structured with each field separated or unstructured (one large address not broken into fields). The im attribute allows you to set instant messaging addresses for the user.

### Examples
This example will set multiple organizations, addresses, relations, managers and phones for the user.

```
gam update user jsmith@acme.org
 relation manager admin@acme.org
 relation spouse psmith@mymail.com
 externalID employeeID 1234567
 externalID "Frequent Flyer Number" ac321905
 phone type mobile value 321-654-0987 notprimary
 phone type work value 123-457-7890 primary
 organization name "Acme Inc." type "Work" title "Product Manager" department "Wafers Division"
  symbol  "ACME" costcenter 1234 location "Richmond Office" domain acme.org primary
 organization name "ACME Softball Team" type unknown title "Pitcher"
  description "2.3 ERA" notprimary
 im type work protocol gtalk primary jsmith@acme.org
 im type home protocol jabber jsmith@jabber.org
```

This example sets a desk location for the user
```
gam update user jsmith@acme.org
  location type desk building NYC-10 desk 2D118C floor 2 section D endlocation
```
---

## Setting Custom User Schema Fields at Create or Update
### Syntax
```
gam create|update user <email address>
 [schemaname.fieldname <fieldvalue>]
 [schemaname.multivaluefieldname multivalued <fieldvalue>]
```
Sets the given custom user schema field for a user. The schema must already be created. See the [create custom user schema command](Custom-Schemas#creating-a-custom-user-schema). If the schema field is multivalued, you must specify multivalued.

### Example
This example sets the id, grade and (multivalued) label fields of the StudentData custom schema for David Jones.
```
gam update user david.jones@acme.com
 StudentData.id 3434380
 StudentData.grade 7
 StudentData.labels multivalued BASEBALL_TEAM
 StudentData.labels multivalued SOCCER_TEAM
 StudentData.labels multivalued HONOR_ROLL
```
---

## Get User Info
### Syntax
```
gam info user <email address> [nogroups] [noaliases] [nolicenses] [noschemas] [schemas <SchemaNameList>] [userview] [skus <SKUIdList>]
```
Retrieve details about the given user. GAM will print out a summary of the user. By default, GAM will retrieve the user's group membership which results in an additional API call. If you do not require this information you can disable it by specifying `nogroups`. The optional `noaliases` parameter prevents GAM from printing out user email aliases. By default, GAM gets license information for the SKUs: Google-Apps-For-Business, Google-Apps-Unlimited, Google-Apps-For-Postini, Google-Apps-Lite, Google-Vault, Google-Vault-Former-Employee. If you want information about different SKUs, user the `skus <SKUIdList>` argument. The optional `nolicenses` parameter prevents GAM from retrieving and printing licenses for the user. The optional `noschemas` parameter prevents GAM from printing out custom schema information for the user. The optional `schemas` parameter accepts a list of schema names separated by commas and prints out only those schemas for the user. The optional `userview` parameter outputs only the information regular users are able to see about the given user, admin only fields are not returned. If you authenticate to GAM as a regular user, you can still run this command with the `userview` parameter and get back the GAL view of the user.

### Example
This example will show information on the user
```
gam info user rstarr

User: rstarr@acme.org
First Name: Ringo
Last Name: Starr
Is a Super Admin: False
Is Delegated Admin: False
Has Agreed to Terms: True
IP Whitelisted: False
Account Suspended: False
Must Change Password: False
Google Unique ID: 117553266811361050021
Customer ID: C02azef93
Mailbox is setup: True
Included in GAL: False
Creation Time: 2011-08-24T12:08:44.000Z
Last login time: 2013-05-08T16:58:54.000Z
Google Org Unit Path: /Google Users

IMs:
 protocol: gtalk
 im: rstarr@acme.org
 type: work
 primary: True

 protocol: jabber
 im: rstarr@jabber.org
 type: home

Addresses:
 countryCode: US
 locality: Richmod
 region: VA
 primary: True
 streetAddress: 321 Acme Rd
 postalCode: 03920
 type: work

 sourceIsStructured: False
 type: home
 formatted: 250 Robins Lane, Richmond, VA 03920

Organizations:
 domain: acme.org
 name: Acme Inc.
 title: Product Manager
 symbol: ACME
 customType:
 primary: True
 location: Richmond Office
 costCenter: 1234
 department: Wafers Division

 description: 2.3 ERA
 customType:
 name: ACME Softball Team
 title: Pitcher

Phones:
 type: mobile
 value: 321-654-0987

 type: work
 primary: True
 value: 123-457-7890

Relations:
 type: manager
 value: admin@acme.org

 type: spouse
 value: psmith@mymail.com

External IDs:
 type: employeeID
 value: 1234567

 type: Frequest Flyer Number
 value: ac321905

Email Aliases:
  ringo@acme.org
  ringo.starr@acme.org

Non-Editable Aliases:
  ringo@acme-alias.org
  ringo.starr@acme-alias.org

Custom Schemas:
 Schema: schoolschema
  id: 21760

 Schema: studentdata
  StudentNumber:
   250593210
  CreditCount: 4.0

 Schema: labels
  label:
   abc

Groups:
  2sv <2sv@acme.org>
  users <users@acme.org>
Licenses:
 Google-Apps-For-Business
 Google-Vault
```
---

## Delete a User
### Syntax
```
gam delete user <email address>
```
delete the given user's account.

### Example
This example deletes Pete Best's account
```
gam delete user pbest
```
---

## Undelete a User
### Syntax
```
gam undelete user <email address>
```
Undeletes a user account deleted in the last 20 days. In order to undelete a user, there must not be any other users or groups with conflicting primary or alias email addresses. See Google's [Restore a recently deleted user](http://support.google.com/a/bin/answer.py?hl=en&answer=1397578) documentation for more help.

---

## Remove a User from All Groups
### Syntax
```
gam user <email address> delete groups
```
Removes a user from all groups they are members of.

---
## Transfer Drive Documents
### Syntax
```
gam user <email address> transfer drive <email address>
```
Transfer the ownership of all of a user's drive documents and folders (preserving folder hierarchy). A folder is created in the target user's drive in the format `orig.owner@domain old files`.  This is particularly useful to ensure that shared drive documents and folders are preserved prior to deleting a user account.

### Example
This example transfers all of the drive files from jane.doe@example.com to archived.accounts@example.com
```
gam user jane.doe@example.com transfer drive archived.accounts@example.com
```
---
# Groups
## Create a Group
### Syntax
```
gam create group <group email> [name <Group Name>] [description <Group Description>]
```
create a group. Group Name and Description are optional and set the groups full name and description. Use quotes around them if they contain spaces. If the Google Groups for Business (user-managed groups) service is enabled for the Google Apps domain, additional groups security settings are available and can be set with the same GAM command as described on the [Groups Settings page](GAM3GroupSettings#Updating__Group_Settings).

### Example
This example creates a group:
```
gam create group mygroup@example.com
```

This example creates a group and [sets max message size](GAM3GroupSettings#Max_Message_Bytes) to 25mb
```
gam create group large_attachments@acme.org maxmessagebytes 25m
```
---

## Update and Rename a Group
### Syntax
```
gam update group <group email> [name <Group Name>]
 [description <Group Description>]
 [email <new email address>]
```
modifying a groups name, description or email address. When changing a group's email address, the new address must not already be in use.

When renaming a group, the group's old address is retained as an alias to ensure continuous mail delivery. (Note: verified on 2017-04-04.) If you prefer not to have the alias in place after the rename, you'll need to [Delete the Alias](ExamplesProvisioning#deleting-an-alias).


If the Google Groups for Business (user-managed groups) service is enabled for the Google Apps domain, additional groups security settings are available and can be set with the same GAM command as described on the [Groups Settings page](GAM3GroupSettings#Updating__Group_Settings).

### Example
This example modifies the group, changing it's name and description
```
gam update group beatles
 name "The Beatles Rock Band"
 description "British Invasion Band"
```

This example modifies the group, changing it's description and [allowing posters from other domains](GAM3GroupSettings#Allow_External_Members).
```
gam update group beatles
 name "The Beetles"
 allow_external_members true
```
---

## Add Members, Managers, Owners to a Group
### Syntax
```
gam update group <group email> add owner|member|manager [allmail|nomail|daily|digest] [notsuspended]
  {user <email address> | group <group address> | ou|ou_and_children <org name> | file <file name> | all users}
```
Add members, owners or managers to a group. You can specify a single user, a group of users, an org of users, a file with users (one per line), or "all users" for all users in Google Apps. The optional arguments allmail, nomail, daily and digest set the email delivery options for the group member. The `notsuspended` argument is used in conjunction with the `ou` and `ou_and_children` arguments to prevent suspended users in the specified Org Unit from being added to the group.

### Example
This example adds a manager to the group
```
gam update group beatles add manager user rstarr@beatles.com
```
This example adds a group (inside) into another group (outside) as nested member, the key is to describe inside as a user instead of group
```
gam update group outside add member user inside@example.com
```
This example adds all members in the Google Apps domain to a group
```
gam update group everyone add member all users
```
---

## Update Members, Managers, Owners in a Group
### Syntax
```
gam update group <group email>
 update owner|member|manager allmail|nomail|daily|digest
  {user <email address> | group <group address> | org <org name> | file <file name> | all users}
```
update members, owners or managers in a group. You can specify a single user, a group of users, an org of users, a file with users (one per line), or "all users" for all users in Google Apps. The specified users who are already a member of the group will have their membership type changed to the specified level. The optional allmail, nomail, daily and digest options set the delivery options for the group member.

### Example
This example makes a user who is currently a manager of a group an owner
```
gam update group beatles update owner user rstarr@beatles.com
```
---

## Sync Members, Managers, Owners to a Group
### Syntax
```
gam update group <group email> sync owner|member|manager [notsuspended] allmail|nomail|daily|digest
  {user <email address> | group <group address> | ou|ou_and_children <org name> | file <file name> | all users}
```

Adds/removes users from the specified group in order to sync membership with the specified entity. The sync operation should result in a minimal amount of API calls when some of the specified users are already in the group. When adding users, their membership type (member, manager, owner) will be set as specified in the command but existing members not being removed will not see their membership type change. The `notsuspended` argument is used in conjunction with the `ou` and `ou_and_children` arguments to prevent suspended users in the specified Org Unit from being added to the group and will cause them to be removed from the group if they are already members. The optional allmail, nomail, daily and digest options set the delivery options for the group member.

### Example
This example syncs the students@acme.edu group membership with the "Students" Org Unit in Google.
```
gam update group students@acme.edu sync member ou "Students"
```
This example syncs the faculty@acme.edu group membership with the "Faculty" Org Unit and sub orgs in Google.
```
gam update group faculty@acme.edu sync member ou_and_children "Faculty"
```
---

## See Delivery Settings for a Member
### Syntax
```
gam info member <memberemail> <groupemail>
```
Shows the settings for a given member of a group including their mail delivery setting.

### Example
This will show user@acme.com’s membership info including delivery_settings
```
gam info member user@acme.com sales@acme.com
```
----

## Remove Users from a Group
### Syntax
```
gam update group <group email>
 remove {user <email address> | group <group address> | org <org name> | file <file name> | all users}
```
Remove users from the given group. The users are completely removed from the group whether they were a member, owner or manager.

### Example
This command removes a user from a group.

```
gam update group students remove user grad@school.edu
```

this example removes all current members from a group
```
gam update group membersclub@acme.org remove group membersclub@acme.org
```
---

## Remove Members, Managers, Owners from a Group by Role
### Syntax
```
gam update group <group email> clear [owner] [manager] [member]
```
Remove users from the given group that have any of the specified roles. If no roles are specified, all members are removed, owners and managers are unaffected.

### Example
This command removes all managers from a group.

```
gam update group students@school.org clear manager
```

This command removes all current members from a group, owners and managers are unaffected.
```
gam update group membersclub@acme.org clear
```
---

## Get Group Info
### Syntax
```
gam info group <group email> [noaliases] [groups]
```
Retrieve information about a given group. The `noaliases` argument suppresses showing any aliases for the group. The `groups` argument shows the groups of which this group is a member.

### Example
This example will provide information about the group
```
gam info group beatles

 nonEditableAliases:
   beatles@acme-alias.org
   the-beatles@acme.org
 description:
 adminCreated: True
 email: test6@jay.powerposters.org
 aliases:
   the-beatles@acme.org
 id: 02ce457m25wwh7z
 name: beatles@acme.org
 allowExternalMembers: false
 whoCanJoin: CAN_REQUEST_TO_JOIN
 whoCanViewMembership: ALL_MANAGERS_CAN_VIEW
 defaultMessageDenyNotificationText:
 includeInGlobalAddressList: true
 archiveOnly: false
 isArchived: true
 membersCanPostAsTheGroup: true
 allowWebPosting: true
 messageModerationLevel: MODERATE_NONE
 replyTo: REPLY_TO_LIST
 customReplyTo:
 sendMessageDenyNotification: false
 messageDisplayFont: DEFAULT_FONT
 whoCanPostMessage: ALL_IN_DOMAIN_CAN_POST
 whoCanInvite: ALL_MANAGERS_CAN_INVITE
 spamModerationLevel: ALLOW
 whoCanViewGroup: ALL_MEMBERS_CAN_VIEW
 showInGroupDirectory: false
 maxMessageBytes: 25M
 allowGoogleCommunication: true
Members:
 member: rstarr@acme.org (user)
 member: gharrison@acme.org (user)
 owner: jlennon@acme.org (user)
 owner: pmccartney@acme.org (user)
```
---

## Delete a Group
### Syntax
```
gam delete group <group email>
```
Delete a given group.

### Example
This example will delete the group
```
gam delete group beatles
```
---

## Print Group Members
### Syntax
```
gam print group-members [todrive] ([domain <DomainName>] [member <EmailAddress>])|[group <EmailAddress>] [membernames] [fields <MembersFieldNameList>]

<MembersFieldName> ::= email|id|role|status|type
<MembersFieldNameList> ::= '<MembersFieldName>(,<MembersFieldName>)*'
```
Print the members of selected groups. By default, the membership of all groups in the primary domain are printed; you may select an alternative domain with the `domain` argument. The `member` argument selects only those groups than contain `<EmailAddress>` as a member.  The `group` argument selects a specific group. The `membernames` argument causes the full name of the member to be included in the output. The `fields` argument lets you specify the list of fields that you want in the output. The optional `todrive` argument will upload the CSV data to a Google Docs Spreadsheet file in the Administrators Google Drive rather than displaying it locally.

### Example
This example will print the membership of all groups that have jimsmith@domain.com as a member.
```
gam print group-members member jimsmith@domain.com
```
This example will print the membership of the technology@domain.com group showing member name information.
```
gam print group-members group technology@domain.com membernames
```
---

# Email Aliases
## Creating an Alias for a User or Group
### Syntax
```
gam create alias <alias> user|group|target <primary address>
```
Create an alias for the given user or group. user or group should be specified based on whether the target primary address is a user or group. If it's unknown which it is, target can be specified in which case both will be tried.

### Example
This example will create an alias for a user
```
gam create alias theking user epresley
```

This example will create an alias for a group
```
gam create alias the-beatles group beatles
```

This example will create an alias for target jimmy-hendrix whether it's a user or a group
```
gam create alias the-jimmy-hendrix target jimmy-hendrix
```
---

## Updating an Alias
### Syntax
```
gam update alias <alias> user|group|target <user name>
```
update an existing alias, changing the user or group it points to.

### Example
This example will update an existing alias, pointing it at another user
```
gam update alias ceo user sbalmer
```
---

## Retrieving Alias Information
### Syntax
```
gam info alias <alias>
```
retrieve information about the given alias.

### Example
This example will retrieve information about the alias
```
gam info alias president

Alias: president
User: bobama
```
---

## Deleting an Alias
### Syntax
```
gam delete alias <alias>
```
removes an alias.

### Example
This example will remove the alias *salesteam*
```
gam delete alias salesteam
```
---

# Determine if an Email Address is a User, Alias or Group
### Syntax
```
gam whatis <email address>
```
determines if the given email address is a user, alias, group or group alias and prints out information about the given resource.

### Example
This example looks up info@acme.com and determines that it is an alias.
```
gam whatis info@acme.com
info@acme.com is not a user...
info@acme.com is an alias

 Alias Email: info@acme.com
 User Email: jdoe@acme.com
```
---

# Domains
## Add a Domain
### Syntax
```
gam create domain <domain>
```
Adds the given domain as a secondary Google Apps domain.

### Example
This example adds secondary.com as a secondary domain.
```
gam create domain secondary.com
```
---
## Add a Domain Alias
### Syntax
```
gam create domainalias <domainalias> <parentdomain>
```
Adds a given domain as an alias of another given parent domain. The parent domain must be an existing primary or secondary domain (yes, alias domains can now point at secondary domains).

### Example
This example adds alias.com as an alias of primary.com
```
gam create domainalias alias.com primary.com
```
This example adds g.secondary.com as an alias of secondary.com
```
gam create domainalias g.secondary.com secondary.com
```
---

## Changing the Primary Domain
### Syntax
```
gam update domain <domain> primary
```
Makes the given domain the new primary domain. The given domain must already exist as a verified secondary domain. At the same time the domain is promoted to primary, the old primary domain will become a secondary domain. Alias domains that point at the current or new primary domains will continue to point at the same domain. Users, groups and aliases with addresses in either domain will not have their address changed.

**Note:** please read [Google's help article](https://support.google.com/a/answer/6301932?hl=en) for further considerations when changing your primary domain.
### Example
This example makes istanbul.com the new primary domain. constantinople.com which was the primary domain will become a secondary domain.
```
gam update domain istanbul.com primary
```
---

## Get Domain Info
### Syntax
```
gam info domain <domain>
```
Get information about a given domain. The domain must be a primary or secondary domain.

### Example
This example shows information about example.com
```
gam info domain example.com
verified: True
domainName: example.com
creationTime: 2014-12-19 10:05:24
isPrimary: True
```
---

## Get Domain Alias Info
### Syntax
```
gam info domainalias <domainalias>
```
Gets information about a given domain alias.

### Example
This example shows information about alias.com.
```
gam info domainalias alias.com
verified: False
creationTime: 2015-09-12 11:08:55
domainAliasName: alias.com
parentDomainName: primary.com
```
---

## Delete a Domain
### Syntax
```
gam delete domain <domain>
```
Deletes a given domain.

### Example
This example deletes the secondary domain secondary.example.com.
```
gam delete domain secondary.example.com
```
---

## Delete a Domain Alias
### Syntax
```
gam delete domainalias <domainalias>
```
Deletes a given domain alias.

### Example
This example deletes the domain alias g.example.com.
```
gam delete domainalias g.example.com
```
---

# Mobile Devices
## Perform Wipe, Approve and Other Actions on Mobile Devices
## Use the "resourceId" column as the mobile id
### Syntax
```
gam update mobile <resourceId>
 action wipe|account_wipe|approve|block|cancel_remote_wipe_then_activate|cancel_remote_wipe_then_block
```
Perform the given action on a mobile device. The resourceId must be specified and can be found by listing all mobile devices. wipe will tell the mobile device to perform a full data reset on next sync. account_wipe will only remove the user's Google account and associated data from the device. approve will allow the device to sync with Google Apps. block will block sync attempts from the device. cancel\_remote\_wipe\_then\_activate and cancel\_remote\_wipe\_then\_block will cancel a remote wipe and then set the status to approved or blocked accordingly.

### Example
This example will wipe the given device.

```
gam update mobile AFiQxQ8n8E7HjDsk13hHSoAIfF6NE78bUsfqjXkrLquNnBo5OyJrn7tR1bnKJmeaT7a_o_hElS1blK0nvNfxOCBnR-Wa5VE9VBbUOzEwK4w-Ik61wkrmtlo action wipe
```
---

## Get Info on a Mobile Device
### Syntax
```
gam info mobile <resourceId>
```

Print info about the given mobile device.

### Example
```
gam info mobile AFiQxQ8n8E7HjDsk13hHSoAIfF6NE78bUsfqjXkrLquNnBo5OyJrn7tR1bnKJmeaT7a_o_hElS1blK0nvNfxOCBnR-Wa5VE9VBbUOzEwK4w-Ik61wkrmtlo

 status: APPROVED
 lastSync: 2013-03-31T01:05:52.164Z
 name: John Smith
 firstSync: 2013-03-29T01:03:54.990Z
 resourceId: AFiQxQ8n8E7HjDsk13hHSoAIfF6NE78bUsfqjXkrLquNnBo5OyJrn7tR1bnKJmeaT7a_o_hElS1blK0nvNfxOCBnR-Wa5VE9VBbUOzEwK4w-Ik61wkrmtlo
 hardwareId: 
 deviceId: android946305472025
 type: GOOGLE_SYNC
 userAgent: Android/4.2.2-EAS-1.3,gzip(gfe)
 model: Unknown
 os: Unknown
 email: jsmith@acme.org
```
---

## Delete a Mobile Device
### Syntax
```
gam delete mobile <resourceId>
```

Deletes the given mobile device. Note that this does not break the device's sync, it simply removes it from the list of devices connected to the domain. If the device still has a valid login/authentication, it will be added back on it's next successful sync.

### Example
This example deletes the given mobile device.

```
gam delete mobile AFiQxQ8n8E7HjDsk13hHSoAIfF6NE78bUsfqjXkrLquNnBo5OyJrn7tR1bnKJmeaT7a_o_hElS1blK0nvNfxOCBnR-Wa5VE9VBbUOzEwK4w-Ik61wkrmtlo
```
---

# Chrome OS Devices
## Updating Chrome OS Devices
### Syntax
```
gam update cros <device id>
 [user <user info>] [location <location info>]
 [notes <notes info>] [ou <new org unit>] [assetid <asset id>]
```

Updates information about the given Chrome OS device. <device id> can be determined using the [gam print cros](GAM3CSVListings#Print_Chrome_OS_Devices) command. user, location, notes and assetid information is optional. ou is optional and allows the Chrome device to be moved to a new Google organizational unit, changing the policies that will be applied to the device.

### Example
This example will update the user, location, notes and asset id for the given Chromebook.

```
gam update cros 647cf127-ab85-4c2b-b07e-63ad1b705c19 user jsmith@acme.org location "Richmond Office" notes "tracking ID #329234" assetid 1234567890
```

This example moves the Chrome device into a OU configured for Kiosk / Public Session mode.
```
gam update cros 647cf127-ab85-4c2b-b07e-63ad1b705c19 ou "Kiosk Chromebooks"
```
----

## Send Commands to Chrome OS Devices
### Syntax
```
gam issuecommand cros <device id> command wipe_users|remote_powerwash|reboot|take_a_screenshot|set_volume <0-100> [times_to_check_status <0-1000+>] [doit]
```
Tells Google servers to send a remote command to the managed Chrome OS device. It's important to note that the device must be in a proper state to accept the command or a 400 error may be returned. For example, the reboot and take_a_screenshot commands only work if the device is configured in auto-start kiosk app mode. The wipe_users and remote_powerwash commands will erase all user data on the device and the remote_powerwash command will require that the device is physically reconnected to the WiFi network and re-enrolled before it can be managed again. These commands require the doit argument so that the admin confirms the potential loss of user data and management. Commands may take some time to execute on the remote device depending on the device state and connectivity to the Internet. It's strongly recommended that devices [be forced to auto-reenroll](https://support.google.com/chrome/a/answer/6352858?hl=en) before performing remote_powerwash to prevent the device from falling out of a managed state permanently. By default, GAM will wait 2 seconds and then check the status of the command before exiting. How many times GAM performs this status check can be configured with the times_to_check_status argument and is configurable from 0 to (some large number?). If the status reached EXPIRED, CANCELLED or EXECUTED_BY_CLIENT then the command has finished and no more checks will be performed.

### Examples
This example will remove user profile data from the device. Device will remain enrolled and connected. User data not synced to the Cloud including Downloads, Android app data and Crostini Linux VMs will be permanently lost.

```
gam issuecommand cros dd1d659a-0ea4-4e94-905e-4726c7a5f1e9 command wipe_users doit
```

This command will powerwash the device with serial number 143040348.

```
gam issuecommand cros query:id:143040348 command remote_powerwash times_to_check_status 10 doit
``` 

This command will powerwash all devices in the /StudentCarts OrgUnit at the end of the school year. Devices will need to be manually reconnected to WiFi which may mean entering a PSK. Use wipe_users if that's going to create to much work for you.

```
gam issuecommand cros "query:orgunitpath:/StudentCarts" command remote_powerwash times_to_check_status 0 doit
```
----

## Disable, Deprovision and Re-enable Chrome OS Devices
### Syntax
```
gam update cros <device id> action disable|reenable|deprovision_same_model_replace|deprovision_different_model_replace|deprovision_retiring_device [acknowledge_device_touch_requirement]
```
Perform the given action on an enrolled Chrome OS device. Action disable will lock the Chrome OS device and prevent user login and usage until re-enabled which is the preferred action for lost/stolen devices. Action reenable will re-enable a disabled device. Actions deprovision_same_model_replace, deprovision_different_model_replace, deprovision_retiring_device will deprovision the device with the given reason. ***Be aware that deprovisioning devices will impact your Chrome device license count. See Google's help article for explanation.***. Deprovisioning a device will remove enterprise management from the device and will require physical wipe and re-enrollment of the device if future management is desired. Deprovision actions require that the argument acknowledge_device_touch_requirement be specified in order to continue.

***Please be careful when deprovisioning devices, re-enrollment of Chrome OS devices can become a major physical task when dealing with hundreds/thousands of devices.***

### Example
This example disables a Chrome OS device
```
gam update cros 52ffe5f4-0152-4dd8-a399-a4595d04db91 action disable
```

This example deprovisions all devices in location Chrome Lab 5. The deprovision reason will be device retirement. 
```
gam print cros query "location:Chrome lab 5" | gam csv - gam update cros ~deviceId action deprovision_retiring_device acknowledge_device_touch_requirement
```
----

## Getting Info About a Chrome OS Device
### Syntax
```
gam info cros <device id> [allfields|full|basic] [nolists] [listlimit <Number>] <CrOSFieldName>* [fields <CrOSFieldNameList>] [downloadfile latest|<id>] [targetfolder <path>]
```
Print out information about the given Chrome OS device. The optional arguments `allfields/full` adds all fields to the output; the optional argument `basic` adds some essential fields to the output. The `<CrOSFieldName>*` and `fields <CrOSFieldNameList>` arguments give you the ability to select the specific fields you want output.

The full data for a Chrome OS device includes two repeating fields, recentUsers and activeTimeRanges, with multiple values per entry. Use the `listlimit <Number>` argument to limit each of the repeating fields to `<Number>` entries. The `nolists` argument eliminates these two fields from the output.

The optional downloadfile argument specifies that GAM should download log files uploaded by the device to Google. Currently only devices that auto-start kiosk apps upload their log files to Google. The optional argument targetfolder specifies the location where the downloaded file should be locally stored.

### Example
This example will print out information about the given Chromebook.
```
gam info cros 647cf127-ab85-4c2b-b07e-63ad1b705c19

 status: ACTIVE
 lastSync: 2013-03-28T23:40:00.014Z
 lastEnrollmentTime: 2013-02-23T20:03:35.332Z
 orgUnitPath: /Chromebooks
 notes: Jay's Chromebook
 serialNumber: HY3A91ECA01698
 annotatedUser: jsmith@acme.org
 bootMode: Verified
 deviceId: 647cf127-ab85-4c2b-b07e-63ad1b705c19
 platformVersion: 3701.62.0 (Official Build) beta-channel daisy
 osVersion: 26.0.1410.40
 firmwareVersion: Google_Snow.2695.117.0
```
---

# Resource Calendars
## Creating a Resource Calendar
### Syntax
```
gam create resource <id> <Common Name>
 [description <description>] [type <type>] [building <building>]
 [capacity <number>] [features <features>] [floor <floor>]
 [floorsection <floorsection>] [category <category>] [uservisibledescription <uservisibiledescription>]
```
create a calendar resource. id is the short name of the calendar and is used to identify it. Common Name is a longer more detailed name, use quotes around the common name if it contains spaces. The optional argument description allows you enter further details about the calendar resource. The optional argument type allows you to classify the resource. For details on using the type argument to organize your resource calendars, see Google's [guidance on organizing resource calendars](https://developers.google.com/google-apps/calendar-resource/#developing_a_naming_strategy_for_your_calendar_resources). The optional argument building specifies the [building](#buildings) where the resource is physically located. The optional argument capacity specifies the seating capacity of the resource. The optional argument features is a comma separated list of [features](#features) of the resource (e.g. tele-conference, CfM, Jamboard, whiteboard, etc). The optional arguments floor and floorsection specify the physical location of the resource within the building.

### Example
This example will create a calendar resource
```
gam create resource business-calendar "Acme Inc. Business Calendar"
```

This example will create a calendar with optional attributes
```
gam create resource ed101 "ED101 Conference Room" description "Conference Room containing conference phone, whiteboard and projector" type "Conference Room"
```
---

## Updating a Resource Calendar
### Syntax
```
gam update resource <id> [name <Name>]
 [description <Description>] [type <Type>] [building <building>]
 [capacity <number>] [features <features>] [floor <floor>]
 [floorsection <floorsection>] [category <category>] [uservisibledescription <uservisibiledescription>]
```
update a calendar resource. Required argument id is the short name of the calendar and is used to identify it. Optional argument name is the resources Common Name and allows you to change the resource calendar name that users see. The optional argument description allows you enter further details about the calendar resource. The optional argument type allows you to classify the resource. For details on using the type argument to organize your resource calendars, see Google's [guidance on organizing resource calendars](http://code.google.com/googleapps/domain/calendar_resource/docs/1.0/calendar_resource_developers_guide_protocol.html#naming_strategy).  The optional argument building specifies the [building](#buildings) where the resource is physically located. The optional argument capacity specifies the seating capacity of the resource. The optional argument features is a comma separated list of [features](#features) of the resource (e.g. tele-conference, CfM, Jamboard, whiteboard, etc). The optional arguments floor and floorsection specify the physical location of the resource within the building.

### Example
This will update the calendar resource, changing the common name, description and type
```
gam update resource board-room name "Board Room 1" description "Board Room #1 with 25 seats and projector" type "Conference Room"
```
---

## Retrieving Resource Calendar Information
### Syntax
```
gam info resource <id>
```
retrieve information for a calendar resource. Required argument id is the short name of the calendar and is used to identify it.

### Example
```
gam info resource ed101
 Resource ID: ed101
 Common Name: ED101 Conference Room
 Email: jay.powerposters.org_6564313031@resource.calendar.google.com
 Type: Conference Room
```
---

## Deleting a Resource Calendar
### Syntax
```
gam delete resource <id>
```
delete a calendar resource. Required argument id is the short name of the calendar and is used to identify it.

### Example
```
gam delete resource ed101
```

# Buildings
## Creating a Building
### Syntax
```
gam create building <name> [id <id>] [latitude <latitude>] [longitude <longitude>] [description <description>] [floors <floors>]
```
Creates a new building. The name argument specifies a name by which the building will be titled in the Calendar UI. The optional id argument specifies an ID by which the building can be managed with the API. If no ID is specified GAM will generate a random ID. The optional arguments latitude and longitude specify the physical location of the building. The optional argument floors specify a comma-separated lists of floors in the building. If floors are not specified the building will default to 1 floor.

### Example
This example creates a building at Google's NYC Office location.
```
gam create building "Google NYC 9th" id google-nyc-9th latitude 40.7416009 longitude -74.004487 description "Google NYC Main Building" floors 1,M,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16
```
----
## Updating a Building
### Syntax
```
gam update building <name or id:id> [name <name>] [latitude <latitude>] [longitude <longitude>] [description <description>] [floors <floors>]
```
Updates an existing building. The name or id argument specifies the building to update. When specifying an id make sure it is prefixed by "id:". Names are case-sensitive. The optional argument name specifies a new name for the building. The optional arguments latitude and longitude specify the physical location of the building. The optional argument floors specify a comma-separated lists of floors in the building.

### Example
This example updates the description of an existing building specified by id:
```
gam update building id:bffa1c34-8b43-4f16-bb39-c832a0358f96 description "Google NYC Office near Chelsea Market"
```
----

## Retrieving Building Information
### Syntax
```
gam info building <name or id:id>
```
Prints information about an existing building. The name or id argument specifies the building to update. When specifying an id make sure it is prefixed by "id:". Names are case-sensitive.

### Example
This example retrieves information for an existing building by name.
```
gam info building "Google NYC 9th"
```
----

## Deleting a Building
### Syntax
```
gam delete building <name or id:id>
```
Deletes an existing building. The name or id argument specifies the building to update. When specifying an id make sure it is prefixed by "id:". Names are case-sensitive.

### Example
This example deletes an existing building.
```
gam delete building id:google-nyc-9th
```
----

# Features
## Creating a Feature
### Syntax
```
gam create feature name <name>
```
Creates a feature named as specified.

### Example
This example creates a Jamboard feature.
```
gam create feature name Jamboard
```
----

## Updating a Feature
### Syntax
```
gam update feature <name> name <newname>
```
Updates an existing feature. Currently only the feature name can be updated.

### Example
This example renames the Jamboard feature to "Google Jamboard".
```
gam update feature Jamboard name "Google Jamboard"
```
----

## Deleting a Feature
### Syntax
```
gam delete feature <name>
```
Deletes an existing feature.

### Example
This example deletes the Jamboard feature.
```
gam delete feature Jamboard
```
----