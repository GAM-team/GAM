- [Introduction](#introduction)
- [Download GAM](#download-gam)
  - [Windows Users](#windows-users)
  - [Mac and Linux Users](#mac-and-linux-users)
- [Install GAM](#install-gam)
  - [Windows Users](#windows-users-1)
  - [Mac and Linux Users](#mac-and-linux-users-1)
- [Uninstall GAM](#uninstall-gam)
  - [Cloud uninstallation](#cloud-uninstallation)
  - [Local uninstallation](#local-uninstallation)
    - [Windows Users](#windows-users-2)
    - [Mac and Linux Users](#mac-and-linux-users-2)
- [Configure GAM](#configure-gam)
  - [Create a Project](#creating-a-project)
  - [Authorize Admin Access](#authorize-admin-access)
  - [Authorize User Data and Settings Access](#authorize-user-data-and-settings-access)
- [Running GAM for the First Time](#running-gam-for-the-first-time)
- [More simple GAM commands](#more-simple-gam-commands)
- [Running GAM on Android or a Chromebook](#running-gam-on-android-or-a-chromebook)
- [Using GAM with a HTTP Proxy](#using-gam-with-a-http-proxy)
- [Using GAM with SSL / TLS MitM Inspection](#using-gam-with-ssl--tls-mitm-inspection)
- [Hostnames Used by GAM](#hostnames-used-by-gam)

# Introduction

GAM is a command line tool that allows administrators to manage many aspects of their Google Workspace (formerly G Suite / Google Apps) Account. This page provides simple instructions for downloading, installing and starting to use GAM.

GAM requires paid (or Education/non-profit) editions of Google Workspace. G Suite Legacy Free Edition has limited API support and not all GAM commands work.

While many GAM functions do not require domain administrative privileges, the setup does.

# Download GAM
## Windows Users
Head to the [Releases page](https://github.com/GAM-team/GAM/releases) and download the latest Windows MSI version of GAM. The filename should look like `gam-6.21-windows-x86_64.zip` (where 6.21 is the latest GAM version).

You then may proceed to [Install GAM](#windows-users-1).

## Mac and Linux Users
Open a shell prompt (Mac OS terminal app) and run:

```
bash <(curl -s -S -L https://gam-shortn.appspot.com/gam-install)
```

make sure you type the command exactly as above (best to use copy and paste). The script will download the latest release of GAM and [install it](#mac-and-linux-users-1).

If you're only _updating_ your GAM install instead run this command.
```
bash <(curl -s -S -L https://gam-shortn.appspot.com/gam-install) -l
```
# Install GAM
## Windows Users
[Download GAM](#windows-users), then run the MSI installer. By default, GAM will install to `C:\GAM` but you can change this to wherever you prefer. GAM will also be added to your path so you can run GAM even if you're not in the GAM folder. 

At the end of the MSI install process, GAM will open a command prompt to allow you to [setup a project and authorize GAM for admin management and user data/config access](#creating-a-project).

## Mac and Linux Users
[Download GAM](#mac-and-linux-users), then after the script has downloaded and installed GAM it will prompt you to [setup a project and authorize GAM for admin management and user data/config access](#creating-a-project).

# Uninstall GAM
Also see [Google Groups discussion](https://groups.google.com/g/google-apps-manager/c/N8XH-aRv7eE/m/tkvHuZSoCQAJ)

## Cloud uninstallation
Visit https://console.developers.google.com and delete any project you [Created for GAM](#creating-a-project).

## Local uninstallation
Uninstalling GAM **locally** depends on how you [installed it](#install-gam).

### Windows Users
[The GAM installer](#windows-users-1) contains an uninstaller, so just run it.

### Mac and Linux Users
Just delete [the installed GAM folder](#mac-and-linux-users-1).

For Linux users, then remove the line `gam() { "/home/user/bin/gam/gam" "$@" ; }` from the `~/.bashrc` file. 

# Configure GAM
To run any of the commands, GAM needs three things to complete the configuration:
* An API project which identifies your install of GAM to Google and keeps track of API quotas.
* Authorization to act as your Google Workspace Administrator.
* A special service account that is authorized to act on behalf of your users in order to modify user-specific settings and data such as Drive files, Calendars and Gmail messages and settings like signatures.

## Creating a Project
If GAM isn't already prompting you to create a project, you can run:
```
gam create project
```
to get started.
* GAM will prompt you for your Google Workspace admin email address. Enter the address of a super admin in your Google Workspace instance.
* Depending on your choices, either a website will open automatically or you'll be given a URL to go to to authorize GAM to create projects as the admin you specified. Click allow, copy the code if given one and switch back to the GAM window.
* GAM will now create the project, turn on necessary Google APIs for the project such as Drive, Gmail, Admin SDK, etc and finally create a service account.
* Next, you'll be asked to go to a URL and perform a few actions to create a "OAuth client ID". Follow the steps as provided and copy the client ID and secret back into GAM when prompted.
* Now you are asked to return to the browser window and make a change to your new service account. Once you've enabled Google Workspace Domain-wide Delegation, return to the GAM console window.

## Authorize Admin Access
* If you're not already prompted to authorize an admin as part of the install and configure process above, you can manually start the authorization by running `gam oauth create`. You'll be prompted for the email address of a super admin in your Google Workspace domain.
* You'll be presented a long list of APIs that GAM can use. By default, the most important APIs are selected. Unless you know what you are doing you can leave this selection as is and press C to continue to authorization.
* GAM will either open a web page for you or prompt you with a URL to visit in order to authorize admin access. Visit the URL and Authorize. You may need to copy a code from the browser back to the GAM window.
* That's it, GAM is now authorized to perform admin actions.

## Authorize User Data and Settings Access
* If you're not already prompted to authorize user data access as part of the install and configure process above, you can manually start the authorization process by running `gam user a_user@example.com check serviceaccount`.
* GAM will prompt you for the email address of a regular, non-admin user in your Google Workspace domain. Make sure this user has the Gmail, Drive and Calendar services enabled. If the service is not enabled, GAM will fail to connect to that service for the user.
* Now GAM will attempt to authenticate with each service / scope via the service account and acting on behalf of the user you specified above. It's expected that the first time through these attempts will FAIL.
  * Logon to the Admin console as a Super Admin 
  * Visit the URL GAM provided you
  * You should see a `Add a new Client ID` box
  * Make sure that `Overwrite existing client ID` is checked
  * Click `Authorize`
  * When the box closes you're done.
* Once you've authorized the Client name for the scopes in the admin console, re-run the check by running `gam user a_user@example.com check serviceaccount` again. It may take a few minutes after authorizing the scopes for all tests to PASS. If you've confirmed the Client name and scopes are listed properly on the website, grab a coffee and then try again.

That's it! GAM is now setup and ready to run.

**Note:** If you're getting a 401 error "client not found" from Google OAuth Authorization, please check that the client_secrets.json file inside your GAM directory matches your Google Workspace API client ID and customer secrets (recursive creation of projects creates new files on the filesystem instead of overwriting the default one).

# Running GAM for the First Time
Open a command prompt, shell or terminal on your computer. On Windows, you can do this by going to Start -> Programs -> Accessories -> Command Prompt. Now run:

```
gam info user
```

You'll be asked to specify which "scopes" you'd like the OAuth token to support. For now, select the last option to continue, all scopes will be selected. Next GAM will open up a web page in order for you to grant access to retrieve data and make changes to your Google Workspace account. Make sure you are logged in to a Google Workspace Administrator account before granting access. Once you've granted access, switch back to the command prompt window, GAM should already be working to display information about your user account.

Congrats, you're up and running with GAM.

# More simple GAM commands

Try the following GAM commands to get a feel for how the program works. I suggest creating a test user account for experimenting, or if you don't have a test account, use your account, we'll call our test user crashtestdummy in the examples below.

If you haven't already, we can just create our crashtestdummy account with GAM:
```html

gam create user crashtestdummy firstname Crash lastname "Test Dummy" password "BuckleUp"
```

We can give crashtestdummy an alias so that emails to idontwearseatbelts go to him:
```html

gam create alias idontwearseatbelts user crashtestdummy
```

We can create a group for crash test dummy's friends:
```html

gam create group test-dummies-united name "Test Dummies United" description "Support Group Against Plastic Abuse"
```

Crash test dummy likes Gmail but sometimes he prefers to use IMAP with his favorite email client, Thunderbird, let's enable IMAP for him:
```html

gam user crashtestdummy imap on
```

these are just a few examples, more are available under the topics to the right. Have fun!

# Running GAM on Android or a Chromebook
See [running GAM on a Chromebook](https://github.com/jay0lee/GAM/wiki/Chrome-OS-Installation) and [running GAM on Android](https://github.com/jay0lee/GAM/wiki/Android-Installation)

# Using GAM with a HTTP Proxy
GAM should be run on a server with direct access to talk to Google servers via the Internet. However, if you must push GAM traffic through an HTTP proxy this can be done by setting the `HTTP_PROXY / HTTPS_PROXY` environment variables.

```
export HTTP_PROXY="http://192.168.1.1:3128"
export HTTPS_PROXY="http://192.168.1.1:3128"
gam info domain
```
Additionally, GAM uses and requires the latest TLS 1.3 protocol by default. However some proxy/firewall solutions do not support TLS 1.3. In order to use GAM in these environments you may need to "lower your shields" by telling GAM to also allow the older TLS 1.2 protocol. This can be done by setting the environment variable `GAM_TLS_MIN_VERSION=TLSv1_2`.

# Using GAM with SSL / TLS MitM Inspection
By default, GAM verifies the Google HTTPS servers it talks to using public certificates signed by known certificate authorities. The authorities are listed in [this file](https://github.com/GAM-team/GAM/blob/main/src/cacerts.pem). GAM should be run on a server with direct access to talk to Google servers via the Internet, SSL / TLS inspection should NOT be used. If it must be used, you should assume that the SSL / TLS MitM proxy has complete access to your Google Workspace admin settings and user data (since it can see the unencrypted GAM API calls). You can tell GAM to check the SSL / TLS certificates against your own certificate authority file by setting the `GAM_CA_FILE` which should point to a PEM formatted file which contains your certificate authority.

Additionally, GAM uses and requires the latest TLS 1.3 protocol by default. However some proxy/firewall solutions do not support TLS 1.3. In order to use GAM in these environments you may need to "lower your shields" by telling GAM to also allow the older TLS 1.2 protocol. This can be done by setting the environment variable `GAM_TLS_MIN_VERSION=TLSv1_2`.

# Hostnames Used By GAM
You can use the command:
```
gam checkconn
```
to test GAM connectivity to hosts and diagnose any issues. GAM talks to the following hosts

| hostname | protocol | port | required? | how to disable | description |
|----------|----------|------|-----------|----------------|-------------|
| **api.github.com** | HTTPS | 443 | No | Manually download the GAM MSI/tar file. Create a file called `noupdatecheck.txt` | Used by GAM installer script at [git.io/install-gam](https://git.io/install-gam) and by GAM to check for updates. |
| **raw.githubusercontent.com** | HTTPS | 443 | No | Manually create the [projectapis.txt](https://github.com/GAM-team/GAM/blob/main/src/project-apis.txt) file. | Determines [which APIs need to be enabled](https://github.com/GAM-team/GAM/blob/main/src/project-apis.txt). |
| **gam-shortn.appspot.com** | HTTPS | 443 | No | Create a file called `noshorturls.txt` in the GAM folder. | Create short URL links for the very long Google authorization URLs that need to be copied and pasted. |
| **accounts.google.com** | HTTPS | 443 | Yes | N/A | required for OAuth authentication and refresh flows. |
| ***.googleapis.com** | HTTPS | 443 | Yes | N/A | Google APIs are hosted on domains like www.googleapis.com and admin.googleapis.com. If you can't allow a wildcard domain then start with www.googleapis.com, oauth2.googleapis.com and [the hosts listed here](https://github.com/GAM-team/GAM/blob/main/src/project-apis.txt). |

This list may not be exhaustive. To see what hosts a given GAM command is trying to talk to you can [enable HTTP logging](https://github.com/GAM-team/GAM/wiki/GAM-options-files#seeing-http-api-calls-made-by-gam).

The following hostnames are NOT accessed directly by GAM. However GAM will direct the admin to access the hostnames within a web browser. These Google services should be enabled and allowed for general user browser access. These Google services may also require additional hostnames to be allowed in order for the service to function.

| hostname | protocol | port | description |
|----------|----------|------|-------------|
| console.cloud.google.com | HTTPS | 443 | GAM directs the user to the Google Cloud Console in order to create an OAuth client ID. |
| admin.google.com | HTTPS | 443 | GAM directs the user to the Google Admin Console in order to authorize domain-wide delegation of the service account. |
| docs.google.com | HTTPS | 443 | GAM may generate a Google Sheet document and point the user to opening the document in their browser. |