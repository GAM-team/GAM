- [OAuth Key Management](#oauth-key-management)
  - [Selecting Which OAuth Key File to Use](#selecting-which-oauth-key-file-to-use)
  - [Display Info About the Current OAuth Token](#display-info-about-the-current-oauth-token)
  - [Revoking an OAuth Token](#revoking-an-oauth-token)
- [Service Account Management](#service-account-management)
  - [Rotating Service Account Keys](#rotating-service-account-keys)
  - [Listing Service Account Keys](#listing-service-account-keys)
  - [Deleting Service Account Keys](#deleting-service-account-keys)

# OAuth Key Management
## Selecting Which OAuth Key File to Use


### Syntax
```
Windows DOS Shell:
set OAUTHFILE=oauth.txt-mydomain.com

Windows PowerShell:
$env:OAUTHFILE="oauth.txt-mydomain.com"

Linux / OSX:
export OAUTHFILE=oauth.txt-mydomain.com
```
By default, GAM saves OAuth credentials to a file named oauth.txt. This works fine if you only have one G Suite instance to admin but if you have multiple, juggling this file can get complicated. If the environment variable OAUTHFILE is set, GAM will use that filename instead of oauth.txt for creating and reading OAuth authentication.

Note that the file name can be whatever you prefer, and the file *must* be stored in the same location as gam.exe or gam.py.

### Example
This DOS shell example switches between OAuth files for multi GAM runs.
```
set OAUTHFILE=oauth.txt-mydomain.com
gam info domain

G Suite Domain:  mydomain.com
Default Language: en
Organization Name: My Domain
Maximum Users: 15
...

set OAUTHFILE=oauth.txt-mypalsdomain.com
gam info domain

G Suite Domain:  mypalsdomain.com
Default Language: en
Organization Name: My Pal's Domain
Maximum Users: 5
...
```

## Display Info About the Current OAuth Token
### Syntax
```
gam oauth info
```
Displays information about the current OAuth token. Note that if the token was created with a version of GAM older than 2.5, it won't be possible to read what admin created the token, you'll need to revoke and recreate the token with 2.5 to see this information.

### Example
This example displays information about the current token
```
gam oauth info

OAuth File: /home/jay/bin/gam/oauth.txt-mydomain.com
G Suite Domain: mydomain.com
Client ID: 01010101010.apps.googleusercontent.com
Secret: XYZXXYZZZZZZZ
Scopes:
  https://apps-apis.google.com/a/feeds/groups/
  https://apps-apis.google.com/a/feeds/alias/
  https://apps-apis.google.com/a/feeds/policies/
  https://apps-apis.google.com/a/feeds/user/
  https://apps-apis.google.com/a/feeds/emailsettings/2.0/
  https://apps-apis.google.com/a/feeds/calendar/resource/
  https://apps-apis.google.com/a/feeds/compliance/audit/
  https://apps-apis.google.com/a/feeds/domain/
  https://www.googleapis.com/auth/apps/reporting/audit.readonly
  https://www.googleapis.com/auth/apps.groups.settings
  https://www.google.com/m8/feeds
  https://www.google.com/calendar/feeds/
  https://www.google.com/hosted/services/v1.0/reports/ReportingData
G Suite Admin: jay@mydomain.com
```

## Revoking an OAuth Token
### Syntax
```
gam oauth revoke
```
Revokes the current OAuth token (de-authorizing it from Google's end) and deletes the current OAuth file. **There is no undo from this operation!** Once revoked, you'll need to re-authorize using a G Suite admin account. Note that you can also revoke OAuth tokens from the [Google Accounts page](https://accounts.google.com/b/0/IssuedAuthSubTokens) of the admin who created the token. Tokens can also be revoked in the G Suite Control Panel by opening the security tab of the authorizing user.

### Example
This example revokes (destroys) and deletes current OAuth token
```
gam oauth revoke

This OAuth token will self-destruct in 3...2...1...boom!
```
# Service Account Management
GAM uses a service account and domain-wide delegation to manage G Suite user data such as Gmail settings/messages, Drive files and Calendars. GAM authenticates service account requests using a private key stored in `oauth2service.json`. The private key is roughly equivalent to a user password and should be kept secure on your machine running GAM. [Google recommends rotating service account keys on a routine basis](https://cloud.google.com/blog/products/gcp/help-keep-your-google-cloud-service-account-keys-safe).

## Rotating Service Account Keys
### Syntax
```
gam rotate sakey [local_key_size <1024|2048|4096>] [retain_none|retain_existing|replace_current]
     [algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048] [validity_hours <number>]
```
Rotates the private key used by GAM to authenticate the service account. This is the equivalent to changing a user's password. By default, GAM generates a new 2048 bit private key and uploads the public portion of the key to Google's servers so Google can authenticate requests signed by the service account. This is the most secure option because the private key never needs to leave the local machine running GAM. The optional argument local_key_size sets the size of the locally generated private key. 1024 is considered weak and not recommended. 2048 is the recommended default. 4096 is very strong but computational intensive and will slow down GAM operations that use service account authentication, especially on less powerful machines. The optional argument algorithm specifies that the new private key should be generated by Google and downloaded by GAM (after which Google forgets the private key). Generating the key locally is the recommended and default approach but this should generally be safe also. KEY_ALG_RSA_2048 is recommended as KEY_ALG_RSA_1024 is a weaker key. By default, GAM will revoke all existing USER_MANAGED keys for the service account after creating a new key. This is the recommended approach as it ensures only the new key can be used to authenticate the account. The optional arguments retain_none (default), replace_existing and retain_existing control how GAM handles revocation of existing keys. replace_existing will only revoke the private key stored in oauth2service.json before the rotate command was run, other keys will be left in place. retain_existing will leave all existing USER_MANAGED keys in place. Having more than one USER_MANAGED key in place is the equivalent of having multiple passwords to authenticate the same user account and is not recommended because it makes it more difficult to confirm the account is secure. Most users should simply keep the default retain_none setting. By default keys created by GAM never expire. The optional argument validity_hours sets the length of time during which the key will be valid and should be used when the [GCP constraints/iam.serviceAccountKeyExpiryHours organization policy](constraints/iam.serviceAccountKeyExpiryHours) is in use. Note that in order to account for system clock skew, GAM sets the key to be valid two minutes earlier than the current system time and thus it will also expire two minutes earlier.

### Examples
This example rotates the key for the existing `oauth2service.json`. You'll notice GAM commands continue to operate as normal after rotation but `oauth2service.json` will contain a new private_key value. It is recommended to run this command on a regular daily or weekly basis.
```
gam rotate sakey
```
This example has Google generate the new private key and send it to GAM (after which Google forgets the private key and only retains the public portion to validate requests signed by the private key).
```
gam rotate sakey algorithm KEY_ALG_RSA_2048
```
This example locally generates a 4096 bit private key which is considered more secure but will increase CPU utilization by GAM and time for commands to execute.
```
gam rotate sakey local_key_size 4096
```
----
## Listing Service Account Keys
### Syntax
```
gam show sakeys [all|system|user]
```
Shows information about the keys associated to the service account stored in `oauth2service.json`. By default, all keys are shown (system and user). System keys (SYSTEM_MANAGED) are generated and used by Google servers and generally do not need admin attention, GAM lists them for completeness sake. User keys (USER_MANAGED) should be rotated on a regular basis and in most cases there should only be a single USER_MANAGED key per service account.

### Example
This example lists all keys for the service account stored in `oauth2service.json`.
```
gam show sakeys
```
----
## Deleting Service Account Keys
### Syntax
```
gam delete sakeys <key_ids> [doit]
```
Revokes the listed keys for the service account. key_ids is a comma or space separated list of key ids to be revoked. By default, GAM will refuse to revoke the key id currently listed in `oauth2service.json` private_key_id because that is the key GAM is currently using and revoking it will break further operations. Add `doit` to the command if you are sure you want to revoke this key.

### Example
This example revokes the key id 0805fce8adbdba5cf88320fc34112ac38ee97fa4.
```
gam revoke sakeys 0805fce8adbdba5cf88320fc34112ac38ee97fa4
```
----