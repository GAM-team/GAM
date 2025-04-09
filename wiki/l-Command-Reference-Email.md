# GAM Email Command Reference

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

## gam \<who\> \<attributes/values\>
where attributes and values are:
* **language** \<language code\>
* **pagesize** 25|50|100
* **shortcuts**|**arrows**|**snippets**|**utf**|**webclips** on|off
* **signature** \<signature text\>|(file \<signature file\>
  * [charset \<Charset\>])
  * (replace \<Tag\> \<String\>)*
  * [name \<String\>]
  * [replyto \<EmailAddress\>]
* **vacation** on|off
  * [subject \<String\>
  * (message \<String\>)|(file \<FileName\> [charset \<CharSet\>])
  * (replace \<Tag\> \<String\>)*
  * [html]
  * [contactsonly]
  * [domainonly]
  * [startdate \<Date\>]
  * [enddate \<Date\>]]
* [add] **label** \<label name\>
  * [messagelistvisibility hide|show]
  * [labellistvisibility hide|show|showifunread]
  * [backgroundcolor \<color\>]
  * [textcolor \<color\>]
* delete **label** \<label name\> |regex:\<RegularExpression\>|--ALL_LABELS--
* update **label** search \<search\> replace \<replace\> [merge]
* update **labelsettings** \<label name\> name \<new label name\>
  * [message_list_visibility show|hide]
  * [label_list_visibility show|hide|show_if_unread]
* show **labels** [onlyuser]
* **filter**
 from \<email address\> |
 to \<email address\> |
 subject \<words\> |
 haswords \<words\> |
 nowords \<words\> |
 musthaveattachment |
 label \<label name\> |
 markread |
 archive |
 star |
 forward \<email address\> |
 trash |
 neverspam
* delete|info **filter** \<FilterIDEntity\>
* [add]|update **sendas**
  * \<email address\>
  * \<name\>
  * [default]
  * [replyto \<email address\>]
  * [treatasalias \<Boolean\>]
  * [signature \<String\>|(file \<FileName\> [charset \<CharSet\>]) (replace \<RegularExpression\> \<String\>)*]
* delete **sendas** \<email address\>
* info **sendas** \<email address] [format]
* **pop** on|off
  * [for allmail|newmail|fromnowown]
  * [action
    * keep |
    * leaveininbox |
    * archive |
    * delete |
    * trash | 
    * markread]
* **imap** on|off
  * [noautoexpunge]
  * [expungebehavior archive|deleteforever|trash]
  * [maxfoldersize 0|1000|2000|5000|10000]
* **forward** on|off [email address] [keep|archive|delete]
* **delegate** to \<user email\>
* add **delegate**|**forwardingaddress** \<user email\>
* show **delegates** [csv]
* show **forwardingaddress**
* show **vacation**|**filters**|**imap**|**pop**|**forward**|**profile**
* show **sendas**|**vacation**|**signature** [format]
* print **delegates**|**forwardingaddress** [todrive]
* delete **delegate**|**forwardingaddress** \<user email\>
* **profile** shared|unshared
* update **photo** \<photo filename\>
* get **photo** [drivedir|(targetfolder \<FilePath\>)] [noshow]
* delete **photo**
* print **filters**|**forward**|**sendas** [todrive]

gam user \<who\> **delete**|**trash**|**untrash** messages|threads
* query \<gmail search\>
* [doit]
* [maxto\<action\> \<number\>]

gam user \<who\> **modify** messages
* addlabel|removelabel \<label\>
* query \<gmail search\>
* [doit]
* [maxto\<action\> \<number\>]

where \<action\> is: delete|trash|untrash|modify
e.g. maxtotrash, maxtountrash