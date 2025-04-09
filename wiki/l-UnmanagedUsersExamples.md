- [Printing User Invitations](#printing-user-invitations)
- [Checking If An Address Is Invitable](#checking-if-an-address-is-invitable)
- [Sending User Invitations](#sending-user-invitations)
- [Cancelling User Invitations](#cancelling-user-invitations)
- [Evicting Unmanaged Users](#evicting-unmanaged-users)

## Printing User Invitations
### Syntax
```
gam print userinvitations [state accepted|declined|invited|not_yet_sent] [todrive]
```
prints the list of known unmanaged users which can be invited to become full Google Workspace users. This is the same list that appears in the [admin console's unmanaged users tool](https://support.google.com/a/answer/6178640). Note that it may take 48-72 hours before an account shows in this list. The optional argument state filters the results to only show accounts in the given state. The optional argument todrive creates a Google Spreadsheet of the results rather than outputting CSV data.

### Example
This example prints existing user invitations.
```
gam print userinvitations
```
----

## Checking If An Address Is Invitable
### Syntax
```
gam user <email>|users <emails>|csvfile:column <file> check isinvitable
```
Checks if the given email addresses are unmanaged accounts that can be invited to join Google Workspace. Only addresses that are invitable are output.

### Examples
This example reads in a csvfile, looks at the email column and checks each address to see if it's invitable.
```
gam csvfile localusers.csv:email check isinvitable
```
----

## Sending User Invitations
### Syntax
```
gam send userinvitation <email>
```
Emails the given address requesting it join the Google Workspace domain. The email must be invitable or an error will be returned. Multiple invitations can be sent be re-running the command (try not to spam users though). You do not need to cancel an invite before sending another.

### Example
This example invites Ahmed's account to join Google Workspace.
```
gam send userinvitation ahmed@acme.com
```
This example invites all addresses in a not_yet_invited state.
```
gam print userinvitations state not_yet_invited | gam csv - gam send userinvitation ~name
```
----

## Cancelling User Invitations
### Syntax
```
gam cancel userinvitation <email>
```
Cancels the invitation for the given address so that the user can no longer accept it even if they have the email. No notice is sent to the address.

### Example
This example cancel's Ahmed's invitation.
```
gam cancel userinvitation ahmed@acme.com
```
----

## Evicting Unmanaged Users
In some cases, it's preferable to evict unmanaged users from your Google Workspace domain namespace rather than inviting them to join. The eviction process renames the consumer user to a @gtempaccount.com address and user will be asked to rename on next login. Eviction is a one way process and cannot later be invited to join Workspace so be sure the accounts should not be a part of your organization.

To evict the accounts, we'll simply create a Google Group with the same email address as the unmanaged user and then delete the group. This is sufficient to evict.
### Examples
This example lists all unmanaged users and evicts them from your Google Workspace domain namespace.
```
gam print userinvitations > invitable.csv
gam csv invitable.csv gam create group ~email
gam csv invitable.csv gam delete group ~email
```
----