- [License Types](#license-types)
- [Adding a License for Users](#adding-a-license-for-users)
- [Updating a License for Users](#updating-a-license-for-users)
- [Deleting a License for Users](#deleting-a-license-for-users)
- [Sync a License for Users](#sync-a-license-for-users)

# License Types
GAM supports the licenses listed in the "Product SKU ID" column of [Google's Documentation](https://developers.google.com/admin-sdk/licensing/v1/how-tos/products). Additionally, GAM supports abbreviations for some of the SKU names:

| License SKU              | Abbreviation  |
|--------------------------|---------------|
| AppSheet Core | appsheetcore |
| AppSheet Enterprise Standard | appsheetstandard |
| AppSheet Enterprise Plus | appsheetplus |
| Assured Controls | assuredcontrols |
| Beyond Corp Enterprise | bce |
| Cloud Identity Free | cloudidentity |
| Cloud Identity Premium | cloudidentitypremium |
| Cloud Search | cloudsearch |
| G Suite Basic |  gsuitebasic |
| G Suite Business | gsuitebusiness |
| G Suite Business Archived | gsuitebusinessarchived |
| G Suite Enterprise Archived | gsuiteenterprisearchived |
| G Suite Enterprise for Education | gsuiteenterpriseeducation |
| G Suite Enterprise for Education (Student) | gsuiteenterpriseeducationstudent |
| G Suite Free/Standard | standard |
| G Suite Government | gsuitegov |
| G Suite Lite | gsuitelite |
| G Suite Message Security | postini |
| Google Chrome Device Management | cdm |
| Google Drive Storage 20gb | 20gb |
| Google Drive Storage 50gb | 50gb |
| Google Drive Storage 200gb | 200gb |
| Google Drive Storage 400gb | 400gb |
| Google Drive Storage 1tb | 1tb |
| Google Drive Storage 2tb | 2tb |
| Google Drive Storage 4tb | 4tb |
| Google Drive Storage 8tb | 8tb |
| Google Drive Storage 16tb | 16tb |
| Google Meet Global Dialing | meetdialing |
| Google Vault | vault |
| Google Vault Former Employee | vfe |
| Google Voice Starter | voicestarter |
| Google Voice Standard | voicestandard |
| Google Voice Premier | voicepremier |
| Google Workspace Business Starter | wsbizstart |
| Google Workspace Business Standard | wsbizstan |
| Google Workspace Business Plus | wsbizplus |
| Google Workspace Enterprise Essentials | wsentess |
| Google Workspace Enterprise Standard | wsentstan |
| Google Workspace Enterprise Plus | wsentplus |
| Google Workspace Essentials | wsess |

# Adding a License for Users
## Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users add license <sku>
```
Assign a license for the given SKU to a user or number of users.
## Example
This example gives members of the sales team a Vault license
```
gam group sales add license vault
```

This example gives users in the "Google Coordinate" OU a license for Google Coordinate
```
gam ou "Google Coordinate" add license Google-Coordinate
```

---


# Updating a License for Users
## Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users update license <sku> from <oldsku>
```
Update the license for the given users.

## Example
This example switches a user from Google Apps Message Security to Google Apps for Work licensing.
```
gam user heavydriveuser@acme.org update license gafw from gams
```

---


# Deleting a License for Users
## Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete license <sku>
```
Deletes the given SKU license for the users.

## Example
This example will remove the Coordinate license for all users.
```
gam all users delete license coordinate
```

---

# Sync a License for Users
## Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users sync license <sku>
```
Adds and removes licenses from users based on their inclusion in the specified user list. The inclusion list could be a Google Group, OrgUnit or local text file. Users who are not included in the user list and who have the license applied will have the given license type removed from their account. Users included in the user list and who do not have the license will have it added to their account.

## Example
This example will create two Google Groups named e4e and e4es, add currently licensed users to the groups and finally sync the license to the group. Because we use group_ns (group no suspended) in the last step, suspended users will have the license removed. Rerunning the final two commands on a recurring basis will keep the licenses aligned with the non-suspended group members.

```
gam create group e4e "G Suite Enterprise for EDU users"
gam create group e4es "G Suite Enterprise for EDU Student users"
gam update group e4e add members license gsuiteenterpriseeducation
gam update group e4es add members license gsuiteenterpriseeducationstudent
gam group_ns e4e sync license gsuiteenterpriseforeducation
gam group_ns e4es sync license gsuiteenterpriseforeducationstudent