# Users - Backup Verification Codes
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage backup verification codes](#manage-backup-verification-codes)
- [Display backup verification codes](#display-backup-verification-codes)

## API documentation
* [Directory API - Verification Codes](https://developers.google.com/admin-sdk/directory/reference/rest/v1/verificationCodes)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Manage backup verification codes
```
gam <UserTypeEntity> update backupcodes|verificationcodes
gam <UserTypeEntity> delete|del backupcodes|verificationcodes
```
You will get the following error message for any user that is suspended:
```
User: user@domain.com, Backup Verification Codes Not Updated: User is suspended. You must unsuspend to process backupcodes
User: user@domain.com, Backup Verification Codes Not Deleted: User is suspended. You must unsuspend to process backupcodes
```
## Display backup verification codes
```
gam <UserTypeEntity> show backupcodes|backupcode|verificationcodes

```
Gam displays the information as an indented list of keys and values.

Exit Status of 0 indicates no errors, and backup codes are sent to stdout.

Exit status of 60 indicates no errors, and that no backup codes are available for this user.
```
gam <UserTypeEntity> print backupcodes|verificationcodes [todrive <ToDriveAttributes>*]
        [delimiter <Character>] [countsonly]
```
GAM displays the information in CSV form.

* `delimiter <Character>` - Separate `verificationCodes` entries with `<Character>`; the default value is `csv_output_field_delimiter` from `gam.cfg`.
* `countsonly` - Display only the number of available backup codes but not the codes themselves.
