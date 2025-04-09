GAM Variable Definitions

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

# General Notes
Fields enclosed in \<angle brackets\> are mandatory

Fields enclosed in [square brackets] are optional.  In most cases, multiple optional fields may be included in a single gam command.

***

# Global Fields
These fields are used in various places in GAM.  If you see them referenced in the command references, you may look up what they refer to here.

## \<who\>
* user \<user email\>
* group \<group email\>
* group_inde \<group email\> 
* ou \<ou-name\>
* ou_and_child \<ou-name\>
* ou_and_children \<ou-name\>
* org
* all users

## Qualifications to some <who> options:

#### "group_inde" sets GAM to include derived memberships in the group.

#### For "group", "org", "ou", "ou_and_child", and "ou_and_children" you can append:
* "_ns" to exclude suspended 
* OR 
* "_susp" to include suspended 


## \<datetime\>
RFC3339 formatted date and time, e.g. YYYY-MM-DDThh:mm:ss.000Z

## \<user email\>
A user in the domain

## \<group email\>
A group in the domain

## \<email address\>
Any email address