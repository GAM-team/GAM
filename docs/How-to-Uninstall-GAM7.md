# Uninstalling GAM7

- [Get Project Info](#get-project-info)
- [Remove Client API access](#remove-client-api-access)
- [Remove Service Account API access](#remove-service-account-api-access)
- [Delete GAM Project](#delete-gam-project)
- [Linux and MacOS and Google Cloud Shell](#linux-and-mac-os-and-google-cloud-shell)
- [Windows](#windows)

## Get Project Info
```
gam version
```

Note the `Config File:` path to `gam.cfg`. In that folder will be a file `oauth2service.json`; look at its contents.
You want these two lines:
```
"client_id": "123691089974044844789"
"project_id": "gam-project-123-456-789"
```

## Remove Client API access
```
gam oauth delete
```

## Remove Service Account API access
In a browser, go to `https://admin.google.com`, login and go to the Security/API Controls/Domain-wide Delegation page.
Find the `Client ID` that matches the `client_id` value from `oauth2service.json`, hover over it and click `Delete`.	

## Delete GAM Project
In a browser, go to `https://console.cloud.google.com/cloud-resource-manager`, login. Find the `ID` that matches
the `project_id` value from `oauth2service.json`; click the three dots at the right end of the line and click `Delete`.
In the box that pops up, put the `project_id` value in ther `Project ID*` field and click `SHUT DOWN`

## Linux and MacOS and Google Cloud Shell

In these examples, the user home folder is shown as /Users/admin; adjust according to your
specific situation; e.g., /home/administrator.

This example assumes that GAM7 has been installed in /Users/admin/bin/gam7.
If you've installed GAM7 in another directory, substitute that value in the directions.

### Delete executable directory

```
rm -fr /Users/admin/bin/gam7
```

### Delete configuration directory

The default GAM configuration directory is /Users/admin/.gam; for more flexibility you
probably want to select a non-hidden location. This example assumes that the GAM
configuration directory will be /Users/admin/GAMConfig; If you've chosen another directory,
substitute that value in the directions.
```
rm -fr /Users/admin/GAMConfig
```

### Delete  working directory

This example assumes that the GAM working directory is be /Users/admin/GAMWork; If you've chosen
another directory, substitute that value in the directions.
```
rm -fr /Users/admin/GAMConfig
```

### Remove executable alias and GAM configuration export

Remove the following line:
```
alias gam="/Users/admin/bin/gam7/gam"
export GAMCFGDIR="/Users/admin/GAMConfig"
```
from these files based on your shell:
```
~/.bash_profile
~/.bashrc
~/.zshrc
~/.profile
```

## Windows

This example assumes that GAM7 has been installed in C:\GAM7; if you've installed
GAM7 in another directory, substitute that value in the directions.

### Delete executable directory

In File Explorer, delete the `C:\GAM7` folder.

### Delete configuration directory

The default GAM configuration directory is C:\Users\<UserName>\.gam; for more flexibility you
probably want to select a non user-specific location. This example assumes that the GAM
configuration directory will be C:\GAMConfig; If you've chosen another directory,
substitute that value in the directions.

In File Explorer, delete the `C:\GAMConfig` folder.

### Delete working directory

This example assumes that the GAM working directory will be C:\GAMWork; If you've chosen
another directory, substitute that value in the directions.

In File Explorer, delete the `C:\GAMWork` folder.

### Reset system path and GAM configuration directory
```
Start Control Panel
Click System
Click Advanced system settings
Click Environment Variables...
Click Path under System variables
Click Edit...
If C:\GAM7 is not on the Path, click Cancel and skip the next three steps
  Click C:\GAM7
  Click Delete
  Click OK
If GAMCFGDIR is not in System variables, skip the next two steps
  Click GAMCFGDIR
  Click Delete
Click OK
Click OK
Exit Control Panel
```

