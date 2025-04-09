# Classroom - Guardians
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Create guardian invitations](#create-guardian-invitations)
- [Delete guardian invitations](#delete-guardian-invitations)
- [Display guardian invitations](#display-guardian-invitations)
- [Delete guardians](#delete-guardians)
- [Synchronize guardians](#synchronize-guardians)
- [Display guardians, indented keys and values](#display-guardians-indented-keys-and-values)
- [Display guardians, CSV format](#display-guardians-csv-format)

## API documentation
* [Classroom API - User Profile Guardian Invitations](https://developers.google.com/classroom/reference/rest/v1/userProfiles.guardianInvitations)
* [Classroom API - User Profile Guardians](https://developers.google.com/classroom/reference/rest/v1/userProfiles.guardians)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<GuardianItem> ::= <EmailAddress>|<UniqueID>|<String>
<GuardianItemList> ::= "<GuardianItem>(,<GuardianItem>)*"
<GuardianEntity> ::=
        <GuardianList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<StudentItem> ::= <EmailAddress>|<UniqueID>|<String>
<GuardianInvitationID> ::= <String>
<GuardianInvitationIDList> ::= "<GuardianInvitationId>(,<GuardianInvitationID>)*"
<GuardianInvitationIDEntity> ::=
        <GuardianInvitationIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<GuardianState> ::= complete|pending
<GuardianStateList> ::= "<GuardianState>(,<GuardianState>)*"
```
## Create guardian invitations
### Selected students, new style
```
gam <UserTypeEntity> create|add guardian|guardianinvite|inviteguardian <GuardianEntity>
```
### Selected students, old style
```
gam create guardian|guardianinvite|inviteguardian <EmailAddress> <StudentItem>
```
## Delete guardian invitations
### Selected students, new style
```
gam <UserTypeEnfity> cancel guardianinvitation|guardianinvitations <GuardianInvitationIDEntity>
gam <UserTypeEntity> delete guardian|guardians <GuardianEntity> invitations
gam <UserTypeEntity> clear guardian|guardians invitations
```
### Selected students, old style
```
gam cancel guardianinvitation|guardianinvitations <GuardianInvitationID> <StudentItem>
gam delete guardian|guardians <GuardianItem> <StudentItem> invitations
```
## Display guardian invitations
### All students
```
gam show guardian|guardians invitations [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [showstudentemails] [formatjson]
gam print guardian|guardians [todrive <ToDriveAttribute>*] invitations [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [showstudentemails] [formatjson [quotechar <Character>]]
```
The Classroom API does not return the student email address, use the `showstudentemails` option to get the student email address. This requires an additional API call per student.

### Selected students, new style
```
gam <UserTypeEntity> show guardian|guardians invitations [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [formatjson]
gam <UserTypeEntity> print guardian|guardians [todrive <ToDriveAttribute>*] invitations [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [formatjson [quotechar <Character>]]
```
### Selected students, old style
```
gam show guardian|guardians invitations [showstudentemails] [states <GuardianStateList>] [invitedguardian <EmailAddress>]
        [student <StudentItem>] [<UserTypeEntity>]
        [formatjson]
gam print guardian|guardians [todrive <ToDriveAttribute>*] invitations [showstudentemails] [states <GuardianStateList>] [invitedguardian <EmailAddress>]
        [student <StudentItem>] [<UserTypeEntity>]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays informations for all guardian invitations; you can limit the display with the following options.
* `states <GuardianStateList>` - Display guardian invitations with the specified state
* `invitedguardian <EmailAddress>` - Display guardians invitations with `<EmailAddress>`

## Delete guardians
### Selected students, new style
```
gam <UserTypeEntity> delete guardian|guardians <GuardianEntity> [accepted|invitations|all]
gam <UserTypeEntity> clear guardian|guardians [accepted|invitations|all]
```
* `accepted` - Delete accepted invitations
* `invitations` - Delete pending invitations
* `all` - Delete accepted and pending invitations

### Selected students, old style
```
gam delete guardian|guardians <GuardianItem> <StudentItem>
```

## Synchronize guardians
Gam deletes any pending guardian invitations and accepted guardians that are not in `<GuardianEntity>` and sends
invitations to the members in `<GuardianEntity>` that don't have a pending invitation or have not accepted.
```
gam <UserTypeEntity> sync guardian|guardians <GuardianEntity>
```
### Example
Your school SIS produces a CSV file, StudentGuardians.csv, each evening with two columns: Student,Guardian.
There is no indication as to what changes have been made from the night before. The following command will perform the
necessary changes.
```
gam csvkmd users StudentGuardians.csv keyfield Student datafield Guardian sync guardians csvdata Guardian
```

## Display guardians, indented keys and values
### All students
```
gam show guardian|guardians [accepted|invitations|all]
        [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [showstudentemails] [formatjson]
```
### Selected students, new style
```
gam <UserTypeEntity> show guardian|guardians [accepted|invitations|all]
        [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [formatjson]
```
### Selected students, old style
```
gam show guardian|guardians [accepted|invitations|all] [invitedguardian <EmailAddress>]
        [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [student <StudentItem>] [<UserTypeEntity>]
        [showstudentemails] [formatjson]
```
Use these options to control what information is displayed:
* `accepted` - Display accepted guardians; this is the default
* `invitations` - Display invitations
    * `states <GuardianInvitationStateList>` - Filter the invitations by state
* `all` - Display accepted guardians and pending invitations
    * `states <GuardianInvitationStateList>` - Filter the invitations by state

By default, Gam displays informations for all guardians; you can limit the display with the following option:
* `invitedguardian <EmailAddress>` - Display guardians with `<EmailAddress>`.

The Classroom API does not return the student email address, use the `showstudentemails` option to get the student email address. This requires an additional API call per student.

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

## Display guardians, CSV format
### All students
```
gam print guardian|guardians [todrive <ToDriveAttribute>*] [accepted|invitations|all]
        [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [showstudentemails] [formatjson [quotechar <Character>]]
```
### Selected students, new style
```
gam <UserTypeEntity> print guardian|guardians [todrive <ToDriveAttribute>*] [accepted|invitations|all]
        [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [formatjson [quotechar <Character>]]
```
### Selected students, old style
```
gam print guardian|guardians [todrive <ToDriveAttribute>*] [accepted|invitations|all]
        [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
        [student <StudentItem>] [<UserTypeEntity>]
        [showstudentemails] [formatjson [quotechar <Character>]]
```
Use these options to control what information is displayed:
* `accepted` - Display accepted guardians; this is the default
* `invitations` - Display invitations
    * `states <GuardianInvitationStateList>` - Filter the invitations by state
* `all` - Display accepted guardians and pending invitations
    * `states <GuardianInvitationStateList>` - Filter the invitations by state

By default, Gam displays informations for all guardians; you can limit the display with the following options.
* `invitedguardian <EmailAddress>` - Display guardians with `<EmailAddress>`.

The Classroom API does not return the student email address, use the `showstudentemails` option to get the student email address. This requires an additional API call per student.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
