# Running GAMADV-XTD3 securely on a Google Compute Engine
- [thanks](#thanks)
- [Introduction](#introduction)
- [Setup Steps](#setup-steps)

## Thanks

Thanks to Jay Lee for the original version of this document.

## Introduction
GAMADV-XTD3 can run on a Linux or Windows Google Compute Engine (GCE) VM and use the attached service account to access Google Workspace APIs. The advantage of this configuration is that no service account private key is accessible to GAMADV-XTD3 directly and there is no risk of the key being stolen/lost.

GAMADV-XTD3 version 6.50.00 or higher is required.

## Setup Steps
1. Create a [GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

2. Create [a service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) which will be used by GAMADV-XTD3.
   * Enter a value in Service account name
   * Enter text in Service account description
   * Click Create and Continue
   * Click Continue under Grant this service account access to project
   * Click Done under Grant users access to this service account
 
3. Grant the service account rights to generate authentication tokens.
   * Go to [console.cloud.google.com](https://console.cloud.google.com).
   * Go to "IAM & Admin" > Service accounts
   * Click on the service account you created (not the default service account).
   * Copy the email address of your service account to the clipboard.
   * Click on the Permissions tab.
   * Click "Grant Access".
   * In the "New principals text box, paste the service account email you copied.
   * Give your service account the "Service Account Key Admin", "Service Account Token Creator" and "View Service Accounts" roles.
   * Click Save

4. [Create a Windows or Linux virtual machine](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances).
   * Scroll down and start at Create a VM and attach the service account
   * Click Go to VM instances
   * Click Create Instance
   * Enter a value for Name
   * Configure Manage Tags and Labels
   * You can choose a region physically close to you though you may be limited in your choices if you want to use the free tier.
   * GAMADV-XTD3 can run on the minimal `e2-micro` [free tier VM](https://cloud.google.com/free/docs/free-cloud-features#compute) though performance may suffer. If you are performing batch operations, raising the CPU count will help performance. If you have a very large and busy Workspace instance downloading reports or Drive file lists may require more RAM.
   * Set Service account under Identity and AOI access
   * Choose the service account you created above instead.
   * GAMADV-XTD3 does not use a significant amount of storage, unless you have specific storage needs the default disk size should suffice.
   * Leave other VM instance settings at their defaults unless you know what you are doing.
   * Click Create

5. Install GAMADV-XTD3 on the VM
   * See: https://github.com/taers232c/GAMADV-XTD3/wiki/How-to-Install-Advanced-GAM

6. Logout and log back in to the VM, you should now be able to run GAMADV-XTD3 commands like:
```
gam version
```

7. Create the special `oauth2service.json` file GAMADV-XTD3 will use:
```
gam create gcpserviceaccount
```
If you'd like, take a look at the generated ```oauth2service.json``` file;
you'll notice that while the file has some fields similar to a normal service account file, there is no `private_key` attribute containing an RSA private key.

8. Enable the Google APIs GAMADV-XTD3 will use:
```
gam enable apis
```
You are given the option to enable them automatically or manually. Automatic enablement will ask you to authenticate to GAMADV-XTD3. You should authenticate as a user with rights to manage project APIs, probably a project owner. If you are not the project owner you can choose manual enablement and GAMADV-XTD3 will provide two or more URLs which you can send to the project owner. When the owner opens these URLs, they'll be prompted to enable all the APIs GAMADV-XTD3 needs.

9. Perform admin actions (manage users, groups, orgunits, Chrome devices, etc)
   * [Configure delegated admin service account (DASA)](https://github.com/taers232c/GAMADV-XTD3/wiki/Using-GAMADV-XTD3-with-a-delegated-admin-service-account); start at step 4.

10. Manage user data
   * Run ```gam user user@domain.com check serviceaccount``` and follow the instructions to perform domain-wide delegation.
