# Using GAM7 with a delegated admin service account
- [Thanks](#thanks)
- [Introduction](#introduction)
- [Advantages](#advantages)
- [Disadvantages](#disadvantages)
- [Setup Steps](#setup-steps)

## Thanks

Thanks to Jay Lee for the original version of this document.

## Introduction
Delegated admin service accounts (DASA) are regular [GCP service accounts](https://cloud.google.com/iam/docs/service-accounts#what_are_service_accounts) that are granted a Workspace [delegated admin role](https://support.google.com/a/answer/33325). Service accounts have an email address like `gam-project-xuw-sp1-c4b@gam-project-xuw-sp1-c4b.iam.gserviceaccount.com` and are not part of a Workspace or Cloud Identity domain even if they are owned by a project in the domain’s organization. Service accounts cannot login to Google web services interactively, they are only able to call Google APIs.

GAM7 version 6.50.00 or higher is required.

## Advantages
* DASA accounts don’t require a Workspace or Cloud Identity license.
* DASA accounts don’t have a password login that can be phished or captured, they use [RSA private keys](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) to sign authentication requests which makes them very secure. You should however [rotate the key](https://jaylee.us/qwm) on a regular basis and keep it safe and secured!
* When a DASA account makes admin changes, the Admin audit log properly shows that the DASA account made the change. This is not the case when using domain-wide delegation.
* DASA accounts are granted [Google admin roles and permissions](https://support.google.com/a/answer/1219251) so that they are only able to perform the actions they are given permissions to perform. This is a simpler model than using both API scopes and admin roles to determine if GAM7 can perform an action.
* When using a DASA account, GAM7 does not need to worry about OAuth, scopes, token refresh, consent screens, etc. DASA accounts can [simply generate a JWT token signed by their private key](https://developers.google.com/identity/protocols/oauth2/service-account#jwt-auth) and use the JWT as the authorization header on Google API calls. This method is both faster and less complex than regular OAuth.

## Disadvantages
* DASA accounts can only be delegated admins. [If a task requires super admin rights to perform](https://support.google.com/a/answer/2405986#:~:text=Only%20super%20administrators%20can...), DASA accounts won’t be able to do it.
Not all Google Admin APIs work with DASA right now. For example, Google Vault API calls will fail with a DASA account.
* DASA is a delegated admin and can make Workspace / Cloud Identity admin API calls, it does not replace domain-wide delegation (DwD) when using GAM7 commands that interact with Gmail, Drive and Calendar user data.
* GAM7 support for DASA is still experimental and some things may fail. Please report your findings to the [GAM group](https://groups.google.com/g/google-apps-manager).

## Setup Steps
1. Upgrade to at least GAM7 6.50.00. Best practice is to always use the [latest version of GAM7](https://github.com/GAM-team/GAM/wiki/How-to-Update-Advanced-GAM).

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

5. Now assign your service account the delegated admin role. You’ll need the service account email address from  step 3. With the role opened in the admin console, click "Assign service accounts" and enter the email address.

6. Still in the admin console, head to Account > Account settings > Profile and record the Customer ID value. You’ll need this in the next steps.

7. Now we need to tell GAM which Workspace / Cloud Identity domain to use. Remember, the DASA account in oauth2service.json is not a member of your domain. We can tell GAM7 which domain to use with gam.cfg variables:
The following variables in `gam.cfg` must be set when `enable_dasa` is True: `admin_email`, `customer_id` and `domain`,
`customer_id` may not be set to `my_customer`.


```
gam config enable_dasa true admin_email admin@domain.com customer_id <Customer ID from step 6> domain domain.com save
```
