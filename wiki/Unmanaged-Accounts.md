# Unmanaged Accounts
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Collections of Users](Collections-of-Users)
- [Definitions](#definitions)
- [Send an invitation](#send-an-invitation)
- [Cancel an invitation](#cancel-an-invitation)
- [Check status of an invitation](#check-status-of-an-invitation)
- [Display invitations status](#display-invitations-status)
- [Verify eligibility for invitation](#verify-eligibility-for-invitation)
- [Bulk verify eligibility for invitation](#bulk-verify-eligibility-for-invitation)

## API documentation
* [Cloud Identity API - User Invitations](https://cloud.google.com/identity/docs/reference/rest/v1beta1/customers.userinvitations)
* [Migrate Unmanaged Users](https://support.google.com/a/answer/6178640)
* [Find Unmanaged Users](https://support.google.com/a/answer/11112794)
* [Manage User Invitations](https://cloud.google.com/identity/docs/how-to/manage-user-invitations)

## Notes
Unmanaged accounts occur when a user registers for a personal Google account using an email address that matches your domain.
These accounts generally exist because a user has previously signed up for a personal Google Account using their work or educational email address. 
If your attempts to provision a managed account with the same primary email address, the conflict needs to be resolved. 

You can send an invitation to an unmanaged account asking them to join and be managed by your domain.

To use these features you must add the `Cloud Identity API` to your project and authorize
the appropriate scope: `Cloud Identity User Invitations API`.
```
gam update project
gam oauth create
```

## Definitions
```
<UserInvitationOrderByFieldName> ::=
        email|
        updatetime
```
## Send an invitation
```
gam send  userinvitation <EmailAddress>
```
## Cancel an invitation
```
gam cancel userinvitation <EmailAddress>
```

## Check status of an invitation
```
gam info userinvitation <EmailAddress> [formatjson]
```
By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display invitations status
This is the same list as found at: Admin Console/Users/More (top right)/Transfer tool for unmanaged users
```
gam show userinvitations
        [state notyetsent|invited|accepted|declined]
        [orderby email|updatetime [ascending|descending]]
        [formatjson]
```
By default, all invitations are shown; you can filter the invitations based on state.
* `state notyetsent` - The UserInvitation has been created and is ready for sending as an email
* `state invited` - The user has been invited by email
* `state accepted` - The user has accepted the invitation and is part of the organization
* `state declined` - The user declined the invitation

By default, invitations are show in ascending order by email address, use `orderby` to change the ordering.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.
```
gam print userinvitations [todrive <ToDriveAttribute>*]
        [state notyetsent|invited|accepted|declined]
        [orderby email|updatetime [ascending|descending]]
        [[formatjson [quotechar <Character>]]
```
By default, all invitations are shown; you can filter the invitations based on state.
* `state notyetsent` - The UserInvitation has been created and is ready for sending as an email
* `state invited` - The user has been invited by email
* `state accepted` - The user has accepted the invitation and is part of the organization
* `state declined` - The user declined the invitation

By default, invitations are show in ascending order by email address, use `orderby` to change the ordering.

By default, Gam displays the information as columns of fields.
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Verify eligibility for invitation
Verify whether a user account is eligible to receive an invitation (is an unmanaged account).

Eligibility is based on the following criteria:
* the email address is a consumer account and it's the primary email address of the account, and
* the domain of the email address matches an existing verified Google Workspace or Cloud Identity domain

If both conditions are met, the user is eligible/invitable.
```
gam check isinvitable <EmailAddress>
```
Gam displays the information as an indented list of keys and values.

## Bulk verify eligibility for invitation

```
gam <UserTypeEntity> check isinvitable [todrive <ToDriveAttribute>*]
```
Gam displays the invitable users in CSV format with the header `invitableUsers`.
