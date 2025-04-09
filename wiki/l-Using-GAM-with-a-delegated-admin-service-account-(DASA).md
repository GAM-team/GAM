# Background
Delegated admin service accounts (DASA) are regular [GCP service accounts](https://cloud.google.com/iam/docs/service-accounts#what_are_service_accounts) that are granted a Workspace [delegated admin role](https://support.google.com/a/answer/33325). Service accounts have an email address like `gam-project-xuw-sp1-c4b@gam-project-xuw-sp1-c4b.iam.gserviceaccount.com` and are not part of a Workspace or Cloud Identity domain even if they are owned by a project in the domain’s organization. Service accounts cannot login to Google web services interactively, they are only able to call Google APIs.

# Advantages
* DASA accounts don’t require a Workspace or Cloud Identity license.
* DASA accounts don’t have a password login that can be phished or captured, they use [RSA private keys](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) to sign authentication requests which makes them very secure. You should however [rotate the key](https://jaylee.us/qwm) on a regular basis and keep it safe and secured!
* When a DASA account makes admin changes, the Admin audit log properly shows that the DASA account made the change. This is not the case when using domain-wide delegation.
* DASA accounts are granted [Google admin roles and permissions](https://support.google.com/a/answer/1219251) so that they are only able to perform the actions they are given permissions to perform. This is a simpler model than using both API scopes and admin roles to determine if GAM can perform an action. This achieves the [principal of least privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege) in a way that's not possible with domain-wide delegation.
* When using a DASA account, GAM does not need to worry about OAuth, scopes, token refresh, consent screens, etc. DASA accounts can [simply generate a signed JWT token](https://developers.google.com/identity/protocols/oauth2/service-account#jwt-auth) and use the JWT as the authorization header on Google API calls. This method is both faster and less complex than regular OAuth.

# Disadvantages
* DASA accounts can only be delegated admins. [If a task requires super admin rights to perform](https://support.google.com/a/answer/2405986#:~:text=Only%20super%20administrators%20can...), DASA accounts won’t be able to do it.
Not all Google Admin APIs work with DASA right now. For example, Google Vault API calls will fail with a DASA account.
* DASA is a delegated admin and can make Workspace / Cloud Identity admin API calls, it does not replace domain-wide delegation (DwD) when using GAM commands that interact with Gmail, Drive and Calendar user data.
* GAM support for DASA is still experimental and some things may fail. Please report your findings to the [GAM group](https://groups.google.com/g/google-apps-manager).

# GAM Setup Steps for DASA
1. I suggest starting with a fresh installation of GAM. You can always install it to a different directory and leave your existing GAM installation alone. DASA requires GAM 5.2 or newer. Please install the latest version from [git.io/gam-releases](https://git.io/gam-releases).

2. Follow the steps in `gam create project` up to the point where you are presented with a URL to the Cloud console to create a Client ID and secret. You don’t need to enter anything those, just press CTRL+C to quit the project creation.

3. GAM will have created a Google Cloud project for you and a service account. The service account is stored in oauth2service.json. If you look at the contents of this file you’ll see a couple important things:
   * client_email is the email address of your service account. Copy this address, we’ll use it to grant the service account delegated admin rights in your Workspace domain thus making it a DASA.
   * private_key is the cryptographic key which is used to sign authorization requests. Google has a copy of the public key and uses it to validate that the API call is being made by the DASA account. Keep oauth2service.json safe and private! It’s the only file needed to use the DASA account!

4. Now grant the service account delegated permissions. Head to [admin.google.com](https://admin.google.com/) > Account > Admin roles. If you don’t already have a delegated admin role created with the permissions you want the DASA account to have you can [use a system role or create your own](https://support.google.com/a/answer/33325).

**Pro tip** GAM now has the ability to create an admin role that has all delegate permissions (Super delegate which is not the same as a super admin) as well as an admin role that has all permissions that can be scoped to an OrgUnit (Super OU delegate). With a regular GAM setup, try running:
```
gam create adminrole "Super Delegate" privileges all
```
or to create an admin role with all privileges that can be scoped to an OrgUnit:
```
gam create adminrole "Super OU Delegate" privileges all_ou
```

5. Now assign your service account the delegated admin role. You’ll need the service account email address from #3. With the role opened in the admin console, click "Assign service accounts" and enter the email address.

6. Still in the admin console, head to Account > Account settings > Profile and record the Customer ID value. You’ll need this in the next steps.

7. Now in the GAM installation, create a file called `enabledasa.txt`. This file tells GAM to use the `oauth2service.json` file and the service account when making admin API calls rather than using `oauth2.txt`.

```
echo > /path/to/GAM/enabledasa.txt
```

8. Now we need to tell GAM which Workspace / Cloud Identity domain to use. Remember, the DASA account in oauth2service.json is not a member of your domain. We can tell GAM which domain to use with environment variables:

```
MacOS/Linux
export GA_DOMAIN=yourdomain.com
export CUSTOMER_ID=<ID from #6 above>

Windows command prompt:
set GA_DOMAIN=yourdomain.com
set CUSTOMER_ID=<ID from #6 above>

Windows PowerShell:
$env:GA_DOMAIN=yourdomain.com
$env:CUSTOMER_ID=<ID from #6 above>
```

Example values on Linux:

```
export GA_DOMAIN=example.com
export CUSTOMER_ID=C01wfv983
```

**Note** that you’ll need to have these values set every time you try to use DASA with GAM so you may want to create a batch file or add them to your login script.

9. Finally we can start running regular GAM admin commands. Try a few of these:

```
# Get info about a user:
gam info user a_user@yourdomain.com

# Add a member to a group
gam update group group@yourdomain.com add member a_user@yourdomain.com


# Create a user
gam create user newuser@yourdomain.com firstname Jerry lastname Seinfeld password p@ssw3rd
```

**Note** if you only gave the DASA account a groups admin role the user command is expected to fail. The delegated admin permissions and roles assigned to the GAM service account is what determines the commands they'll be allowed to use.

Good luck and as always, feedback in the [GAM group](https://groups.google.com/g/google-apps-manager) is very welcome!