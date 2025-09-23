GAM setup with minimal GCP permissions.

- GCP Admin can create a project for the Workspace / GAM admin.

- GAM admin needs following permissions on the created project resource:

```
clientauthconfig.brands.create
clientauthconfig.brands.update
clientauthconfig.clients.create
clientauthconfig.clients.createSecret
clientauthconfig.clients.delete
clientauthconfig.clients.get
clientauthconfig.clients.getWithSecret
clientauthconfig.clients.list
clientauthconfig.clients.listWithSecrets
clientauthconfig.clients.update
iam.serviceAccountKeys.create
iam.serviceAccounts.create
iam.serviceAccounts.list
iam.serviceAccounts.setIamPolicy
oauthconfig.testusers.get
oauthconfig.verification.get
resourcemanager.projects.get
serviceusage.services.enable
serviceusage.services.get
serviceusage.services.list
```
Reasons for permission by service:
| Service(s) | Reason |
|---------|--------|
| clientauthconfig and oauthconfig | Manage the [OAuth Consent Page](https://developers.google.com/workspace/guides/configure-oauth-consent) |
| iam | Manage service accounts and their keys |
| serviceusage | Enable Google API services |
| resourcemanager | Read basic project info |

- Once GAM admin has rights to the new project they can complete setup with:
```
gam use project
```
admin will be prompted for the project ID.