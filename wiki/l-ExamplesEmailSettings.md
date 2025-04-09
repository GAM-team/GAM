- [Signatures and Away Messages](#signatures-and-away-messages)
  - [Setting a Signature](#setting-a-signature)
  - [Retrieving a Signature](#retrieving-a-signature)
  - [Enabling/Disabling and Setting a Vacation (Away) Message](#enablingdisabling-and-setting-a-vacation-away-message)
  - [Retrieving Vacation Settings](#retrieving-vacation-settings)
- [Labels and Filters](#labels-and-filters)
  - [Create a Label](#create-a-label)
  - [Retrieving User's Labels](#retrieving-users-labels)
  - [Delete a Label](#delete-a-label)
  - [Create a Filter](#create-a-filter)
  - [Retrieve a Filter](#retrieve-a-filter)
  - [Delete a Filter](#delete-a-filter)
  - [Print Filter Details](#print-filter-details)
  - [Show Filter Details](#show-filter-details)
- [IMAP, POP](#imap-pop)
  - [Setting IMAP Settings](#setting-imap-settings)
  - [Retrieving IMAP Settings](#retrieving-imap-settings)
  - [Setting POP Settings](#setting-pop-settings)
  - [Retrieving POP Settings](#retrieving-pop-settings)
- [Send As](#send-as)
  - [Add a Send As Address (Custom From)](#add-a-send-as-address-custom-from)
  - [Update a Send As Address](#update-a-send-as-address)
  - [Delete a Send As Address](#delete-a-send-as-address)
  - [Retrieve a Send As Address](#retrieve-a-send-as-address)
  - [Print Send As Addresses](#print-send-as-addresses)
  - [Show Send As Addresses](#show-send-as-addresses)
- [Forwarding](#forwarding)
  - [Add a Forwarding Address](#add-a-forwarding-address)
  - [Delete a Forwarding Address](#delete-a-forwarding-address)
  - [Retrieve a Forwarding Address](#retrieve-a-forwarding-address)
  - [Print Forwarding Addresses](#print-forwarding-addresses)
  - [Show Forwarding Addresses](#show-forwarding-addresses)
  - [Setting a Forward](#setting-a-forward)
  - [Print Forward Settings](#print-forward-settings)
  - [Show Forward Settings](#show-forward-settings)
- [Delegates](#delegates)
  - [Creating a Gmail delegate](#creating-a-gmail-delegate)
  - [Deleting a Gmail delegate](#deleting-a-gmail-delegate)
  - [Print Gmail delegates](#print-gmail-delegates)
  - [Show Gmail delegates](#show-gmail-delegates)
  - [Creating a Contact delegate](#creating-a-contact-delegate)
  - [Deleting a Contact delegate](#deleting-a-contact-delegate)
  - [Print Contact delegates](#print-contact-delegates)
  - [Show Contact delegates](#show-contact-delegates)
- [Managing S/MIME Certificates](#managing-smime-certificates)
  - [Adding S/MIME Certificates](#adding-smime-certificates)
  - [Updating S/MIME Certificates](#updating-smime-certificates)
  - [Deleting S/MIME Certificates](#deleting-smime-certificates)
  - [Show/Print S/MIME Certificates](#show-print-smime-certificates)
- [Hiding/Unhiding users from the domain contacts](#hidingunhiding-users-from-the-domain-contacts)
  - [Changing a users profile to hidden/unhidden](#changing-a-users-profile-to-hiddenunhidden)
  - [Showing users profile hidden/unhidden status](#showing-users-profile-hiddenunhidden-status)
- [User Profile Photos](#user-profile-photos)
  - [Updating Profile Photos](#updating-profile-photos)
  - [Getting Profile Photos](#getting-profile-photos)
  - [Deleting Profile Photos](#deleting-profile-photos)
- [Managing User Email](#managing-user-email)
  - [Modifying User Emails](#modifying-user-emails)
  - [Deleting or Trashing User Emails](#deleting-trashing-or-untrashing-user-emails)
  - [Sending Email as a User](#sending-email-as-a-user)
  - [Dropping Emails into a User Mailbox](#dropping-emails-into-a-user-mailbox)
  - [Drafting Emails for a User](#drafting-emails-for-a-user)
- [Print/Show User Gmail Profile](#print-show-user-gmail-profile)
  - [Print User Gmail Profile](#print-user-gmail-profile)
  - [Show User Gmail Profile](#show-user-gmail-profile)
- [Managing User Display Language](#managing-user-display-language)
  - [Set User Language](#set-user-language)
  - [Get User Language](#get-user-language)

# Signatures and Away Messages
## Setting a Signature
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users [signature <signature text>] [file <signature file>] [replyto <EmailAddress>] (replace <Tag> <String>)*
```
sets a email signature for the given users' primary email address. Use quotes around the signature text if it contains spaces (which it almost certainly will). New lines can be specified with \n. HTML can also be used. An empty string like "" will disable the signature. Use the optional `file` argument to specify a filename that contains the signature text. This is easier for long, complex signatures.  Use the optional `replyto` argument to specify a reply to address for use with this signature. The optional argument `replace` can be used to insert values into the signature text. Every instance of {`Tag`} in the signature will be replaced by `String`. Instances of the form {RT}...{`Tag`}...{/RT} will be eliminated if that `Tag` was not specified or if `Tag` was specified but the accompanying `String` is empty. {RT} and {/RT} are eliminated from the signature.
### Example
This example sets all user's signatures to be:
```
Acme Inc
1321 Main Ave
http://www.acme.com
```

```
gam all users signature
 "Acme Inc<br>1321 Main Ave<br>http://www.acme.com
```

This example reads the signature from a file:
```
gam user bob@example.com signature file bobs-sig.txt
```

This example reads the signature from an HTML file:
```
gam user sue@example.com signature file sues-html-sig.html html
```
----

## Retrieving a Signature
### Syntax
```
gam
 user <username> | group <groupname>| ou <ouname> | all users show signature [format]
```
Shows the email signature for the given users. By default, the raw HTML of the signature is shown, the optional argument `format` causes the HTML to be interpreted.

### Example
This example shows all user's signature

```
gam all users show signature
```
----

## Enabling/Disabling and Setting a Vacation (Away) Message
### Syntax
```
gam
 user <username> | group <groupname> | ou <ouname> | all users
 vacation on|off subject <subject text> [message <message text>] | [file <message file>] [html]
 startdate <YYYY-MM-DD> enddate <YYYY-MM-DD>
 [contactsonly] [domainonly]
 (replace <Tag> <String>)*
```
enable or disable a vacation/away message for the given users. `subject <subject text>` will set the away message subject. `message <message text>` will set the away message text. Use quotes around `<subject text>` and `<message text>` if they contain spaces (which they probably will). If `file` is specified instead of message, the message will be read from the given text file. In `<message text>`, \n will be replaced with a new line. The optional argument `html` says to interpret the message text as HTML. Except for the simplest messages, you should specify `html` even if your message doesn't contain HTML as Google does unexpected line wrapping when `html` is not specified. The optional `startdate` and `enddate` arguments set a start and end date for the vacation message to be enabled. The optional argument `contactsonly` will only send away messages to persons in the user's Contacts. The optional argument `domainonly` will prevent vacation messages from going to users outside the Google Apps domain. The optional argument `replace` can be used to insert values into the away message text. Every instance of {`Tag`} in the message will be replaced by `String`. Instances of the form {RT}...{`Tag`}...{/RT} will be eliminated if that `Tag` was not specified or if `Tag` was specified but the accompanying `String` is empty. {RT} and {/RT} are eliminated from the message.

### Example
This example sets the away message for the user
```
gam user epresley vacation on subject "Elvis has left the building"
 message "I will be on Mars for the next 100 years. I'll get back to you when I return.\n\nElvis"
```

This example reads the message from a text file:
```
gam user bob@example.com vacation on subject "I am away" file bobs-away-message.txt
```
----

## Retrieving Vacation Settings
### Syntax
```
gam
 user <username> | group <groupname> |ou <ouname> | all users show vacation [format]
```
Show the given user's vacation message and settings. By default, the plain text or raw HTML of the vacation message is shown, the optional argument `format` causes the HTML to be interpreted.

## Example
This example shows the vacation settings for jsmith
```
gam user jsmith show vacation
```

# Labels and Filters
## Create a Label
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users label <label name>
```
create a Gmail Label for the given users. Use quotes around the label name if it contains spaces. Labels are described <a href='http://mail.google.com/support/bin/answer.py?hl=en&answer=118708'>here.</a>

### Example
This example creates a label called New Label for all users
```
gam all users label "New Label"
```

## Retrieving User's Labels
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show labels [onlyuser] [showcounts]
```
Show the labels for the given users. If the optional argument `onlyuser` is specified, default labels including inbox, unread, drafts, sent, chat, muted, spam, trash, popped, and contactcsv will not be shown. Label visibility will also be reported. If the optional argument `showcounts` is specified, message and thread counts will be show for each label.

### Example
This example shows the labels for all members of the marketing group
```
gam group marketing show labels
```

## Delete a Label
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete label <label name>
```
delete the given label for the given users.  Use quotes around the label name if it contains spaces. Labels are described <a href='http://mail.google.com/support/bin/answer.py?hl=en&answer=118708'>here.</a>

### Example
This example deletes a label called Old Label for all users
```
gam all users delete label "Old Label"
```

## Create a Filter
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users filter
  from <email>|to <email>|subject <words>|haswords <words>|nowords <words>|musthaveattachment
  label <label name>|markread|archive|star|forward <email address>|trash|neverspam|important|notimportant
```
Create a Filter for the given users. Filter must have one or more conditions (from, to, subject, haswords, nowords or musthaveattachment) and one or more actions (label, markread, archive, star, forward, trash, neverspam, important or notimportant). You do not need to create a label before creating a filter that labels messages, creating a filter that labels messages will automatically create the label. **Filters** are described <a href='http://mail.google.com/support/bin/answer.py?hl=en&answer=6579'>here</a> and **Search operators** <a href='https://support.google.com/mail/answer/7190?hl=en'>here</a>.

### Examples
This example creates a filter for the user john that labels messages from dianne@gmail.com and archives them (thus they will only appear under the label)

```
gam user john filter from dianne@gmail.com label Dianne archive
```
This example creates a filter for the user john that marks messages from dianne@gmail.com as category:primary and stars them (hint: you can find **all predefined Lable/Category types** [here](https://developers.google.com/gmail/api/guides/labels))

```
gam user john filter from dianne@gmail.com label "CATEGORY_PERSONAL" star
```

This example creates a filter for the user john that labels messages from anyuser@anysubdomain.example.com and anyuser@example.com and marks messages to never send to spam (hint: `-me` avoids **Sent messages** to show up in the INBOX)

```
gam user john filter from "-me AND .example.com OR example.com" label "thrusted" neverspam
```

## Retrieve a Filter
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users info filters <FilterIDList>
```

Display details of a list of specific filters.

## Delete a Filter
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete filters <FilterIDList>
```

Delete a list of filters of a user.

## Print Filter Details
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print filters [todrive]
```
Display or upload to Google Drive a CSV report of all of a users' filters. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

## Show Filter Details
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show filters
```
Display details of all of a users' filters.

# IMAP, POP
## Setting IMAP Settings
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users imap on|off [noautoexpunge] [expungebehavior archive|deleteforever|trash] [maxfoldersize 0|1000|2000|5000|10000]<br>
```
turn IMAP on or off for given users. There are three options:<br>
`noautoexpunge`: If this value is not specified, Gmail will immediately expunge a message when it is marked as deleted in IMAP. When specified, Gmail will wait for an update from the client before expunging messages marked as deleted.
`expungebehavior`: The action that will be executed on a message when it is marked as deleted and expunged from the last visible IMAP folder. The acceptable values are: "archive": Archive messages marked as deleted; "deleteforever": Immediately and permanently delete messages marked as deleted. The expunged messages cannot be recovered; "trash": Move messages marked as deleted to the trash.
`maxfoldersize`: An optional limit on the number of messages that an IMAP folder may contain. Legal values are 0, 1000, 2000, 5000 or 10000. A value of zero is interpreted to mean that there is no limit.

### Example
This example will turn IMAP on for all current users in the domain.
```
gam all users imap on
```

## Retrieving IMAP Settings
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show imap
```
shows the given users' current IMAP settings.

### Example
This example shows all user's IMAP status.<br>
```
gam all users show imap<br>
```


## Setting POP Settings
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users pop on|off [for allmail|newmail] [action keep|archive|delete|markread]<br>
```
turn POP3 on or off for given users, "for allmail" will expose all Inbox mail to the POP client while "for newmail" will expose only mail received after POP was enabled. POPped mail can be left alone (keep), archived (archive), deleted (delete) or marked read (markread). If the for and action arguments are not specified, all mail will be popped and kept in the Inbox.

### Example
This example will turn POP on for any users in the group students. All mail in the Inbox will be exposed to the POP client and POPped emails will be kept in the Inbox.
```
gam group students pop on
```

This example will turn POP on for Bob but only for new mail he receives. Mail will be archived after it is popped:
```
gam user bob@example.com pop on for newmail action archive
```


## Retrieving POP Settings
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show pop
```
show the given users' POP settings.

### Example
This example shows the pop settings for the group students
```
gam group students show pop
```

# Send As
## Add a Send As Address (Custom From)
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users sendas <EmailAddress> <Name> [signature <String>|(file <FileName>) [replyto <EmailAddress>] [default] [treatasalias <Boolean>] (replace <Tag> <String>)*
```
Add `<EmailAddress>` as one of the given users' send as addresses (also called Custom From). `<Name>` is the nice name users see with the email (Use quotes if `<name>` includes spaces). Each send as address can have its own signature. See <a href='https://github.com/jay0lee/GAM/wiki/ExamplesEmailSettings#setting-a-signature'>Setting a Signature</a>. Optionally, `default` specifies that this should be the address used for outgoing mail by default (user can choose which address mail is sent from when they compose). Also optional, `replyto <EmailAddress>` specifies a Reply To address to be used when mail is sent out via this sendas. See <a href='https://support.google.com/a/answer/1710338?ctx=gmail&hl=en&authuser=0&visit_id=1-636106946018751865-4063694491&rd=1'>here</a> for a description of the `treatasalias <Boolean>` argument. The optional argument `replace` can be used to insert values into the signature text. Every instance of {`Tag`} in the signature will be replaced by `String`. Instances of the form {RT}...{`Tag`}...{/RT} will be eliminated if that `Tag` was not specified or if `Tag` was specified but the accompanying `String` is empty. {RT} and {/RT} are eliminated from the signature.

****Warning:**** Google has recently taken steps to limit what email addresses forwards can be set to via the API (and thus via GAM).
See <a href='http://googleappsupdates.blogspot.com/2010/05/gmail-now-requires-verification-of.html'>this blog post</a> for details about what domains you can set forwards to.
Generally you are limited to forwarding to your primary domain, alias and secondary domains and subdomains of those.

### Example
This example adds mtodd as one of alincoln's send as addresses.
```
gam user alincoln sendas mtodd "First Lady" replyto mtodd signature "Mary"
```

## Update a Send As Address
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users update sendas <EmailAddress> [name <Name>] [signature <String>|(file <FileName> ) (replace <Tag> <String>)*] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
```
Update the characteristics of  `<EmailAddress>` as one of the given users' send as addresses. See above for a description of the arguments.

### Example
This example updates mtodd as one of alincoln's send as addresses.
```
gam user alincoln update sendas mtodd name "Abe's Wife"
```

## Delete a Send As Address
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete sendas <EmailAddress>
```
Delete `<EmailAddress>` as one of the given users' send as addresses.

### Example
This example deletes alincoln's send as address mtodd.
```
gam user alincoln delete sendas mtodd
```

## Retrieve a Send As Address
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users info sendas <EmailAddress> [format]
```
Shows the status of `<EmailAddress>` as one of the given users' send as addresses.

### Example
This example shows the status of alincoln's send as address mtodd.
```
gam user alincoln info sendas mtodd
```

## Print Send As Addresses
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print sendas [todrive]
```
Display or upload to Google Drive a CSV report of users' send as addresses. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

### Example
This example outputs all users send as addressess in a CSV format.
```
gam all users print sendas
```

## Show Send As Addresses
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show sendas [format]
```
Shows the given users' send as addresses.

### Example
This example shows alincoln's send as addresses.
```
gam user alincoln show sendas
```
# Forwarding
## Add a Forwarding Address
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users add forwardingaddress <EmailAddress>
```
Add `<EmailAddress>` as one of the given users' forwarding addresses.
****Warning:**** Google has recently taken steps to limit what email addresses forwards can be set to via the API (and thus via GAM). See <a href='http://googleappsupdates.blogspot.com/2010/05/gmail-now-requires-verification-of.html'>this blog post</a> for details about what domains you can set forwards to. Generally you are limited to forwarding to your primary domain, alias and secondary domains and subdomains of those.

### Example
This example adds mtodd as one of alincoln's forwarding addresses.
```
gam user alincoln add forwardingaddress mtodd
```

## Delete a Forwarding Address
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete forwardingaddress <EmailAddress>
```
Delete `<EmailAddress>` as one of the given users' forwarding addresses.

### Example
This example deletes alincoln's forwarding address mtodd.
```
gam user alincoln delete forwardingaddress mtodd
```

## Retrieve a Forwarding Address
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users info forwardingaddresses <EmailAddress>
```
Shows the status of `<EmailAddress>` as one of the given users' forwarding addresses.

### Example
This example shows the status of alincoln's forwarding address mtodd.
```
gam user alincoln info forwardingaddress mtodd
```

## Print Forwarding Addresses
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print forwardingaddresses [todrive]
```
Display or upload to Google Drive a CSV report of users' forwarding addresses. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

### Example
This example outputs all users forwarding addressess in a CSV format.
```
gam all users print forwardingaddresses
```

## Show Forwarding Addresses
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show forwardingaddresses
```
Shows the given users' forwarding addresses.

### Example
This example shows alincoln's forwarding addresses.
```
gam user alincoln show forwardingaddresses
```

## Setting a Forward
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users forward off
gam user <username>|group <groupname>|ou <ouname>|all users forward on <EmailAddress> keep|archive|delete|markread
```
Disable/enable and set an automatic email forward for the given users. If turning forwarding on, an `<EmailAddress>` and an action (`keep|archive|delete|markread`) are both required. The `<EmailAddress>` you specify must already have been set up as a forwarding address. Actions specify what to do with messages that have been forwarded.

### Example
This example sets a forward for the user, messages will be deleted after they are forwarded so they will not show up in the user's account
```
gam user eclapton forward on eclapton@music.com delete
```

## Print Forward Settings
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print forward [todrive]
```
Display or upload to Google Drive a CSV report of users' forward settings. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

### Example
This example outputs all users forwarding settings in a CSV format.
```
gam all users print forward
```

## Show Forward Settings
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show forward
```
shows the given users' forwarding settings.

### Example
This example shows alincoln's forwarding settings.
```
gam user alincoln show forward
```


# Delegates
A delegate is someone who has been given access to someone else's email or contacts. The delegator is the one whose email and contacts are accessible by the delegate.
Delegate and the delegators must be in the same domain, granting delegate access across multiple domains is currently not possible.

## Creating a Gmail delegate
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delegate to <delegate email>
gam user <username>|group <groupname>|ou <ouname>|all users add delegate <delegate email>
```
Gives email and contact access for the given users (the delegators) to the specified delegate account. Unlike when users request delegate access via Gmail settings, no email will be sent to the delegators for approval, the approval occurs immediately.
The delegate and the delegator must be in the same domain, granting delegate access across multiple domains is currently not possible.

Both the Gmail delegator and the delegate:

* Must be active. A 500 error is returned if either user is suspended and disabled.<br>
* Must not require a change of password on the next sign in. A 500 error is returned if either user has this flag enabled in the control panel, or, using the Provisioning API, the changePasswordAtNextLogin attribute is true.

You can confirm these settings using the <a href='ExamplesProvisioning#Get_User_Info'>gam info user</a> command. Both "Account suspended" and "Must change password" should show false for both the delegate and the delegator.

### Example
This example gives jbezos access to the contacts and email of the sales account.
```
gam user sales delegate to jbezos@amazon.com
```


## Deleting a Gmail delegate
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete delegate <delegate email>
```
Deletes the delegate for the given users.

### Example
This example takes away deSecretary's access to deBoss's email and contacts.
<br>
```
gam user deBoss delete delegate deSecretary
```

## Print Gmail delegates
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print delegates [todrive]
```
Display or upload to Google Drive a CSV report of users' delegates. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file.

Prints the delegates that have access to the given user accounts.

### Example
This example prints delegates across the entire domain.
```
gam all users print delegates
```


## Show Gmail delegates
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show delegates [csv]
```
Shows the delegates that have access to the given user accounts. Optional argument csv prints out CSV style output instead of human readable.

### Example
This example shows delegates for users in the technology group.
```
gam group technology show delegates
```
----
##  Creating a Contact delegate
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users add contactdelegate <delegate email>
```
Delegates given user(s) contacts to the given delegate user.

### Example
This examples gives D. Landingham access to manage J. Bartlet's contacts.
```
gam user jbartlet@acme.com add contactdelegate dlandingham@acme.com
```
----
## Deleting a Contact delegate
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete contactdelegate <delegate email>
```
Removes a delegate user's access to a given user's contacts.

### Example
This example removes C. Young's delegate access to J. Bartlet's contacts.
```
gam user jbartlet@acme.com delete contactdelegate cyoung@acme.com
```
----
## Print Contact delegates
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print contactdelegates [todrive]
```
Prints the contact delegates of a given user. The optional todrive argument causes the output to generate a Google Sheet rather than printing to the console.

### Example
This example prints all contact delegates for J. Bartlet to a Google Sheet.
```
gam user jbartlet@acme.com print contactdelegates todrive
```
----
## Show Contact delegates
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show contactdelegates
```
Shows the contact delegates of a given user in human-friendly output format.

### Example
This example shows all contact delegates for J. Bartlet.
```
gam user jbartlet@acme.com show contactdelegates
```
----

# Managing S/MIME Certificates
## Adding S/MIME Certificates
### Syntax
```
gam user <email> add smime <file <filename>> <password <password>> [default] [sendas <email>]
```
Uploads an S/MIME certificate for the user. The file argument specifies the local file which contains the S/MIME Certificate to be uploaded. The password argument specifies the password used to encrypt the S/MIME certificate. The optional argument default specifies that if user has multiple certificates for this sendas, this one should be the default. The optional argument sendas specifies the sendas email address that the S/MIME certificate should be used with. If sendas is not specified, the user's primary address is assumed.

### Example
This example uploads the file jim.pfx for Jim and marks it as default.
```
gam user jim@acme.com add smime file jim.pfx password p@ssw3rd default
```
----
## Updating S/MIME Certificates
### Syntax
```
gam user <email> update smime [id <id>] [sendas <email>] <default>
```
Updates a S/MIME certificate for a user. Currently the only update operation is to mark the certificate as the default. The id argument specifies the id of the S/MIME certificate to update. If ID is not specified then all existing certificates will be listed. The sendas argument specifies the sendas address which owns the certificate to be updated. If sendas is not specified, the user's primary address is assumed. The default argument updates the selected certificate to be the default. Currently default is required since it's the only update operation.

### Example
This example sets a certificate to be the default for John's primary address.
```
gam user john@acme.com update smime id 84833830 default
```
----

## Deleting S/MIME Certificates
### Syntax
```
gam user <email> delete smime <id <id>> [sendas <email>]
```
Deletes a S/MIME certificate for a user. The id argument specfies which S/MIME certificate should be deleted. The optional sendas argument specifies the sendas address which the certificate is associated with. If sendas is not specified then the user's primary address is used.

### Example
This example delete's the user's certificate.
```
gam user john@acme.com delete smime id 34394348349
```
----

## Show/Print S/MIME Certificates
### Syntax
```
gam user <email> show|print smime primaryonly todrive
```
Show or print the S/MIME certificates of the specified user(s). Show displays the certificates on the screen while print outputs CSV format. The optional argument primaryonly skips looking up additional sendas addresses for user and only pulls certificates associated with the user's primary address. The optional argument todrive specifies that printed output should be uploaded to a Google Drive Spreadsheet instead of displaying the CSV to the screen.

### Example
This example creates a spreadsheet with all user primary certificates.
```
gam all users print smime primaryonly todrive
```
----

<h1>Hiding/Unhiding users from the domain contacts</h1>
Individual user profiles can be hidden/unhidden from the domain contacts list (sometimes called the Global Address List or GAL).<br>
<br>
<h2>Changing a users profile to hidden/unhidden</h2>
<h3>Syntax</h3>
<pre><code>gam user &lt;username&gt;|group &lt;groupname&gt;|ou &lt;ouname&gt;|all users profile shared|unshared<br>
</code></pre>
Share a user's profile (contact) information with other users in the domain. If a user's profile is shared, they'll show up in autocomplete and contact searches for other users. If a user is unshared, others will not be able to discover the user's address and detailed contact info.<br>
<br>
<h3>Example</h3>
this example hides all users in the asked-to-be-hidden Google group from email address autocomplete and contact searches.<br>
<br>
<pre><code>gam group asked-to-be-hidden profile unshared<br>
</code></pre>
<hr />

<h2>Showing users profile hidden/unhidden status</h2>
<h3>Syntax</h3>
<pre><code>gam user &lt;username&gt;|group &lt;groupname&gt;|ou &lt;ouname&gt;|all users show profile<br>
</code></pre>
Show the current sharing status of the users' profile.<br>
<br>
<h3>Example</h3>
this example shows the status of all user profiles in the domain.<br>
<br>
<pre><code>gam all users show profile<br>
</code></pre>
<hr />

# User Profile Photos
## Updating Profile Photos
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users update photo <photo filename>
```
Create or replace the user's photo with the one specified by filename. File should be jpg format. You can use #user# as part of the filename and it will be replaced with the user's full email address.

### Examples
this example replaces Michael Jones' photo with the one from the employee photo directory
```
gam user michael.jones@acme.com update photo h:\employee-photos\mjones.jpg
```

this example replaces all user's photos with ones stored in c:\photos\<user email>.jpg
```
gam all users update photo c:\photos\#user#.jpg
```

## Getting Profile Photos
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users get photo [drivedir|(targetfolder <FilePath>)] [noshow]
```
Gets the users' current photo and saves it to a file named username-domain.jpg in the GAM path. If `drivedir` is specified, the files will be saved in the folder referenced by the environment variable GAMDRIVEDIR. If `targetfolder <FilePath>` is specified, the files will be saved in FilePath. The `noshow` argument prevents to photo data from being displayed to stdout.

## Example
This example retrieves photos for all users in Google Apps and saves them to files in the C:\photos directory.
```
gam all users get photo targetfolder "C:\photos"
```

## Deleting Profile Photos
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete photo
```
Deletes the given users' profile photo returning it to blank.

### Example
This example will delete the profile photo for all members of the group named abused-the-system
```
gam group abused-the-system delete photo
```


# Managing User Emails
## Modifying User Emails
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users modify messages|threads query <gmail search> [doit] [maxtomodify <number>] [addlabel <label>] [removelabel <label>] 
```
Modify user Gmail messages or threads. If you specify messages, the search will be done against individual messages and only individual messages that match the query will be modified. If you specify threads then all messages in all threads that match the query will be modified. The addlabel argument specifies labels that should be added to matching messages/threads. The removelabel argument specifies labels that should be added to matching messages/threads. The query parameter is required and uses Gmail search syntax. See the [Advanced Gmail Search help article](https://support.google.com/mail/answer/7190?hl=en) for some tips on complex searches. 

By default, GAM will not modify any messages/threads for users. The doit parameter is needed to tell GAM to actually perform the modify operation. 

The maxtomodify paramater (default: 1) defines how many matching messages/threads per user that may be modified. If more than this number of message matches the search query, GAM will refuse to modify ANY messages for that user. 

### Example
This example moves all matching messages to the Spam folder.
```
gam user joe@acme.com modify messages query 'subject:"buy viagra"' addlabel SPAM removelabel INBOX doit maxtomodify 10
```

This example marks all messages from president@acme.com as Important and Starred.
```
gam all users modify messages query from:president@acme.com addlabel IMPORTANT addlabel STARRED doit maxtomodify 500
```
----

## Deleting, Trashing or Untrashing User Emails
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users delete|trash|untrash messages|threads query <gmail search> [doit] [maxtodelete|maxtotrash|maxtountrash <number>] 
```
Delete or move to trash messages or threads for a user or group of users. If you specify messages, the search will be done against individual messages and only individual messages that match the query will be deleted/trashed/undeleted. If you specify threads then all messages in all threads that match the query will be deleted/trashed/undeleted. The query parameter is required and uses Gmail search syntax. See the [Advanced Gmail Search help article](https://support.google.com/mail/answer/7190?hl=en) for some tips on complex searches. 

By default, GAM will not delete/trash/untrash any messages for users, it only shows what messages will be impacted. The doit parameter is needed to tell GAM to actually perform the delete/trash/untrash operation.

The maxtodelete/maxtotrash/maxtountrash paramater (default: 1) defines how many matching messages/threads per user that may be affected. If more than this number of message matches the search query, GAM will refuse to modify ANY messages for that user.

### Examples
This example gets a count of how many messages a user has with PDF attachments but doesn't actually do anything to them.
```
gam user joe@acme.org delete messages query filename:pdf
```

This example will delete the message that has this exact [RFC822 Message ID header](https://support.google.com/groups/answer/75960?hl=en) for all users. Only one message at most will be deleted for all users (they should have only one copy). This example is useful if an email is sent to a large number of people and you wish to remove it from their mailbox quickly.
```
gam all users delete messages query rfc822msgid:CAGoYzwvzepSfbHB8mBoOx4VqsiotTmRjvBSFjz8NMg2VXeHTrA@mail.gmail.com doit
```

This example will trash the thread that has a message from internal.leaker@gmail.com. This means that if users have replied to the message or forwarded it, those messages should also be deleted from the user mailbox.
```
gam all users delete threads query from:internal.leaker@gmail.com maxtodelete 10 doit
```

This example will trash all messages older than 7 years for members of the group. **BE CAREFUL!** There is no undo button. This command could be run on a regular basis (once a day or so) in order to ensure messages older than 7 years are trashed for the user.
```
gam group purge7@acme.org trash messages query older_than:7y doit maxtodelete 999999999
```
## Sending Email as a User
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users sendemail [message <message>] [file <file>] [subject <subject] [recipient <recipient>]
```
Sends an email as the given user. The optional argument message specifies the text to use for the email message including headers and body. The optional argument file reads the message including headers and body from a local file. An easy way to create a rich email message is to send it to yourself in Gmail UI and then [Download the original](https://support.google.com/mail/answer/29436?hl=en) to a file. The optional arguments subject and recipient set the message subject / recipient respectively and will override the headers set in message or file.

### Example
This example sends a quick message to the user and from the user
```
gam user test@example.com sendemail subject "from me, to me"
```
This example sends a message from the user to an external address
```
gam user test@example.com sendemail file c:\gam\test.eml recipient thedude@gmail.com
```
## Dropping Emails into a User Mailbox
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users insertemail|importemail [message <message>] [file <file>] [subject <subject] [recipient <recipient>] [labels <labels,>]
```
Drops an email into the given users mailbox. Note that unlike sendemail, these commands will always put the email directly into the user's mailbox, no matter who the recipient is set to. insertemail uses the [INSERT API method](https://developers.google.com/gmail/api/v1/reference/users/messages/insert) and is fastest though messages will not be de-duplicated or threaded in the Gmail mailbox. importemail uses the [IMPORT API method](https://developers.google.com/gmail/api/v1/reference/users/messages/import) which is slower but offers more processing options during delivery. By default, messages dropped in a user mailbox receive *no labels* which means they are archived and marked as read. To best grab a user's attention for reading the recommendation is to set labels like INBOX,UNREAD,IMPORTANT,STARRED. The optional argument message specified the message including headers and body. The optional argument file reads the message including headers and body from a local file. The optional arguments subject and recipient set the message subject and recipients overriding message and file. The optional argument labels specifies a comma separated list of labels to apply to the message.

Dropped messages do not get processed by user Gmail filters.

### Example
This example is the fastest way to get an email in front of a LOT of users quickly with a custom message per-user.
```
gam print users givenname | gam csv - gam user ~primaryEmail insertemail subject "ALERT: ~~givenName~~ donuts in the break room" labels INBOX,UNREAD,IMPORTANT,STARRED
```
## Drafting Emails for a User
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users draftemail [message <message>] [file <file>] [subject <subject] [recipient <recipient>]
```
Places a draft email in the given user's mailbox. The optional argument message specifies the email message including headers and body. The optional argument file reads the message from a local file. The optional argument subject sets the message subject overriding message/file. The optional argument recipient sets the message recipient overriding message/file.

### Example
This example creates a draft message for a user.
```
gam user me@example.com draftemail subject "TPS Report" message "This is my TPS report" recipient boss@example.com
```

# Print/Show User Gmail Profile
## Print User Gmail Profile
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print gmailprofile [todrive]
```
Display or upload to Google Drive a CSV report of user Gmail profile data. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. 

## Show User Gmail Profile
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users print gmailprofile
```
Display a formatted report of user Gmail profile data.
---
# Managing User Display Language
## Set User Language
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users language <language code>
```
set the display language used for the user. A full list of language codes can be found [here.](https://developers.google.com/gmail/api/guides/language_settings#display_language).
### Example
This example sets the user's language to UK English
```
gam user jlennon language en-GB
```
---
## Get User Language
### Syntax
```
gam user <username>|group <groupname>|ou <ouname>|all users show language
```
get the display language currently set for the user.
### Example
This example gets the current language of the user.
```
gam user jlennon show language
```
---