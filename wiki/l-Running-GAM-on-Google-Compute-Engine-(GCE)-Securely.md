# Intro
GAM can run on a Linux or Windows Google Compute Engine (GCE) VM and use the attached service account to access Google Workspace APIs. The advantage of this configuration is that no service account private key is accessible to GAM directly and there is no risk of the key being stolen/lost. To use GAM on GCE with a service account:

1. Create a [GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

2. Create [a service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) which will be used by GAM. Continue steps 2 and 3 without granting the new service account any special access to the project and without granting users access to the service account.

3. Grant the service account rights to generate authentication tokens.
   * go to [console.cloud.google.com](https://console.cloud.google.com).
   * go to "IAM & Admin" > Service accounts
   * click on the service account you created (not the default service account).
   * copy the email address of your service account to the clipboard.
   * click on the Permissions tab.
   * click "Grant Access".
   * In the "New principals text box, paste the service account email you copied.
   * Give your service account the "Service Account Token Creator" and "View Service Accounts" roles.

4. [Create a Windows or Linux virtual machine](https://cloud.google.com/compute/docs/instances/create-start-instance).
   * You can choose a region physically close to you though you may be limited in your choices if you want to use the free tier.
   * GAM can run on the minimal `e2-micro` [free tier VM](https://cloud.google.com/free/docs/free-cloud-features#compute) though performance may suffer. If you are performing batch operations, raising the CPU count will help performance. If you have a very large and busy Workspace instance downloading reports or Drive file lists may require more RAM.
   * [DO NOT use the default service account](https://cloud.google.com/iam/docs/best-practices-service-accounts#single-purpose). Choose the service account you created above instead.
   * GAM does not use a significant amount of storage, unless you have specific storage needs the default disk size should suffice.
   * leave other VM instance settings at their defaults unless you know what you are doing.

5. Install GAM on the VM with the command:
```
bash <(curl -s -S -L https://git.io/gam-install) -l
```
the `-l` argument causes GAM to be installed and SKIP the normal setup wizard.

6. Logout and log back in to the VM, you should now be able to run GAM commands like:
```
gam version
```

7. Create the special `oauth2service.json` file GAM will use:
```
gam create signjwtserviceaccount
```
If you'd like, take a look at the generated ```oauth2service.json``` file with:
```
cat ~/bin/gam/oauth2service.json
```
you'll notice that while the file has some fields similar to a normal service account file, there is no `private_key` attribute containing an RSA private key.

8. Enable the Google APIs GAM will use:
```
gam enable apis
```
you are given the option to enable them automatically or manually. Automatic enablement will ask you to authenticate to GAM. You should authenticate as a user with rights to manage project APIs, probably a project owner. If you are not the project owner you can choose manual enablement and GAM will provide two or more URLs which you can send to the project owner. When the owner opens these URLs, they'll be prompted to enable all the APIs GAM needs.

9. GAM is now installed, the last steps are to grant GAM permissions to your Google Workspace domain.
   * If you want to manage user data, run ```gam user you@example.com check serviceaccount``` and follow the instructions to perform domain-wide delegation.
   * If you want to perform admin actions (manage users, groups, etc) [you can configure delegated admin service account (DASA)](https://github.com/GAM-team/GAM/wiki/Using-GAM-with-a-delegated-admin-service-account-(DASA)).