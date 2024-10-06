- [About Google Apps Audits](#about-google-apps-audits)
- [Audit Monitors](#audit-monitors)
  - [Create a Audit Monitor](#create-a-audit-monitor)
  - [List Audit Monitors](#list-audit-monitors)
  - [Delete an Audit Monitor](#delete-an-audit-monitor)
- [Managing the GPG Key](#managing-the-gpg-key)
  - [Updating the GPG Key on Google's Servers](#updating-the-gpg-key-on-googles-servers)
- [User Account Activity](#user-account-activity)
  - [Request an Account's Activity](#request-an-accounts-activity)
  - [Retrieving Current Status of Activity Request(s)](#retrieving-current-status-of-activity-requests)
  - [Downloading the Results of a Completed Activity Request](#downloading-the-results-of-a-completed-activity-request)
  - [Deleting a Completed Activity Request](#deleting-a-completed-activity-request)
- [User Mailbox Exports](#user-mailbox-exports)
  - [Request an Export of a User's Mailbox](#request-an-export-of-a-users-mailbox)
  - [Retrieving Current Status of Export(s)](#retrieving-current-status-of-exports)
  - [Downloading the Results of a Completed Export Request](#downloading-the-results-of-a-completed-export-request)
  - [Deleting a Completed Export Request](#deleting-a-completed-export-request)
- [Using GPG with Audits](#using-gpg-with-audits)
  - [Creating/Uploading a GPG Key](#creatinguploading-a-gpg-key)
    - [Downloading GPG](#downloading-gpg)
      - [Windows Users](#windows-users)
      - [Linux Users](#linux-users)
      - [Mac Users](#mac-users)
    - [Creating/Uploading the Key](#creatinguploading-the-key)
    - [Uploading the GPG Key](#uploading-the-gpg-key)
  - [Decrypting Downloaded Files with GPG](#decrypting-downloaded-files-with-gpg)

# About Google Apps Audits
```diff
- Most of the Email Audit API's functionality has been replaced/improved upon
- by Google's Vault and email routing functionality. GAM 3.8+ no longer supports
- the email audit commands listed below. If you need to use these audit commands,
- use GAM 3.72 or older. No support is provided for these commands going forward.
```

# Audit Monitors
## Create a Audit Monitor
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit monitor create <source user> <destination user> [begin <begin date>] [end <end date>]  [incoming_headers]
  [outgoing_headers] [nochats] [nodrafts] [chat_headers] [draft_headers]
```
create an audit monitor for the source user. All Mail to and from the source user will be forwarded to the destination user. By default, the audit will begin immediately and last for 30 days. Optional parameters begin and end can set the start and end times. Both parameters must be in the future with end being later than begin, the format is "YYYY-MM-DD hh:mm". Optional parameters, incoming\_headers and outgoing\_headers configure the audit to not send the given message's full email body but just the message headers. By default, the audit will also forward the source user's Chats and saved message Drafts. The optional parameters nochats and nodrafts disable forwarding of these type of messages. The optional parameters chat\_headers and draft\_headers tell the audit to only send the headers of the given messages instead of the full message body.

Only one audit is possible per a source and destination user combo. Creating a new audit with the same source and destination of an existing audit will overwrite the settings of the current of the existing audit.

### Example
This example configures an audit of the source user, forwarding full copies of all incoming, outgoing, chat and draft messages to the destination user. The audit will start immediately and terminate in 30 days time
```
gam audit monitor create jsmith fthomas
```

This example will start the audit on the given date and end it on the given date. Only message headers of each type will be sent to fthomas
```
gam audit monitor create jsmith fthomas begin "2010-07-15 12:00" end "2011-07-15 12:00"
  incoming_headers outgoing_headers chat_headers draft_headers
```

This example will not capture drafts or chats
```
gam audit monitor create jsmith fthomas nochats nodrafts
```

---


## List Audit Monitors
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit monitor list <source user>
```
shows the current audit monitors for the user source user.

This example will list the current monitors for the user jsmith
```
gam audit monitor list jsmith

jsmith has the following monitors:

 Destination: fthomas
  Begin: 2010-07-04 12:00
  End: 2010-08-05 12:00
  Monitor Incoming: HEADER_ONLY
  Monitor Outgoing: HEADER_ONLY
  Monitor Chats: NONE
  Monitor Drafts: NONE
```

---


## Delete an Audit Monitor
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit monitor delete <source user> <destination user>
```
delete the audit monitor for the given source user / destination user combo.

This example deletes the monitor that is sending all jsmith's mail to fthomas
```
gam audit monitor delete jsmith fthomas
```

---


# Managing the GPG Key
## Updating the GPG Key on Google's Servers
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit uploadkey
```
updates the public GPG key that Google's servers use to encrypt Audit Activity and Export files. The key should be provided on Standard Input. See [Using GPG with Audits](ExamplesAccountAuditing#using-gpg-with-audits) for more details on GPG keys.

This example tells GPG to print the key on standard output and gam reads the key on standard input
```
gpg --export --armor | gam audit uploadkey
```

---


# User Account Activity
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
## Request an Account's Activity
```
gam audit activity request <user>
```
request the account activity of the given user. Requests can take several hours/days to be completed by Google's servers. GAM will print out a request ID which can be used to monitor the progress of the request (see Retrieving Request Status below). Note that before requesting an account's activity, a GPG key should be uploaded to Google Servers. See [Using GPG with Audits](ExamplesAccountAuditing#Using_GPG_with_Audits) for more details on GPG keys. Failure to upload a key will result in the activity request always getting a status of ERROR.

This example creates a request for the user's activity
```
gam audit activity request jsmith
```

---


## Retrieving Current Status of Activity Request(s)
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit activity status [user] [request_id]
```
get the current status of existing account activity requests. Optionally, a user and request\_id can be specified to limit the retrieval to a single request.

This example retrieves the status of all current activity requests
```
gam audit activity status
```

---


## Downloading the Results of a Completed Activity Request
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit activity download <user> <request_id>
```
download the results of an activity request that has a status of COMPLETED. The required parameters user and request\_id specify which request to download. The GPG encrypted activity file will be saved to a file named with the format activity-username-request\_id-1.txt.gpg and should be decrypted with GPG.

This example downloads the encrypted activity log of the COMPLETED request
```
gam audit activity download jsmith 234342
```

---


## Deleting a Completed Activity Request
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit activity delete <user> <request_id>
```
delete the completed activity request for the given user. User and Request ID are required parameters.

This example deletes the completed activity request for the user
```
gam audit activity delete jsmith 234342
```

---


# User Mailbox Exports
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
## Request an Export of a User's Mailbox
```
gam audit export request <user> [begin <Begin Date>] [end <End Date>] [search <Search Query>] [headersonly] [includedeleted]
```
request an export of all mail in a user's mailbox. Optional parameters begin and end date specify the range of messages that should be included in the export and should be of the format "YYYY-MM-DD hh:mm". By default, export begins at account creation and ends at the time of the export request. Optional parameter search, specifies a search query defining what messages should be included in the export. The query parameters are the same as those used in the Gmail interface and described [here](http://mail.google.com/support/bin/answer.py?hl=en&answer=7190). Optional parameter headersonly specifies that only the message headers should be included in the export instead of the full message body. Optional parameter includedeleted specifies that deleted messages should also be included in the export.

Note that before requesting an export of an account, a GPG key should be uploaded to Google's Server. See [Using GPG with Audits](ExamplesAccountAuditing#Using_GPG_with_Audits) for more details on GPG keys. Failure to upload a key will result in the export request always getting a status of ERROR.

This example requests an export of all of a user's mail including deleted messages
```
gam audit export request jsmith includedeleted
```

This example requests an export of all of a user's mail for a 30 day range including deleted
```
gam audit export request jsmith begin "2010-06-01 00:00" end "2010-07-01 00:00" includedeleted
```

This example requests an export of all of a user's mail that has the word secret in the message subject
```
gam audit export request jsmith search "subject:secret"
```

---


## Retrieving Current Status of Export(s)
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit export status [user] [request_id]
```
retrieve the status of current export requests. If the optional parameters user and request\_id are specified, only the status of the one request will be retrieved, otherwise all current requests' status will be retrieved.

This example shows the status of all current export requests
```
gam audit export status
```

---


## Downloading the Results of a Completed Export Request
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit export download <user> <request_id>
```
download the encrypted results of a completed export request. The required parameters user and request\_id specify which request's results should be downloaded. The encrypted files are saved with file names of export-username-request\_id-file\_number.mbox.gpg. If a file already exists on the hard drive, GAM will not re-download that file. GAM does not verify that the existing local file is complete, only that it exists. Thus if a download is interrupted, delete the partially downloaded file and start the process again, GAM will then skip over the files that have finished downloading. After they have been downloaded, they can be decrypted with GPG and then viewed with a mail client like Thunderbird.

This example downloads the completed export request for jsmith
```
gam audit export download jsmith 344920
```

---


## Deleting a Completed Export Request
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
```
gam audit export delete <user> <request_id>
```
delete the completed export request. The required parameters user and request\_id specify which request to delete.

This example deletes the export request for the given user
```
gam audit export delete jsmith 344920
```


# Using GPG with Audits
## Creating/Uploading a GPG Key
**This command is deprecated and will not work in GAM 3.8+**. [Details](#about-google-apps-audits)
### Syntax
Google's Servers use GPG to encrypt files that you request via the Audit API for account activity and mailbox export. Before you can successfully request a user account activity log or mailbox export, you need to create a GPG and upload it to Google's Servers for their use.
### Downloading GPG
#### Windows Users
A Windows version of GPG can be downloaded [here](ftp://ftp.gnupg.org/gcrypt/binary/gnupg-w32cli-1.4.10b.exe). I suggest installing it to an easy to remember location like C:\GPG.

#### Linux Users
GPG comes with many Linux distributions by default. Try opening a Terminal and typing:
```
gpg --version
```
if you get an error, visit your Linux Distributions website and search for instructions on installing GPG.

#### Mac Users
You can download a version of GPG for Macs [here](https://gpgtools.org/). Download the GPG Suite and run the package installer. The GUI suite will open. You can quit it and continue as below or use the GUI to generate your key.

### Creating/Uploading the Key
Run the command:
```
gpg --gen-key --expert
```
you will be prompted for the kind of key you want, choose "RSA and RSA (default)".

Next you'll be prompted for the keysize. This determines how strong the encryption is. If you're not paranoid about security, I suggest choosing a smaller key size as bigger keys will take longer to encrypt/decrypt your data thus greatly slowing down the process (especially for large exports), 1024 should be fine in most cases.

Next you'll be prompted for how long the key should be valid. Specify 0 so that the key does not expire.

Next you'll be prompted for your name, email address and a comment. Remember the name you enter, you'll need it for the next step. Google doesn't really use this information so feel free to make something up if you want.

Finally, you'll be prompted for a passphrase, you'll need this passphrase in order to decrypt activity logs and exports so make sure you remember what it is!

### Uploading the GPG Key
You can now upload your key to Google's Servers with the command:
```
gpg --export --armor -a "Your Name" | \path\to\gam\gam audit uploadkey
```
where "Your Name" is the name you entered for yourself in the last GPG command. This will output the GPG key and "pipe" it into GAM, telling GAM to upload the key to Google.

## Decrypting Downloaded Files with GPG
Once you've submitted requests, the requests complete and you download requests, you can decrypt the data with GPG. The command to decrypt is:
```
gpg --output <new decrypted file> --decrypt <encrypted file> 
```
encrypted file is one of the files GAM downloaded from a completed activity or export request. In the case of exports, you may have multiple files to decrypt. Here's an example decrypt command:
```
gpg --output jsmith-activity.txt --decrypt c:\gam\activity-jsmith-34231-1.txt.gpg
```
this will create a file jsmith-activity.txt with the decrypted results.