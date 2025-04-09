# GAM Calendar Command Reference

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

## gam calendar \<calendar email\> \<action\> [\<options\>]

## where action and options are:
* **showacl**|**wipe**
* **add**|**update**
  * freebusy |
  * read |
  * editor |
  * owner \<user email\> |
  * user \<user email\> |
  * group \<group email\> |
  * domain [\<Domain name\>] |
  * default
* **delete**
  * \<user email\>|
  * user \<user email\>|
  * group \<group email\>|
  * domain [\<Domain name\>]|
  * default
* addevent
  * [attendee \<user email\>]
  * [location \<location\>]
  * [optionalattendee \<user email\>] 
  * [anyonecanaddself]
  * [summary \<summary\>]
  * [source \<title\> \<url\>]
  * [description \<event description\>]
  * [id \<id\>]
  * [available]
  * start allday \<YYYY-MM-DD\> | \<start datetime\>
  * end allday \<YYYY-MM-DD\> | \<end datetime\>
  * [guestscantinviteothers]
  * [guestscantseeothers]
  * [visibility default|public|private]
  * [tentative]
  * [notifyattendees]
  * [recurrence \<repeat\>]
  * [noreminders] | [reminder \<minutes\> email|popup|sms]
  * [timezone \<timezone]
  * [privateproperty \<Key\> \<Value\>]
  * [sharedproperty \<Key\> \<Value\>]
  * [colorindex \<index\>]
* deleteevent
  * [eventid \<id\>]
  * [query \<query\>]
  * [notifyattendees]
  * [doit]
  
## gam \<who\> show calendars|calsettings

## gam \<who\> delete calendar \<calendar email\>

## gam \<who\> add | update calendar \<calendar email\>
* [selected true|false]
* [hidden true|false]
* [reminder email|sms|popup (minutes)]
* [summary \<summary\>]
* [colorindex (1-24)]
* [backgroundcolor \<htmlcolor\>]
* [foregroundcolor \<htmlcolor\>]

## gam \<who\> update calattendees csv \<csv file\>
* [start YYYY-MM-DD]
* [end YYYY-MM-DD]
* [allevents]
* [dryrun]

## gam \<who\> transfer seccals \<target user\> [keepuser]
## gam \<who\> info calendar \<calendar email\>|primary
## gam \<who\> print calendars [todrive]
