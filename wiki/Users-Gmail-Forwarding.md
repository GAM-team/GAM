# Users - Gmail - Forwarding
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Introduction](#introduction)
- [Manage forwarding addresses](#manage-forwarding-addresses)
- [Display forwarding addresses](#display-forwarding-addresses)
- [Manage forwarding](#manage-forwarding)
- [Display forwarding](#display-forwarding)
- [Examples](#examples)

## API documentation
* [Gmail API - Forwarding Addresses](https://developers.google.com/gmail/api/v1/reference/users.settings.forwardingAddresses)
* [Gmail API - Forwarding](https://developers.google.com/gmail/api/v1/reference/users.settings/updateAutoForwarding)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<FalseValues>= false|off|no|disabled|0
<TrueValues> ::= true|on|yes|enabled|1
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<EmailAddressList> ::= "<EmailAddress>(,<EmailAddress>)*"
<EmailAddressEntity> ::=
        <EmailAddressList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Users
```
## Introduction
An email address must be defined as a forwarding address before it can be used to forward.
A user can have multiple forwarding addresses, none or one of them can be active at a time.

## Manage forwarding addresses
```
gam <UserTypeEntity> add forwardingaddress|forwardingaddresses <EmailAddressEntity>
gam <UserTypeEntity> delete forwardingaddress|forwardingaddresses <EmailAddressEntity>
```
## Display forwarding addresses
```
gam <UserTypeEntity> info forwardingaddress|forwardingaddresses <EmailAddressEntity>
gam <UserTypeEntity> show forwardingaddress|forwardingaddresses
gam <UserTypeEntity> print forwardingaddress|forwardingaddresses [todrive <ToDriveAttribute>*]
```
## Manage forwarding
```
gam <UserTypeEntity> forward <FalseValues>
gam <UserTypeEntity> forward <TrueValues> keep|leaveininbox|archive|delete|trash|markread <EmailAddress>
```
* `keep|leaveininbox` - Leave the message in the INBOX.
* `archive` - Archive the message.
* `delete|trash` - Move the message to the TRASH.
* `markread` - Leave the message in the INBOX and mark it as read.

## Display forwarding
```
gam <UserTypeEntity> show forward|forwards
gam <UserTypeEntity> print forward|forwards [enabledonly] [todrive <ToDriveAttribute>*]

```
* `enabledonly` - Do not display users with forwarding disabled.

## Examples

This will show all active forwards to user@domain.com.
```
gam config auto_batch_min 1 csv_output_row_filter "forwardTo:regex:user@domain.com" num_threads 5 redirect csv ./UserActiveForwards.csv multiprocess all users print forwards enabledonly
```

This will show all possible forwards to user@domain.com.
```
gam config auto_batch_min 1 csv_output_row_filter "forwardingEmail:regex:user@domain.com" num_threads 5 redirect csv ./UserPossibleForwards.csv multiprocess all users print forwardingaddresses
```

Get a list of all users with forwarding enabled and send that list to a Google Sheet, and use multiprocessing to speed it up a little. Limiting the number of parallel threads to 5 to not be rate-limited by the API.

```
gam config auto_batch_min 1 num_threads 5 redirect csv ./AllForwards.csv multiprocess all users print forwards enabledonly todrive
```

Get the same type of list but instead based on a list of staff OUs, where the header in the local file StaffOUs.csv is OU.

```
gam config auto_batch_min 1 num_threads 5 redirect csv ./StaffForwards.csv multiprocess csvdatafile ous_ns StaffOUs.csv:OU print forwards enabledonly todrive
```

Show forwarding addresses for all users with forwarding on.
```
gam config auto_batch_min 1 num_threads 5 redirect csv ./FowardEnabledUsers.csv multiprocess redirect stdout - multiprocess redirect stderr stdout all users print forward enabledonly
gam redirect csv ./FowardEnabledUsersForwardingAddresses.csv multiprocess redirect stdout - multiprocess redirect stderr stdout csv ./FowardEnabledUsers.csv gam user "~User" print forwardingaddresses
```

Show forwarding addresses that are not your domain for all users with forwarding on.
```
gam config csv_output_row_drop_filter "forwardTo:regex:yourdomain.com" auto_batch_min 1 num_threads 20 redirect csv ./NonDomainForwards.csv multiprocess redirect stdout - multiprocess redirect stderr stdout all users print forward enabledonly
```